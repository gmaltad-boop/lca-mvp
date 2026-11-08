import json,re,unicodedata,pathlib,sys
root=pathlib.Path('/projects/t002')
source=(root/'input/transcricao.md').read_text(encoding='utf-8')
data=json.loads((root/'output/extracao.json').read_text(encoding='utf-8'))
matches=list(re.finditer(r'\[(\d+:\d{2})\] Microphone:',source))
blocks=[(m.group(1),source[m.start():matches[i+1].start() if i+1<len(matches) else len(source)]) for i,m in enumerate(matches)]
errors=[]
if data.get('modelo')!='openai/gpt-5.1': errors.append('modelo deve ser openai/gpt-5.1')
items=data.get('itens',[])
if len(items)!=6: errors.append('exatamente seis itens')
for item in items:
    prefix=str(item.get('id'))+': '
    for field in ['id','minuto_origem','trecho_curto','modelo_estrutura','o_que_a_fonte_sustenta','limite','hipotese_lca','tarefa_proposta','metrica_proposta','resultado_lca_observado']:
        if item.get(field) is None or item.get(field)=='': errors.append(prefix+'campo ausente: '+field)
    quote=item.get('trecho_curto','')
    times=re.findall(r'\d+:\d{2}',str(item.get('minuto_origem','')))
    if not quote or len(quote)>180: errors.append(prefix+'trecho vazio ou maior que 180 caracteres')
    if not any(t in times and quote in b for t,b in blocks): errors.append(prefix+'trecho nao e literal no minuto informado')
    if not re.search(r'fisioterap|pacient|cl[ií]nic|concierge',item.get('hipotese_lca',''),re.I): errors.append(prefix+'hipotese fora do contexto LCA')
    normalized=''.join(c for c in unicodedata.normalize('NFD',item.get('resultado_lca_observado','')) if unicodedata.category(c)!='Mn').lower()
    if normalized!='nao medido': errors.append(prefix+'resultado deve ser nao medido')
if not any('39:27' in str(x.get('minuto_origem')) and '40:38' in str(x.get('minuto_origem')) for x in items): errors.append('divergencia obrigatoria ausente')
print(json.dumps({'passed':not errors,'errors':errors},ensure_ascii=False))
sys.exit(1 if errors else 0)
