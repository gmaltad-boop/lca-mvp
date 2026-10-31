import test from "node:test";
import assert from "node:assert/strict";
import { validateOutput, SCHEMA } from "../src/schema.js";

function good() {
  return {
    patient_memory: [], observed_facts: ["a"],
    professional_hypotheses: ["nenhuma hipótese registrada"],
    information_gaps: [], revisable_clinical_evolution: [], reminders: [],
    follow_up_questions: [], patient_goal: null, goal_progress: [],
    new_achievements: [], safety_note: "ok"
  };
}
test("aceita objeto valido", () => {
  assert.doesNotThrow(() => validateOutput(good()));
});
test("rejeita chave ausente", () => {
  const o = good(); delete o.safety_note;
  assert.throws(() => validateOutput(o));
});
test("rejeita status fora do enum", () => {
  const o = good(); o.goal_progress = [{ criterion: "x", status: "melhorou" }];
  assert.throws(() => validateOutput(o));
});
test("rejeita patient_goal numerico", () => {
  const o = good(); o.patient_goal = 3;
  assert.throws(() => validateOutput(o));
});
test("schema exige exatamente todos os campos declarados", () => {
  assert.deepEqual([...SCHEMA.required].sort(), [...Object.keys(SCHEMA.properties)].sort());
});
