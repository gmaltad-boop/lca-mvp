import fs from "node:fs";
import https from "node:https";
import { organizeNote } from "../src/organize-note.js";

const KEY = process.env.OPENAI_API_KEY;

function getJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (r) => {
      let s = "";
      r.on("data", (c) => (s += c));
      r.on("end", () => resolve({ status: r.statusCode, text: s }));
    }).on("error", reject);
  });
}

const { status, text } = await getJson("https://api.openai.com/v1/models?limit=100");
let all = [];
if (status === 200) all = JSON.parse(text).data.map((m) => m.id);
console.log("modelos visiveis:", all.length, "| amostra:", all.slice(0, 25).join(", "));

const gpt = all.filter((m) => /gpt-/.test(m));
const cands = [];
for (const p of ["gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o"]) {
  const m = gpt.find((x) => x === p || x.startsWith(p + "-"));
  if (m && !cands.includes(m)) cands.push(m);
}
if (!cands.length) cands.push(...gpt.slice(0, 3));
if (!cands.length) cands.push("gpt-5.1");
console.log("candidatos a testar:", cands.join(", "));

const NOTE = `Paciente: P-001
Data: 30/10/2026
Sessao: 03
Queixa principal: dor lombar baixa, pior ao sentar por muito tempo e ao levantar da cadeira.

S:
Paciente refere melhora parcial desde a ultima sessao. Relata dor 4/10 ao sentar por mais de 30 min. Antes relatava 7/10. Diz que conseguiu fazer os exercicios em casa 2x na semana, mas esqueceu em alguns dias por rotina corrida. Relata medo de "travar" ao pegar peso no chao. Nega irradiação no momento. Refere melhora para levantar da cama pela manha.

O:
Chegou andando sem auxilio. Sem queixa importante durante marcha. Realizados exercicios de mobilidade lombopelvica, ponte, ativacao de gluteo medio, dissociacao quadril/lombar e treino de sentar-levantar. Boa tolerancia geral. Referiu desconforto leve no final do treino de sentar-levantar, sem piora sustentada. Necessitou correcao verbal para controle de tronco e respiracao. Orientado manter exercicios domiciliares 3x/semana e observar resposta nas proximas 24h.

Pontos importantes:
- Dor reduziu de 7/10 para 4/10 segundo relato.
- Adesao parcial aos exercicios.
- Medo de pegar peso ainda presente.
- Melhorou levantar da cama.
- Precisa reavaliar dor ao sentar e confianca para flexao/levantamento.

Pendencias:
- Nao foi aplicado questionario funcional porque ele nao soube responder as perguntas.
- Nao foi registrada escala de medo/evitacao.
- Nao foi medido tempo exato de tolerancia sentado alem do relato.`;

let written = false;
for (const model of cands.slice(0, 3)) {
  try {
    const out = await organizeNote({ note: NOTE, patientGoal: null, apiKey: KEY, model });
    fs.writeFileSync("tests/teste-01-saida-referencia.json", JSON.stringify(out, null, 2));
    console.log("\nOK modelo escolhido:", model);
    console.log("SAIDA (inicio):");
    console.log(JSON.stringify(out, null, 2).slice(0, 1800));
    written = true;
    break;
  } catch (e) {
    console.log("falha com " + model + " -> " + (e.status || "") + " " + String(e.message).slice(0, 220));
  }
}
if (!written) console.log("SEM_SAIDA_REFERENCIA");
