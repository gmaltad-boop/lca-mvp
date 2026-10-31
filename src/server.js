// Servidor local: estaticos + API minima. Zero dependencias externas.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, save, uid } from "./storage.js";
import { applyAction } from "./state.js";
import { organizeNote, ApiError } from "./organize-note.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");

try {
  const envFile = path.join(ROOT, ".env");
  if (fs.existsSync(envFile)) {
    for (const line of fs.readFileSync(envFile, "utf8").split("\n")) {
      const m = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && m[1] && !(m[1] in process.env)) process.env[m[1]] = m[2];
    }
  }
} catch {}

const PORT = Number(process.env.PORT || 3000);
const MODEL = process.env.OPENAI_MODEL || "gpt-5.1";
const KEY = process.env.OPENAI_API_KEY || "";

const dataFile = () => path.join(ROOT, "data", "lca.json");
const loadDb = () => load(dataFile());

const ITEM_CATS = [
  ["observed_facts", "Fatos observados"],
  ["professional_hypotheses", "Hipóteses (registradas pelo profissional)"],
  ["information_gaps", "Lacunas de informação"],
  ["revisable_clinical_evolution", "Evolução clínica (rascunho revisável)"],
  ["reminders", "Lembretes para a próxima sessão"],
  ["follow_up_questions", "Follow-up (rascunho)"],
  ["new_achievements", "Novas conquistas"]
];

function json(res, code, obj) {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(obj));
}
async function readBody(req) {
  let s = "";
  for await (const c of req) s += c;
  return s ? JSON.parse(s) : {};
}
function sendStatic(res, name) {
  const mime = { "index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8", "styles.css": "text/css; charset=utf-8" }[name] || "application/octet-stream";
  fs.readFile(path.join(ROOT, "public", name), (err, buf) => {
    if (err) { res.writeHead(404, { "Content-Type": "text/plain" }); return res.end("404"); }
    res.writeHead(200, { "Content-Type": mime });
    res.end(buf);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, "http://localhost");
    const p = u.pathname;

    if (req.method === "GET" && p === "/") return sendStatic(res, "index.html");
    if (req.method === "GET" && (p === "/app.js" || p === "/styles.css")) return sendStatic(res, p.slice(1));

    if (p === "/api/patients" && req.method === "GET") return json(res, 200, { patients: loadDb().patients });

    if (p === "/api/patients" && req.method === "POST") {
      const b = await readBody(req);
      const db = loadDb();
      const patient = {
        id: uid(),
        label: String(b.label || "Paciente sem nome").slice(0, 60),
        patient_goal: b.patient_goal ? String(b.patient_goal).slice(0, 300) : null,
        fictitious: true,
        created_at: new Date().toISOString()
      };
      db.patients.push(patient);
      save(db, dataFile());
      return json(res, 201, { patient });
    }

    const pm = p.match(/^\/api\/patients\/([\w-]+)$/);
    if (pm && req.method === "GET") {
      const db = loadDb();
      const patient = db.patients.find((x) => x.id === pm[1]);
      if (!patient) return json(res, 404, { error: "Paciente não encontrado" });
      const sessions = db.sessions.filter((s) => s.patient_id === patient.id)
        .sort((a, b) => String(b.date).localeCompare(String(a.date)));
      return json(res, 200, { patient, sessions });
    }

    if (p === "/api/sessions" && req.method === "GET") {
      const db = loadDb();
      const session = db.sessions.find((s) => s.id === u.searchParams.get("id"));
      if (!session) return json(res, 404, { error: "Sessão não encontrada" });
      return json(res, 200, { session });
    }

    if (p === "/api/sessions" && req.method === "POST") {
      const b = await readBody(req);
      const db = loadDb();
      const patient = db.patients.find((x) => x.id === b.patient_id);
      if (!patient) return json(res, 404, { error: "Paciente não encontrado" });
      if (!b.raw_note || !String(b.raw_note).trim()) return json(res, 400, { error: "Nota vazia" });
      const session = {
        id: uid(), patient_id: patient.id,
        date: String(b.date || "").slice(0, 10) || new Date().toISOString().slice(0, 10),
        raw_note: String(b.raw_note), generated: null, generated_at: null, items: []
      };
      db.sessions.push(session);
      save(db, dataFile());
      return json(res, 201, { session });
    }

    const sm = p.match(/^\/api\/sessions\/([\w-]+)\/generate$/);
    if (sm && req.method === "POST") {
      const db = loadDb();
      const session = db.sessions.find((s) => s.id === sm[1]);
      if (!session) return json(res, 404, { error: "Sessão não encontrada" });
      const patient = db.patients.find((x) => x.id === session.patient_id);
      const generated = await organizeNote({
        note: session.raw_note,
        patientGoal: patient ? patient.patient_goal : null,
        apiKey: KEY,
        model: MODEL
      });
      session.generated = generated;
      session.generated_at = new Date().toISOString();
      session.items = ITEM_CATS.flatMap(([key, label]) =>
        (generated[key] || []).map((text) => ({ id: uid(), category: key, label, text: String(text), status: "pending" }))
      );
      save(db, dataFile());
      return json(res, 200, { session });
    }

    if (p === "/api/items" && req.method === "POST") {
      const b = await readBody(req);
      const db = loadDb();
      const session = db.sessions.find((s) => s.id === b.session_id);
      const item = session && session.items ? session.items.find((i) => i.id === b.item_id) : null;
      if (!item) return json(res, 404, { error: "Item não encontrado" });
      const next = applyAction(item.status, b.action);
      if (b.action === "edit") item.text = String(b.text == null ? "" : b.text);
      item.status = next.status;
      save(db, dataFile());
      return json(res, 200, { item });
    }

    if (p === "/api/data" && req.method === "POST" && u.searchParams.get("action") === "reset") {
      const f = dataFile();
      try { fs.rmSync(f); } catch {}
      return json(res, 200, { ok: true });
    }

    return json(res, 404, { error: "Rota não encontrada" });
  } catch (e) {
    const code = e instanceof ApiError ? e.status : (Number.isInteger(e && e.status) ? e.status : 500);
    return json(res, code >= 400 && code <= 599 ? code : 500, { error: e.message || String(e) });
  }
});

server.listen(PORT, () => console.log("LCA MVP (dados ficticios) em http://localhost:" + PORT));
