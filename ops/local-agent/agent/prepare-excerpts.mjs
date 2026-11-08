import fs from 'node:fs/promises';
const base=new URL('../workspaces/t002-missao1/input/',import.meta.url);
const source=await fs.readFile(new URL('transcricao.md',base),'utf8');
const matches=[...source.matchAll(/\[(\d+:\d{2})\] Microphone:/g)];
const times=new Set(['13:54','18:08','19:38','39:27','40:38','42:05','68:06','80:16']);
const blocks=matches.map((m,i)=>({time:m[1],text:source.slice(m.index,matches[i+1]?.index||source.length)})).filter(b=>times.has(b.time));
await fs.writeFile(new URL('contexto-selecionado.md',base),'# Recorte literal para a tentativa corrigida\n\nOrigem: transcricao.md; selecao do coordenador apos falhas anteriores. Cobertura parcial: nao afirmar leitura integral nesta tentativa.\n\n'+blocks.map(b=>b.text).join('\n\n'));
console.log(JSON.stringify({blocks:blocks.length,characters:blocks.reduce((n,b)=>n+b.text.length,0)}));
