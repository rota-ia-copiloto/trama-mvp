from datetime import timedelta
from .domain import AS_OF, fingerprint
OPS=[('op_campinas','Campus Campinas','Campinas / SP'),('op_paulinia','Complexo Paulínia','Paulínia / SP'),('op_sorocaba','Centro Sorocaba','Sorocaba / SP')]
OCCS={'Auxiliar de limpeza':'Facilities','Auxiliar de logística':'Logística','Auxiliar de produção':'Indústria'}
THEMES=['Deslocamento','Previsibilidade da escala','Remuneração','Benefícios','Desenvolvimento']

def seed(store):
    if store.all('operation'): return
    for oi,(op,name,city) in enumerate(OPS):
        store.add('operation',{'id':op,'operation_id':op,'name':name,'city':city},audit=False)
        for ci,occ in enumerate(OCCS):
            base=1800+ci*350+oi*60
            offers=[('Própria',base,'6x1','Operação Horizonte'),('Externa',base+80,'5x2','Alternativa Alpha'),('Externa',None if oi==2 else base+180,'12x36','Alternativa Beta')]
            for j,(kind,salary,schedule,title) in enumerate(offers):
                store.add('offer',{'operation_id':op,'occupation':occ,'title':title,'kind':kind,'salary':salary,'unit':'Mensal','schedule':schedule,'hours':44 if j!=2 else 36,'city':city,'benefits':'Vale-transporte; refeição no local' if j==0 else 'Vale-transporte; vale-alimentação','skills':'Organização; segurança; trabalho em equipe','source':'Base sintética TRAMA • geração reproduzível','published':(AS_OF-timedelta(days=15+j*5)).isoformat(),'collected':AS_OF.isoformat(),'link':'CLT','cbo':'Não informado'},audit=False)
            for i in range(24):
                start=AS_OF-timedelta(days=20+i*15)
                end=start+timedelta(days=55+i) if i%6==0 else None
                if end and end>AS_OF: end=None
                store.add('person',{'operation_id':op,'occupation':occ,'start':start.isoformat(),'end':end.isoformat() if end else None,'voluntary':i%2==0},audit=False)
            for i in range(14):
                opened=AS_OF-timedelta(days=5+i*9)
                status=['Aceita','Aceita','Recusada','Pendente','Desistência'][i%5]
                filled=(opened+timedelta(days=8+i%7)) if status=='Aceita' else None
                if filled and filled>AS_OF: filled=None
                store.add('hire',{'operation_id':op,'occupation':occ,'opened':opened.isoformat(),'status':status,'filled':filled.isoformat() if filled else None},audit=False)
            for kind in ['Interna','Externa']:
                n=6 if oi==2 and ci==2 else 18
                camp=store.add('campaign',{'operation_id':op,'occupation':occ,'name':f'{kind} • ciclo novembro','audience':kind,'eligible':30,'channel':'Convite voluntário presencial','criteria':'Interesse em ocupação operacional; participação voluntária','date':AS_OF.isoformat()},audit=False)
                for i in range(n):
                    theme=THEMES[(i+ci)%5] if i>8 else THEMES[oi%3]
                    store.add('response',{'operation_id':op,'occupation':occ,'campaign_id':camp,'audience':kind,'theme':theme,'date':(AS_OF-timedelta(days=i%20)).isoformat(),'channel':'Convite voluntário presencial','interested':i%3!=0,'alternative':'Logística' if ci==0 else 'Comércio','text':f'Exemplo sintético sobre {theme.lower()}.','synthetic':True},audit=False)
            store.add('intervention',{'operation_id':op,'occupation':occ,'title':'Revisar comunicação de escala e acesso','problem':'Compreender barreiras de atração','hypothesis':'Maior clareza pode apoiar candidaturas qualificadas','action':'Testar anúncio com escala e acesso explícitos','owner':'Equipe de RH • demo','cost':0,'autonomy':'Revisão de comunicação interna','dependencies':'Validação com gestão do contrato','metric':'Aceitação de ofertas','baseline':'A definir após linha de base','target':'Pactuar antes do teste','comparison':'Comparar com oferta anterior; sem inferência causal','start':AS_OF.isoformat(),'end':(AS_OF+timedelta(days=30)).isoformat(),'state':'Rascunho','evidence_ids':[],'evaluation':'Ainda não iniciada'},audit=False)
