// Chamada a OpenAI Responses API (Structured Outputs, strict) + validacao.
import https from "node:https";
import { SCHEMA, SYSTEM_PROMPT, validateOutput } from "./schema.js";

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

function postJson(url, headers, body, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({
      hostname: u.hostname, path: u.pathname, method: "POST",
      headers: { ...headers, "Content-Length": Buffer.byteLength(body) }
    }, (res) => {
      let s = "";
      res.on("data", (c) => (s += c));
      res.on("end", () => resolve({ status: res.statusCode, text: s }));
    });
    req.setTimeout(timeoutMs, () => req.destroy(new Error("timeout na API")));
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

export function buildPayload(note, patientGoal, model) {
  const user = [
    "Objetivo cadastrado do paciente: " + (patientGoal ? JSON.stringify(patientGoal) : "(nenhum cadastrado)"),
    "",
    "Organize esta nota de atendimento para revisao profissional:",
    "",
    note
  ].join("\n");
  return {
    model,
    store: false,
    input: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: user }
    ],
    text: { format: { type: "json_schema", name: "lca_note", strict: true, schema: SCHEMA } }
  };
}

function extractText(body) {
  if (typeof body.output_text === "string" && body.output_text.length) return body.output_text;
  const out = Array.isArray(body.output) ? body.output : [];
  const ref = out.find((o) => o.refusal != null);
  if (ref) throw new ApiError("O modelo recusou a resposta: " + ref.refusal, 403);
  const msg = out.find((o) => o.type === "message");
  if (msg && Array.isArray(msg.content) && msg.content[0] && msg.content[0].text) return msg.content[0].text;
  throw new ApiError("Resposta da API sem texto utilizavel", 500);
}

export async function organizeNote({ note, patientGoal = null, apiKey, model = "gpt-5.1", post = postJson }) {
  if (!apiKey) throw new ApiError("OPENAI_API_KEY ausente (defina no .env)", 500);
  if (!note || !note.trim()) throw new ApiError("Nota vazia", 400);
  const { status, text } = await post(
    "https://api.openai.com/v1/responses",
    { "Content-Type": "application/json", Authorization: "Bearer " + apiKey },
    JSON.stringify(buildPayload(note, patientGoal, model))
  );
  let body;
  try { body = JSON.parse(text || "{}"); } catch { throw new ApiError("Resposta nao-JSON da API", 500); }
  if (status < 200 || status >= 300) throw new ApiError((body.error && body.error.message) || "HTTP " + status, status);
  let raw;
  try { raw = extractText(body); } catch (e) { if (e instanceof ApiError) throw e; throw new ApiError("Saida da API fora do formato esperado", 500); }
  let parsed;
  try { parsed = JSON.parse(raw); } catch { throw new ApiError("Saida da API fora do formato esperado", 500); }
  return validateOutput(parsed);
}
