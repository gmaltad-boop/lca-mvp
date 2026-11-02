import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { findPython } from './python-runtime.mjs';

// Local stdio only. No shell, downloads, policy changes or credential lookup.
try {
  const env = { ...process.env };
  for (const name of ['OPENAI_API_KEY', 'DRAEL_API_KEY', 'LCA_DISCORD_BOT_TOKEN']) delete env[name];
  const child = spawn(findPython(), [join(dirname(fileURLToPath(import.meta.url)), 'mcp_server.py')], {
    stdio: 'inherit', shell: false, windowsHide: true, env
  });
  child.on('error', () => { process.stderr.write('LCA: não foi possível iniciar o Python configurado.\n'); process.exitCode = 2; });
  child.on('exit', code => { process.exitCode = code ?? 2; });
} catch {
  process.stderr.write('LCA: configure LCA_PYTHON_EXE com o executável real do Python.\n');
  process.exitCode = 2;
}
