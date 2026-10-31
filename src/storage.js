// Armazenamento local em JSON. Data viva em data/lca.json (fora do git).
import fs from "node:fs";
import path from "node:path";

export const EMPTY = () => ({ patients: [], sessions: [] });

export function load(file) {
  try {
    const data = JSON.parse(fs.readFileSync(file, "utf8"));
    return { patients: Array.isArray(data.patients) ? data.patients : [],
             sessions: Array.isArray(data.sessions) ? data.sessions : [] };
  } catch {
    return EMPTY();
  }
}

export function save(data, file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, file);
}

export function reset(file) {
  try { fs.rmSync(file); } catch {}
  return load(file);
}

export function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}
