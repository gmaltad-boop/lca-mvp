const app = document.getElementById("app");
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function api(path, opts = {}) {
  const r = await fetch("/api" + path, {
    method: opts.method || "GET",
    headers: { "Content-Type": "application/json" },
    body: opts.body ? JSON.stringify(opts.body) : undefined
  });
  let j = {};
  try { j = await r.json(); } catch {}
  if (!r.ok) throw new Error(j.error || "HTTP " + r.status);
  return j;
}

const BADGE = { pending: "pendente", edited: "editado · aguarda aprovação", approved: "aprovado", discarded: "descartado" };
const badge = (st) => '<span class="badge b-' + st + '">' + (BADGE[st] || st) + "</span>";

async function render() {
  const h = location.hash || "#/";
  try {
    if (h === "#/") return await renderPatients();
    let m = h.match(/^#\/paciente\/([\w-]+)$/);
    if (m) return await renderPatient(m[1]);
    m = h.match(/^#\/revisao\/([\w-]+)$/);
    if (m) return await renderReview(m[1]);
    app.innerHTML = "<p>Rota desconhecida.</p>";
  } catch (e) {
    app.innerHTML = '<div class="card error"><strong>Não foi possível carregar.</strong><br>' + esc(e.message) + "</div>";
  }
}
window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);

async function renderPatients() {
  const { patients } = await api("/patients");
  app.innerHTML =
    "<h2>Pacientes (dados fictícios)</h2>" +
    '<form id="np" class="card form">' +
      '<input id="np-label" placeholder="Rótulo fictício (ex.: Paciente A)" maxlength="60" required>' +
      '<input id="np-goal" placeholder="Objetivo (opcional, nas palavras do paciente — ex.: voltar à feira)">' +
      "<button>Adicionar paciente</button>" +
    "</form>" +
    '<ul class="list">' +
      (patients.map((p) =>
        "<li><a href='#/paciente/" + p.id + "'><strong>" + esc(p.label) + "</strong></a> " +
        (p.patient_goal ? '<span class="goal">objetivo: ' + esc(p.patient_goal) + "</span>" : '<span class="muted">sem objetivo cadastrado</span>') +
        "</li>").join("") || '<li class="muted">Nenhum paciente ainda — adicione acima.</li>') +
    "</ul>" +
    (patients.length ? '<button class="danger" id="wipe">Apagar dados locais</button>' : "");
  document.getElementById("np").onsubmit = async (e) => {
    e.preventDefault();
    await api("/patients", { method: "POST", body: { label: document.getElementById("np-label").value, patient_goal: document.getElementById("np-goal").value } });
    render();
  };
  const w = document.getElementById("wipe");
  if (w) w.onclick = async () => {
    if (confirm("Apagar TODOS os dados locais deste protótipo?")) {
      await api("/data?action=reset", { method: "POST" });
      render();
    }
  };
}

async function renderPatient(id) {
  const { patient, sessions } = await api("/patients/" + id);
  app.innerHTML =
    '<div class="row"><a href="#/">← pacientes</a><h2>' + esc(patient.label) + "</h2></div>" +
    (patient.patient_goal
      ? '<div class="card"><strong>Objetivo cadastrado:</strong> <span class="goal">“' + esc(patient.patient_goal) + '”</span></div>'
      : '<div class="card muted">Nenhum objetivo cadastrado (opcional — registre nas palavras do paciente).</div>') +
    '<form id="ns" class="card form">' +
      "<h3>Nova sessão</h3>" +
      '<input type="date" id="ns-date" value="' + new Date().toISOString().slice(0, 10) + '">' +
      '<textarea id="ns-note" rows="7" placeholder="Cole aqui a nota de atendimento (dados fictícios ou anonimizados)."></textarea>' +
      '<button id="ns-btn">Salvar e gerar resumo estruturado</button>' +
      '<span id="ns-msg" class="muted"></span>' +
    "</form>" +
    '<ul class="list">' +
      (sessions.map((s) => {
        const c = { pending: 0, edited: 0, approved: 0, discarded: 0 };
        for (const i of s.items || []) c[i.status]++;
        const rev = s.generated
          ? '<span class="muted small">' + (s.items || []).length + " itens · pendente " + c.pending + " · editado " + c.edited + " · aprovado " + c.approved + " · descartado " + c.discarded + "</span>"
          : '<span class="badge b-pending">sem resumo gerado</span>';
        return '<li><a href="#/revisao/' + s.id + '"><strong>' + esc(s.date) + "</strong></a> — " + rev + "</li>";
      }).join("") || '<li class="muted">Nenhuma sessão ainda.</li>') +
    "</ul>";
  document.getElementById("ns").onsubmit = async (e) => {
    e.preventDefault();
    const btn = document.getElementById("ns-btn");
    const msg = document.getElementById("ns-msg");
    const note = document.getElementById("ns-note").value;
    if (!note.trim()) { msg.textContent = "Cole uma nota antes de gerar."; return; }
    btn.disabled = true;
    msg.textContent = "Salvando a sessão…";
    try {
      const { session } = await api("/sessions", { method: "POST", body: { patient_id: id, date: document.getElementById("ns-date").value, raw_note: note } });
      msg.textContent = "Gerando resumo estruturado… (alguns segundos)";
      await api("/sessions/" + session.id + "/generate", { method: "POST" });
      location.hash = "#/revisao/" + session.id;
    } catch (err) {
      msg.textContent = err.message;
      btn.disabled = false;
    }
  };
}

async function renderReview(sid) {
  const { session } = await api("/sessions?id=" + sid);
  const gen = session.generated;
  const c = { pending: 0, edited: 0, approved: 0, discarded: 0 };
  for (const i of session.items || []) c[i.status] = (c[i.status] || 0) + 1;
  const total = (session.items || []).length;

  const goalBlock = gen && gen.patient_goal
    ? '<div class="card"><h3>Progresso ao objetivo</h3><div class="goal">“' + esc(gen.patient_goal) + '”</div>' +
      ((gen.goal_progress || []).length
        ? "<ul>" + gen.goal_progress.map((g) => '<li><span class="chip">' + g.status.replace("_", " ") + "</span> " + esc(g.criterion) + "</li>").join("") + "</ul>"
        : '<p class="muted">Sem critérios com suporte explícito nesta nota.</p>') +
      "</div>"
    : '<div class="card muted">Sem objetivo cadastrado — sem vínculo de progresso nesta sessão.</div>';

  const memBlock = gen && (gen.patient_memory || []).length
    ? '<details class="card"><summary>Memória do paciente (' + gen.patient_memory.length + ")</summary><ul>" +
      gen.patient_memory.map((t) => "<li>" + esc(t) + "</li>").join("") + "</ul></details>"
    : "";

  const cards = (session.items || []).map((it) => {
    const actions = [];
    if (it.status === "pending" || it.status === "edited") actions.push('<button data-a="approve" data-id="' + it.id + '">Aprovar</button>');
    if (it.status !== "approved") actions.push('<button data-a="discard" data-id="' + it.id + '">Descartar</button>');
    if (it.status !== "discarded") actions.push('<button data-a="edit" data-id="' + it.id + '">Editar</button>');
    if (it.status === "discarded") actions.push('<button data-a="approve" data-id="' + it.id + '">Aprovar (reabrir)</button>');
    return '<div class="card item" data-item="' + it.id + '">' +
      '<div class="itemhead">' + esc(it.label) + " " + badge(it.status) + "</div>" +
      '<p class="itemtext" id="txt-' + it.id + '">' + esc(it.text) + "</p>" +
      '<div class="actions"><button class="ghost" data-a="locate" data-id="' + it.id + '">Localizar na nota</button>' + actions.join("") + "</div>" +
      '<div class="editor" id="ed-' + it.id + '" hidden><textarea id="ta-' + it.id + '" rows="4">' + esc(it.text) + "</textarea>" +
      '<div><button data-a="save-edit" data-id="' + it.id + '">Salvar edição</button> <button class="ghost" data-a="cancel-edit" data-id="' + it.id + '">Cancelar</button></div></div>' +
      "</div>";
  }).join("");

  app.innerHTML =
    '<div class="row"><a href="#/paciente/' + session.patient_id + '">← ' + esc(session.date) + '</a><h2>Revisão do resumo</h2></div>' +
    '<div class="summarybar"><span class="chip">' + total + " itens</span>" +
    '<span class="chip">pendentes ' + c.pending + '</span><span class="chip">editados ' + c.edited + '</span>' +
    '<span class="chip">aprovados ' + c.approved + '</span><span class="chip">descartados ' + c.discarded + '</span>' +
    '<span class="muted">regra: editar ≠ aprovar</span></div>' +
    (gen && gen.safety_note ? '<div class="banner2">' + esc(gen.safety_note) + "</div>" : "") +
    '<div class="reviewgrid"><section class="card notepanel" id="notepanel"><h3>Nota original</h3><pre id="note-text">' + esc(session.raw_note) + "</pre></section>" +
    '<section class="items">' + goalBlock + memBlock + (cards || '<div class="card muted">Nenhum item gerado.</div>') + "</section></div>";

  app.querySelectorAll("[data-a]").forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      const a = btn.dataset.a;
      const iid = btn.dataset.id;
      if (a === "locate") { locateInNote(iid); return; }
      if (a === "cancel-edit") { document.getElementById("ed-" + iid).hidden = true; return; }
      if (a === "edit") {
        const ta = document.getElementById("ta-" + iid);
        ta.value = document.getElementById("txt-" + iid).textContent;
        document.getElementById("ed-" + iid).hidden = false;
        return;
      }
      const action = a === "save-edit" ? "edit" : a;
      const text = a === "save-edit" ? document.getElementById("ta-" + iid).value : undefined;
      try {
        await api("/items", { method: "POST", body: { session_id: sid, item_id: iid, action, text } });
        renderReview(sid);
      } catch (err) { alert(err.message); }
    };
  });
}

function locateInNote(itemId) {
  const el = document.querySelector('.item[data-item="' + itemId + '"] .itemtext');
  const pre = document.getElementById("note-text");
  if (!el || !pre) return;
  const tokens = el.textContent.trim().split(/\s+/);
  const t = pre.textContent;
  const lt = t.toLowerCase();
  let snippet = null;
  for (let n = Math.min(tokens.length, 8); n >= 3; n--) {
    const cand = tokens.slice(0, n).join(" ");
    if (lt.includes(cand.toLowerCase())) { snippet = cand; break; }
  }
  if (!snippet) {
    const np = document.getElementById("notepanel");
    np.classList.add("flash");
    setTimeout(() => np.classList.remove("flash"), 1200);
    return;
  }
  const idx = lt.indexOf(snippet.toLowerCase());
  pre.innerHTML = esc(t.slice(0, idx)) + "<mark>" + esc(t.slice(idx, idx + snippet.length)) + "</mark>" + esc(t.slice(idx + snippet.length));
  pre.querySelector("mark").scrollIntoView({ behavior: "smooth", block: "center" });
}
