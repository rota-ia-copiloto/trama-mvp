from datetime import date, timedelta
from statistics import mean
from collections import Counter
import hashlib
import json
import math

AS_OF = date(2026, 11, 17)
MIN_GROUP = 10
STATES = ['Rascunho', 'Em revisão', 'Aprovada', 'Em execução', 'Em avaliação', 'Concluída']

def dt(value):
    return date.fromisoformat(value) if value else None

def ratio(n, d):
    return n / d if d else None

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def scope_match(row, operation, occupation=None):
    return row.get('operation_id') == operation and (not occupation or row.get('occupation') == occupation)

def workforce_metrics(people, hires, start, end):
    days = (end - start).days + 1
    headcounts = [sum(dt(p['start']) <= start+timedelta(days=i) and (not p.get('end') or dt(p['end']) >= start+timedelta(days=i)) for p in people) for i in range(days)]
    avg = mean(headcounts) if headcounts else 0
    departures = sum(p.get('end') is not None and start <= dt(p['end']) <= end and p.get('voluntary', False) for p in people)
    events = [h for h in hires if start <= dt(h['opened']) <= end]
    accepted = sum(h['status'] == 'Aceita' for h in events)
    refused = sum(h['status'] == 'Recusada' for h in events)
    filled = [h for h in events if h.get('filled') and dt(h['filled']) <= end]
    fill_days = [(dt(h['filled'])-dt(h['opened'])).days for h in filled]
    retention = {}
    cohort = [p for p in people if start <= dt(p['start']) <= end]
    for horizon in [90, 180]:
        mature = [p for p in cohort if dt(p['start'])+timedelta(days=horizon) <= end]
        retained = sum(not p.get('end') or dt(p['end']) >= dt(p['start'])+timedelta(days=horizon) for p in mature)
        retention[horizon] = {'n':retained, 'd':len(mature), 'pending':len(cohort)-len(mature), 'value':ratio(retained, len(mature))}
    return {'turnover':{'n':departures,'d':avg,'value':ratio(departures,avg)}, 'acceptance':{'n':accepted,'d':accepted+refused,'value':ratio(accepted,accepted+refused)}, 'fill':{'value':mean(fill_days) if fill_days else None,'d':len(fill_days)}, 'open':sum(h['status'] in ['Pendente','Aceita'] and not h.get('filled') for h in events), 'pending':sum(h['status']=='Pendente' for h in events), 'withdrawn':sum(h['status']=='Desistência' for h in events), 'retention':retention}

def safe_listening(rows, start, end, threshold=MIN_GROUP):
    selected = [r for r in rows if start <= dt(r['date']) <= end]
    # Aggregate only: never return free text or respondent-level data to dashboard/LLM/export.
    if len(selected) < threshold:
        return {'suppressed':True,'reason':f'Conteúdo protegido: mínimo de {threshold} respostas neste recorte.'}
    counts = Counter(r['theme'] for r in selected)
    return {'suppressed':False, 'n':len(selected), 'themes':dict(counts), 'interested':sum(r.get('interested',False) for r in selected), 'channels':dict(Counter(r['channel'] for r in selected))}

def economic(benefits, costs):
    if any(not math.isfinite(float(x)) or float(x) < 0 for x in [*benefits,*costs]):
        raise ValueError('Valores devem ser finitos e não negativos.')
    total_b, total_c = sum(benefits), sum(costs)
    return {'benefit':total_b,'cost':total_c,'net':total_b-total_c,'roi':ratio(total_b-total_c,total_c)}

def unique_benefits(channels):
    seen=set(); result=[]
    for item in channels:
        if not item.get('included'): continue
        key=item.get('effect_id')
        if not key: raise ValueError('Identifique o efeito econômico.')
        if key in seen: raise ValueError('Mesmo efeito incluído em mais de um canal.')
        seen.add(key); result.append(float(item['value']))
    return result

def payback(initial, monthly):
    if initial < 0: raise ValueError('Investimento inválido.')
    balance=-initial
    if balance >= 0: return 0
    for i, cash in enumerate(monthly,1):
        balance += cash
        if balance >= 0: return i
    return None

def validate_offer(row):
    required=['operation_id','occupation','title','kind','city','schedule','source','published','collected']
    for field in required:
        if not str(row.get(field,'')).strip(): raise ValueError(f'Campo obrigatório: {field}')
    if row['kind'] not in ['Própria','Externa']: raise ValueError('Tipo deve ser Própria ou Externa.')
    for field in ['published','collected']: dt(row[field])
    if dt(row['published'])>dt(row['collected']): raise ValueError('Publicação posterior à coleta.')
    if row.get('salary') not in [None,'']:
        salary=float(row['salary'])
        if not math.isfinite(salary) or salary <= 0: raise ValueError('Salário deve ser positivo e finito.')
        row['salary']=salary
    else: row['salary']=None
    row.setdefault('benefits','Não informado'); row.setdefault('skills','Não informado')
    row.setdefault('unit','Mensal'); row.setdefault('link','CLT'); row.setdefault('cbo','Não informado')
    return row

def report(context, title='Síntese TRAMA'):
    lines=[f'# {title}', '', '**Ambiente demonstrativo • dados sintéticos**',f"Recorte: {context['scope']}", 'Método: relatório descritivo calculado; não gerado por IA.', '']
    for e in context['evidence']:
        lines += [f"## {e['id']} — {e['title']}", json.dumps(e['data'], ensure_ascii=False, indent=2),'']
    lines += ['## Limitações', 'Dados sintéticos; escutas voluntárias de conveniência; comparações descritivas não demonstram causalidade. Grupos pequenos são suprimidos.']
    return '\n'.join(lines)
