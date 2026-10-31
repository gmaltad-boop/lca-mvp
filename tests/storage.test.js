import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { load, save } from "../src/storage.js";

const F = "data/teste-storage.json";
test("save/load faz roundtrip fiel", () => {
  const d = { patients: [{ id: "p1", label: "Paciente A" }], sessions: [] };
  save(d, F);
  assert.deepEqual(load(F), d);
  fs.rmSync(F, { force: true });
});
test("arquivo ausente retorna estrutura vazia", () => {
  assert.deepEqual(load("data/nao-existe.json"), { patients: [], sessions: [] });
});
