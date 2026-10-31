import test from "node:test";
import assert from "node:assert/strict";
import { applyAction, STATUSES } from "../src/state.js";

test("editar a partir de pendente produz edited (NUNCA approved)", () => {
  assert.equal(applyAction("pending", "edit").status, "edited");
});
test("aprovar pendente -> approved", () => {
  assert.equal(applyAction("pending", "approve").status, "approved");
});
test("descartar edited -> discarded", () => {
  assert.equal(applyAction("edited", "discard").status, "discarded");
});
test("editar um item aprovado volta a edited (nova aprovacao necessaria)", () => {
  assert.equal(applyAction("approved", "edit").status, "edited");
});
test("editar um item descartado reabre como edited", () => {
  assert.equal(applyAction("discarded", "edit").status, "edited");
});
test("transicao inexistente lanca erro", () => {
  assert.throws(() => applyAction("pending", "voar"));
});
test("status conhecidos", () => {
  assert.deepEqual([...STATUSES].sort(), ["approved", "discarded", "edited", "pending"]);
});
