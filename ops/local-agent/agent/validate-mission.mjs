import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(here);
const mission=path.join(root,'workspaces','t002-missao1');
const source=await fs.readFile(path.join(mission,'input','transcricao.md'),'utf8');
const data=JSON.parse(await fs.readFile(path.join(mission,'output','extracao.json'),'utf8'));
const matches=[...source.matchAll(/\[(\d+:\d{2})\] Microphone:/g)];
const blocks=matches.map((x,i)=>({time:x[1],text:source.slice(x.index,matches[i+1]?.index||source.length)}));
const issues=[];
if(data.modelo!=='openai/gpt-5.1')issues.push({rule:'executor_model_metadata_incorrect'});
if(!Array.isArray(data.itens)||data.itens.length!==6)issues.push({rule:'item_count'});
const required=['id','minuto_origem','trecho_curto','modelo_estrutura','o_que_a_fonte_sustenta','limite','hipotese_lca','tarefa_proposta','metrica_proposta','resultado_lca_observado'];
for(const item of data.itens||[]) {
  for(const key of required)if(item[key]==null||item[key]==='')issues.push({id:item.id,rule:'missing_field',field:key});
  if(String(item.trecho_curto).length>180)issues.push({id:item.id,rule:'excerpt_too_long'});
  if(!source.includes(item.trecho_curto))issues.push({id:item.id,rule:'excerpt_not_literal'});
  const times=String(item.minuto_origem).match(/\d+:\d{2}/g)||[];
  if(!times.length||!times.some(t=>blocks.some(b=>b.time===t&&b.text.includes(item.trecho_curto))))issues.push({id:item.id,rule:'excerpt_timestamp_mismatch'});
  if(!/fisioterap|pacient|cl[ií]nic|concierge/i.test(item.hipotese_lca||''))issues.push({id:item.id,rule:'lca_context_missing'});
  if(String(item.resultado_lca_observado).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()!=='nao medido')issues.push({id:item.id,rule:'invented_outcome'});
}
if(!(data.itens||[]).some(x=>String(x.minuto_origem).includes('39:27')&&String(x.minuto_origem).includes('40:38')))issues.push({rule:'required_divergence_missing'});
const result={passed:issues.length===0,item_count:data.itens?.length,issues};
await fs.writeFile(path.join(mission,'output','validacao-codex.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));process.exitCode=result.passed?0:1;
