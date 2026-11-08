import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

export function findPython() {
  if (process.env.LCA_PYTHON_EXE) {
    if (!existsSync(process.env.LCA_PYTHON_EXE)) throw new Error('LCA_PYTHON_EXE inválido');
    return process.env.LCA_PYTHON_EXE;
  }
  if (process.platform !== 'win32') return 'python3';
  const base = join(process.env.LOCALAPPDATA || '', 'Python');
  if (existsSync(base)) {
    const options = readdirSync(base, { withFileTypes: true })
      .filter(item => item.isDirectory() && /^pythoncore-[0-9]/.test(item.name))
      .map(item => join(base, item.name, 'python.exe')).filter(existsSync);
    if (options.length === 1) return options[0];
  }
  throw new Error('Configure o executável real do Python em LCA_PYTHON_EXE; não será instalado automaticamente.');
}
