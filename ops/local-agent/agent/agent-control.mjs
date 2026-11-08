import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(here);
const stateFile=path.join(here,'mission-state.json');
const mode=process.argv[2]||'status';
const iterationLimit=process.argv.includes('--verified-run')?10:6;
const emit=x=>console.log(JSON.stringify(x));
let sessionKey;
try { sessionKey=(await fs.readFile(path.join(root,'state','agent-canvas','api-key.txt'),'utf8')).trim(); }
catch { emit({ready:false,reason:'local_service_not_initialized'});process.exit(2); }
async function api(route,method='GET',body) {
  const response=await fetch('http://127.0.0.1:8000'+route,{method,headers:{'X-Session-API-Key':sessionKey,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(45000)});
  const result=await response.json().catch(()=>({}));
  if(!response.ok) {
    const e=new Error('local_api_error');e.status=response.status;e.route=route;
    e.validation=Array.isArray(result.detail)?result.detail.map(x=>({loc:x.loc,type:x.type})):undefined;
    throw e;
  }
  return result;
}
try {
  if(mode==='probe') {
    const response=await fetch('http://127.0.0.1:8000/canvas',{signal:AbortSignal.timeout(10000)});
    emit({ready:response.ok,http_status:response.status});
  } else if(mode==='start') {
    try {await fs.access(stateFile);throw new Error('mission_already_initialized');}catch(e){if(e.message==='mission_already_initialized')throw e;}
    const env=await fs.readFile(path.join(here,'.env.local'),'utf8');
    const key=env.match(/^OPENAI_API_KEY\s*=\s*(.+)$/m)?.[1]?.trim().replace(/^['"]|['"]$/g,'');
    if(!key)throw new Error('key_not_configured');
    const llm={model:'openai/gpt-5.1',api_key:key,max_output_tokens:6000,reasoning_effort:'none'};
    await api('/api/profiles/lca-missao-1','POST',{llm,include_secrets:true});
    await api('/api/profiles/lca-missao-1/activate','POST');
    const id=randomUUID();
    const result=await api('/api/conversations','POST',{conversation_id:id,workspace:{kind:'LocalWorkspace',working_dir:'/projects/t002/output'},worktree:false,max_iterations:iterationLimit,stuck_detection:true,autotitle:false,confirmation_policy:{kind:'NeverConfirm'},agent_settings:{agent_kind:'openhands',llm,condenser:{enabled:false},verification:{critic_enabled:false,enable_iterative_refinement:false},tools:[{name:'terminal',params:{}}]},client_tools:[]});
    const actualId=result.id||result.conversation_id||id;
    await fs.writeFile(stateFile,JSON.stringify({id:actualId,model:llm.model,started_at:new Date().toISOString(),event_submission:'pending'},null,2));
    const message='Missão revisada com ferramenta mínima: use APENAS terminal, no máximo seis ações. Ação1: leia em UM comando /projects/t002/MISSAO.md e /projects/t002/input/contexto-selecionado.md. Não leia a transcrição inteira nem outros arquivos: o recorte literal de 8 blocos basta e a cobertura parcial deve ser declarada. Ação2: em UM script Python, construa os seis itens e grave extracao.json e relatorio.md em /projects/t002/output/. Para trecho_curto, use uma fatia literal de até150 caracteres de cada bloco original, extraída programaticamente do arquivo, sem reescrever ou completar frases. Produza seis itens nos grupos 13:54,18:08,19:38,39:27+40:38+42:05,68:06,80:16. Aplicações devem ser estritamente observações ou medições administrativas/comerciais do concierge LCA para fisioterapeutas; nenhum módulo, cadastro de pacientes, ferramenta clínica, produto ou automação nova. Ação3: rode python /projects/t002/validate.py; se falhar, corrija por Python e repita dentro do limite. Não crie plano ou tracker e não releia arquivos completos. Não use internet, outros agentes, integrações, credenciais ou ambiente do processo. Pare após passed=true e diga o resultado. Metadados reais: executor OpenHands Agent Canvas1.34.0/SDK1.58.1, modelo openai/gpt-5.1. Fonte de origem única transcricao.md. Resultado LCA observado não medido.';
    await api(`/api/conversations/${actualId}/events`,'POST',{role:'user',content:[{type:'text',text:message}],run:true});
    await fs.writeFile(stateFile,JSON.stringify({id:actualId,model:llm.model,started_at:new Date().toISOString(),event_submission:'submitted'},null,2));
    emit({id:actualId,mission_submitted:true,max_iterations:iterationLimit,max_output_tokens:6000});
  } else {
    const saved=JSON.parse(await fs.readFile(stateFile,'utf8'));
    if(mode==='interrupt') {await api(`/api/conversations/${saved.id}/interrupt`,'POST');emit({id:saved.id,interrupt_requested:true});}
    else if(mode==='feedback') {
      const message=await fs.readFile(path.join(here,'review-feedback.txt'),'utf8');
      await api(`/api/conversations/${saved.id}/events`,'POST',{role:'user',content:[{type:'text',text:message}],run:true});
      emit({id:saved.id,review_feedback_submitted:true});
    }
    else if(mode==='run') {await api(`/api/conversations/${saved.id}/run`,'POST');emit({id:saved.id,resume_requested:true});}
    else if(mode==='final') {
      const result=await api(`/api/conversations/${saved.id}/agent_final_response`);
      const text=typeof result.response==='string'?result.response:'';
      const keyPattern=/sk-[A-Za-z0-9_-]{12,}/g;
      await fs.writeFile(path.join(root,'workspaces','t002-missao1','output','agent-final.txt'),text.replace(keyPattern,'[REDACTED]'));
      emit({id:saved.id,final_saved:true,characters:text.length});
    } else if(mode==='events'||mode==='diagnostics'||mode==='trace') {
      const data=await api(`/api/conversations/${saved.id}/events/search?limit=100`);
      const events=Array.isArray(data)?data:(data.items||data.events||[]);
      if(mode==='diagnostics'||mode==='trace') {
        const env=await fs.readFile(path.join(here,'.env.local'),'utf8');
        const key=env.match(/^OPENAI_API_KEY\s*=\s*(.+)$/m)?.[1]?.trim().replace(/^['"]|['"]$/g,'');
        const errors=events.filter(x=>mode==='trace'?['ActionEvent','ObservationEvent','ConversationErrorEvent'].includes(x.kind):String(x.kind||'').includes('Error')).map(x=>({kind:x.kind,details:x.detail||x.details||x.error||x.message||x.error_message,action:mode==='trace'?x.action:undefined,observation:mode==='trace'?JSON.stringify(x.observation||{}).slice(0,600):undefined,fields:Object.keys(x)}));
        let text=JSON.stringify({id:saved.id,errors});
        if(key)text=text.split(key).join('[REDACTED]');
        text=text.split(sessionKey).join('[REDACTED]').replace(/sk-[A-Za-z0-9_-]+/g,'[REDACTED]').replace(/[A-Za-z0-9_-]{40,}/g,'[REDACTED]');
        console.log(text.slice(0,16000));
      } else emit({id:saved.id,event_count:events.length,events:events.map(x=>({kind:x.kind,source:x.source,type:x.type,tool_name:x.tool_name,error_code:x.error_code})).slice(-20)});
    } else {
      const result=await api(`/api/conversations/${saved.id}`);
      const metrics=result.stats||result.metrics||{};
      const usages=Object.values(metrics.usage_to_metrics||{});
      emit({id:saved.id,status:result.execution_status,reported_cost_usd:usages.reduce((s,x)=>s+(x.accumulated_cost||0),0),prompt_tokens:usages.reduce((s,x)=>s+(x.accumulated_token_usage?.prompt_tokens||0),0),completion_tokens:usages.reduce((s,x)=>s+(x.accumulated_token_usage?.completion_tokens||0),0)});
    }
  }
} catch(e) {emit({ok:false,reason:['mission_already_initialized','key_not_configured'].includes(e.message)?e.message:'operation_failed',http_status:e.status,network_code:e.cause?.code,error_type:e.name,route:e.route,validation:e.validation});process.exitCode=1;}
