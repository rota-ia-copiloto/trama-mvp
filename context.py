from .domain import workforce_metrics, safe_listening, dt

def build_context(store,op,occ,start,end):
    metrics=workforce_metrics(store.all('person',op,occ),store.all('hire',op,occ),start,end)
    evidence=[]
    evidence.append({'id':'metric_baseline','title':'Linha de base calculada','data':metrics})
    offers=[r for r in store.all('offer',op,occ) if start<=dt(r['published'])<=end]
    for o in offers:
        evidence.append({'id':o['id'],'title':f"Oferta {o['kind']} • {o['title']}",'data':{k:v for k,v in o.items() if k not in ['org']}})
    for audience in ['Interna','Externa']:
        rows=[r for r in store.all('response',op,occ) if r['audience']==audience]
        safe=safe_listening(rows,start,end)
        if not safe['suppressed']:evidence.append({'id':'escuta_'+audience.lower(),'title':f'Escuta {audience.lower()} agregada','data':safe})
    return {'scope':{'operation_id':op,'occupation':occ,'period':f'{start.isoformat()} / {end.isoformat()}'},'metrics':{'turnover':metrics['turnover'],'acceptance':metrics['acceptance'],'fill':metrics['fill'],'retention_90':metrics['retention'][90],'retention_180':metrics['retention'][180]},'evidence':evidence,'limitations':['Base exclusivamente sintética.','Proximidade ocupacional não prova concorrência real.','Escutas de conveniência; sem inferência causal.','Conteúdo de grupos pequenos não enviado ao provedor.']}
