import fs from 'node:fs/promises';
const text = await fs.readFile(new URL('./.env.local', import.meta.url), 'utf8');
const key = text.match(/^OPENAI_API_KEY\s*=\s*(.+)$/m)?.[1]?.trim().replace(/^['"]|['"]$/g, '');
if (!key) { console.log(JSON.stringify({configured:false})); process.exit(1); }
try {
  const live = process.argv.includes('--live');
  const response = await fetch(live?'https://api.openai.com/v1/responses':'https://api.openai.com/v1/models', {method:live?'POST':'GET',headers:{Authorization:`Bearer ${key}`,'Content-Type':'application/json'},body:live?JSON.stringify({model:'gpt-5.1',input:'Responda apenas OK.',max_output_tokens:64,store:false,reasoning:{effort:'none'}}):undefined,signal:AbortSignal.timeout(45000)});
  const body = await response.json();
  console.log(JSON.stringify({configured:true,check:live?'bounded_generation':'model_access',authenticated:response.ok,http_status:response.status,gpt_5_1_available:live?undefined:body.data?.some(x=>x.id==='gpt-5.1')??false,response_status:body.status,usage:body.usage,error_code:response.ok?undefined:body.error?.code}));
  process.exitCode=response.ok?0:1;
} catch { console.log(JSON.stringify({configured:true,authenticated:false,network_error:true})); process.exitCode=1; }
