import test from "node:test";
import assert from "node:assert/strict";
import { organizeNote, buildPayload, ApiError } from "../src/organize-note.js";

const GOOD = {
  patient_memory: [], observed_facts: ["relata dor 4/10"],
  professional_hypotheses: ["nenhuma hipótese registrada"],
  information_gaps: ["objetivo do paciente não informado — registrar nas palavras do paciente"],
  revisable_clinical_evolution: ["Paciente refere melhora parcial."],
  reminders: ["Reavaliar dor ao sentar."],
  follow_up_questions: ["Como ficou nas últimas 24h?"],
  patient_goal: null, goal_progress: [], new_achievements: [], safety_note: "Rascunho sujeito a revisao."
};
const okPost = () => Promise.resolve({ status: 200, text: JSON.stringify({ output_text: JSON.stringify(GOOD) }) });

test("payload usa store:false, strict e sistema com regras", () => {
  const p = buildPayload("nota x", null, "m");
  assert.equal(p.store, false);
  assert.equal(p.text.format.strict, true);
  assert.match(p.input[0].content, /NAO diagnostica/);
});
test("organiza com transporte mockado (sucesso)", async () => {
  const out = await organizeNote({ note: "nota", apiKey: "k", post: okPost });
  assert.deepEqual(out, GOOD);
});
test("nota vazia -> ApiError 400", async () => {
  await assert.rejects(
    () => organizeNote({ note: "   ", apiKey: "k", post: okPost }),
    (e) => e instanceof ApiError && e.status === 400
  );
});
test("chave ausente -> ApiError 500", async () => {
  await assert.rejects(
    () => organizeNote({ note: "n", apiKey: "", post: okPost }),
    (e) => e instanceof ApiError && e.status === 500
  );
});
test("HTTP 500 vira ApiError com mensagem", async () => {
  const post = () => Promise.resolve({ status: 500, text: JSON.stringify({ error: { message: "boom" } }) });
  await assert.rejects(
    () => organizeNote({ note: "n", apiKey: "k", post }),
    (e) => e instanceof ApiError && e.status === 500 && /boom/.test(e.message)
  );
});
test("recusa do modelo e detectada", async () => {
  const post = () => Promise.resolve({ status: 200, text: JSON.stringify({ output: [{ type: "message", refusal: "conteudo sensivel", content: [] }] }) });
  await assert.rejects(
    () => organizeNote({ note: "n", apiKey: "k", post }),
    (e) => e instanceof ApiError && /recusou/i.test(e.message)
  );
});
test("JSON malformado -> ApiError 500", async () => {
  const post = () => Promise.resolve({ status: 200, text: JSON.stringify({ output_text: "{nao-json" }) });
  await assert.rejects(
    () => organizeNote({ note: "n", apiKey: "k", post }),
    (e) => e instanceof ApiError && e.status === 500
  );
});
