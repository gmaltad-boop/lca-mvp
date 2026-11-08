import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { findPython } from '../server/python-runtime.mjs';

try {
  const child = spawn(findPython(), ['-m', 'unittest', 'discover', '-s', join(dirname(fileURLToPath(import.meta.url)), '../tests'), '-v'], {
    stdio: 'inherit', shell: false, windowsHide: true,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' }
  });
  child.on('error', () => { process.stderr.write('Não foi possível iniciar o Python.\n'); process.exitCode = 2; });
  child.on('exit', code => { process.exitCode = code ?? 2; });
} catch {
  process.stderr.write('Configure LCA_PYTHON_EXE com o executável real do Python.\n');
  process.exitCode = 2;
}
