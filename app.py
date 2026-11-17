import json, os, io, html
from datetime import timedelta, date
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from trama.store import Store
from trama.seed import seed, OCCS, THEMES
from trama.domain import AS_OF, STATES, safe_listening, report, economic, unique_benefits, payback, validate_offer, fingerprint, dt
from trama.context import build_context
from trama.ai import Gemini, AIError

st.set_page_config(page_title='TRAMA | Inteligência do Trabalho',page_icon='◈',layout='wide')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif}h1,h2,h3{font-family:Manrope,sans-serif!important;letter-spacing:-.7px}h1{font-weight:800!important;font-size:2.3rem!important}.block-container{padding-top:4rem;max-width:1500px}section[data-testid="stSidebar"]{background:#112e40;color:#e7f1f4}section[data-testid="stSidebar"] *{color:inherit}section[data-testid="stSidebar"] [data-baseweb="select"] *{color:#17394a!important}section[data-testid="stSidebar"] .stRadio label{padding:5px 0}section[data-testid="stSidebar"] input{color:#17394a!important}section[data-testid="stSidebar"] .stCaption{color:#a3bdc8}div[data-testid="stMetric"]{background:white;border:1px solid #e1e8ed;border-radius:14px;padding:20px}div[data-testid="stMetricValue"]{font-family:Manrope;font-weight:800;font-size:1.45rem}div[data-testid="stMetricLabel"]{font-size:12px;color:#607b8c}.hero{background:linear-gradient(110deg,#123448,#165063);color:#fff;padding:30px 34px;border-radius:18px;margin:8px 0 25px}.hero h2{color:white;margin:5px 0 10px;font-size:28px}.hero p{color:#c6dde4;max-width:800px;margin:0}.eyebrow{font-size:11px;letter-spacing:2px;font-weight:700;color:#5fc7b3}.tag{display:inline-block;padding:5px 11px;border-radius:25px;font-size:11px;background:#dff2ec;color:#147966;margin-right:8px}.scope{font-size:12px;color:#68818e;margin-bottom:15px}.insight{background:#fff;border:1px solid #e0e8ee;border-radius:13px;padding:20px;margin-bottom:12px}.insight b{color:#17485a}.insight p{color:#5b7685;font-size:14px;margin:10px 0 0}.stButton>button{border-radius:9px}div[data-testid="stExpander"]{background:#fff;border-radius:10px}.stTabs [data-baseweb="tab-list"]{gap:22px}.stTabs [aria-selected="true"]{color:#168878!important}footer{display:none}
</style>''',unsafe_allow_html=True)
store=Store(); seed(store)
PAGES=['Visão executiva','Radar ocupacional','Permanência','Atratividade','Laboratório de intervenções','Valor econômico','Copiloto TRAMA','Dados e configurações']

def go(page):st.session_state['nav']=page

def secret(name):
    try:return st.secrets.get(name,os.getenv(name,''))
    except Exception:return os.getenv(name,'')

def get_ai():return Gemini(st.session_state.get('stored_api_key') or secret('GEMINI_API_KEY'),st.session_state.get('stored_model') or secret('GEMINI_MODEL'))

def pct(value):return f'{value*100:.1f}%' if value is not None else 'Indisponível'
def money(value):return 'R$ '+f'{value:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def title(kicker,name,desc):
    st.markdown(f'<div class="eyebrow" style="color:#168878">{kicker}</div>',unsafe_allow_html=True);st.title(name);st.caption(desc)

def panel(label,text):st.markdown(f'<div class="insight"><b>{html.escape(label)}</b><p>{html.escape(text)}</p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## ◈ TRAMA')
    st.caption('INTELIGÊNCIA DO TRABALHO')
    st.divider()
    st.caption('ESPAÇO DE TRABALHO')
    st.markdown('**Horizonte Serviços**')
    st.caption('Empresa fictícia • demonstração local')
    page=st.radio('Navegação',PAGES,key='nav',label_visibility='collapsed')
    st.divider()
    st.selectbox('Perspectiva',['Direção','RH e atração','Operações','Inteligência'],key='profile')
    st.caption('Perfil demonstrativo. Não é autenticação.')
    st.markdown('🟢 **Dados sintéticos**')
    st.caption(('IA conectada • última geração válida' if st.session_state.get('ai_meta',{}).get('provider')=='Gemini' else 'IA configurada • ainda sem chamada') if get_ai().configured else 'IA generativa não configurada')
    st.caption('Os registros salvos ficam no SQLite desta instalação.')

ops=store.all('operation');op_by={o['name']:o for o in ops}
a,b,c=st.columns([1.35,1.3,1])
with a: op_name=st.selectbox('Operação / contrato',list(op_by),key='op')
op=op_by[op_name];opid=op['id']
with b: occ=st.selectbox('Ocupação',list(OCCS),key='occ')
with c: window=st.selectbox('Período',[90,180,365],format_func=lambda x:f'Últimos {x} dias',index=2,key='window')
end=AS_OF;start=end-timedelta(days=window-1)
st.markdown(f'<div class="scope">{html.escape(op["city"])} &nbsp; / &nbsp; {OCCS[occ]} &nbsp; / &nbsp; {start:%d/%m/%Y} — {end:%d/%m/%Y} &nbsp; · &nbsp; Base demonstrativa em {AS_OF:%d/%m/%Y}</div>',unsafe_allow_html=True)
ctx=build_context(store,opid,occ,start,end)
SCOPE=f'{opid}|{occ}|{window}'
if st.session_state.get('last_scope')!=SCOPE:
    for key in ['analysis','ai_meta','extraction','import_preview']:
        st.session_state.pop(key,None)
    st.session_state['last_scope']=SCOPE

# All evidence, including export/LLM, is assembled by the same server-side aggregation.
def evidence_browser():
    for e in ctx['evidence']:
        with st.expander(f"{e['title']} · {e['id']}"):
            st.json(e['data'])

def render_analysis(result,meta):
    st.caption('Rascunho de IA • requer revisão humana' if meta.get('provider')=='Gemini' else 'Exemplo demonstrativo predefinido • sem chamada de IA')
    st.subheader(result['title']);st.write(result['summary'])
    for o in result['observations']:
        st.write('**Observação:** '+o['text']);st.caption('Evidências: '+', '.join(o['evidence_ids']))
    for label,key in [('Hipóteses','hypotheses'),('Dados necessários','data_gaps'),('Limitações','limitations')]:
        with st.expander(label):
            for text in result[key]:st.write('• '+text)
    st.info(result['proposed_intervention']['action'])
    if result.get('metric_ids'):
        for ident in result['metric_ids']:
            names={'turnover':'Turnover voluntário','acceptance':'Aceitação de ofertas','fill':'Tempo de preenchimento','retention_90':'Permanência em 90 dias','retention_180':'Permanência em 180 dias'}
            metric=ctx['metrics'][ident]
            value=(f"{metric['value']:.1f} dias" if metric['value'] is not None else 'Indisponível') if ident=='fill' else pct(metric['value'])
            st.metric(names[ident],value)
            st.caption(f"Base de cálculo: {metric.get('n','inícios efetivos')} / {metric['d']} · registros sintéticos")
    with st.expander('Abrir evidências citadas'):
        refs=set(result['evidence_ids'])|{x for o in result['observations'] for x in o['evidence_ids']}
        for e in ctx['evidence']:
            if e['id'] in refs:st.markdown('**'+e['title']+'**');st.json(e['data'])

def ai_generate(task,question=''):
    ai=get_ai()
    if not ai.configured:st.warning('Configure a IA em Dados e configurações. O relatório descritivo continua disponível.');return
    if not st.session_state.get('allow_synthetic_ai',False):st.warning('Autorize o envio da base sintética em Dados e configurações.');return
    try:
        with st.spinner('Conectando as evidências do recorte…'):
            if task=='summary':result,meta=ai.summarize_listening(ctx)
            elif task=='intervention':result,meta=ai.recommend_intervention(ctx)
            else:result,meta=ai.answer_copilot(question,ctx)
        meta['evidence_ids']=[e['id'] for e in ctx['evidence']]
        st.session_state['analysis']=result;st.session_state['ai_meta']=meta
        store.add('ai_run',{'operation_id':opid,'occupation':occ,**meta})
    except Exception as exc:
        st.error(str(exc) if isinstance(exc,AIError) else 'A saída não passou na validação. Nenhum dado foi alterado; tente novamente.')

if page=='Visão executiva':
    st.markdown('<div class="hero"><div class="eyebrow">MERCADO · PESSOAS · DECISÕES</div><h2>Entenda a disputa. Transforme a decisão.</h2><p>Conecte as alternativas do mercado ao que as pessoas valorizam — e descubra quais mudanças vale a pena testar.</p></div>',unsafe_allow_html=True)
    m=ctx['evidence'][0]['data'];cols=st.columns(4)
    for col,label,value in zip(cols,['Turnover voluntário','Aceitação de ofertas','Tempo de preenchimento','Postos descobertos'],[pct(m['turnover']['value']),pct(m['acceptance']['value']),f"{m['fill']['value']:.1f} dias" if m['fill']['value'] is not None else 'Indisponível',str(m['open'])]):
        col.metric(label,value)
    st.caption('Calculado sobre registros sintéticos • abertura até início efetivo • postos sem início registrado no recorte')
    with st.expander('Como os indicadores foram calculados'):
        st.json(m);st.write('Turnover: saídas voluntárias / efetivo médio diário. Aceitação: aceitas / (aceitas + recusadas). Desistências e pendências são apresentadas separadamente.');st.caption(f"Pendências: {m['pending']} • desistências: {m['withdrawn']}")
    l,r=st.columns([1.5,1])
    with l:
        st.subheader('Onde investigar agora')
        panel('01 · Competitividade da oferta','Compare escala, salário base e benefícios separadamente. Alternativas próximas não comprovam concorrência real.')
        st.button('Explorar ofertas →',on_click=go,args=('Radar ocupacional',),width='stretch')
        panel('02 · Voz de quem está dentro e fora','Cruze as escutas com a oferta. Preferências declaradas ajudam a formular hipóteses; o teste mede o resultado.')
        st.button('Consultar escutas →',on_click=go,args=('Permanência',),width='stretch')
    with r:
        st.subheader('Permanência por coorte')
        for days in [90,180]:
            rr=m['retention'][days];st.metric(f'{days} dias',pct(rr['value']));st.caption(f"{rr['n']} vinculados / {rr['d']} com janela completa • {rr['pending']} aguardando maturação")
        st.button('Abrir laboratório →',on_click=go,args=('Laboratório de intervenções',),width='stretch')
    st.caption('Custo de substituição: indisponível na base. Requer levantamento de custos incrementais; use Valor econômico para cenários manuais.')
    st.subheader('Briefing da operação')
    st.download_button('Exportar relatório descritivo',report(ctx),file_name='TRAMA_Briefing.md',mime='text/markdown')
    if st.button('Gerar briefing com IA'):ai_generate('copilot','Prepare briefing executivo com hipóteses e próximos passos.')
    if st.session_state.get('analysis'):render_analysis(st.session_state['analysis'],st.session_state['ai_meta'])

elif page=='Radar ocupacional':
    title('MOTOR 01 · MERCADO','Quem disputa seus trabalhadores?','Compare condições concretas e investigue alternativas ocupacionais.')
    tabs=st.tabs(['Comparar ofertas','Cadastrar oferta','Extrair anúncio com IA'])
    offers=[e['data'] for e in ctx['evidence'] if e['title'].startswith('Oferta')]
    with tabs[0]:
        if offers:
            table=pd.DataFrame(offers)
            st.dataframe(table[['title','kind','salary','unit','schedule','hours','benefits','published']].rename(columns={'title':'Oferta','kind':'Tipo','salary':'Salário base (R$)','unit':'Unidade','schedule':'Escala','hours':'Horas/semana','benefits':'Benefícios','published':'Publicação'}),hide_index=True,width='stretch')
            st.caption('Salário não informado permanece vazio. Valores mensais brutos; benefícios não somados ao salário.')
            known=table.dropna(subset=['salary'])
            if not known.empty:
                fig=px.bar(known,x='title',y='salary',color='kind',color_discrete_map={'Própria':'#173d51','Externa':'#38a58f'},labels={'salary':'Salário base mensal (R$)','title':'Oferta','kind':'Tipo'})
                fig.update_layout(height=300,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(t=10,b=20))
                st.plotly_chart(fig,width='stretch')
            selected=st.selectbox('Abrir oferta',range(len(offers)),format_func=lambda i:offers[i]['title'])
            detail=offers[selected]
            d1,d2=st.columns(2)
            d1.markdown('**Condições da oferta**');d1.write(f"{detail.get('link','Não informado')} · escala {detail['schedule']} · {detail.get('hours','Não informado')} h/semana")
            d1.write('Benefícios: '+detail['benefits'])
            d2.markdown('**Competências e origem**');d2.write(detail['skills']);d2.caption(detail['source']);d2.caption('Coleta: '+detail['collected'])
            with st.expander('Metadados da oferta e referência'):st.json(detail)
        else:st.info('Nenhuma oferta publicada no período selecionado.')
        panel('Adjacência ocupacional • hipótese','Organização, segurança e trabalho em equipe são competências compartilhadas. A hipótese de concorrência com comércio e logística exige escuta e validação.')
        internal=next((e for e in ctx['evidence'] if e['id']=='escuta_interna'),None)
        if internal:st.caption('Há escuta agregada disponível, mas não há evidência suficiente para afirmar transição efetiva entre ocupações.')
    with tabs[1]:
        with st.form('new_offer'):
            name=st.text_input('Título da oferta');kind=st.selectbox('Tipo',['Própria','Externa']);salary_known=st.checkbox('Salário informado',value=True)
            salary=st.number_input('Salário base mensal bruto (R$)',min_value=1.,value=2000.)
            scale=st.text_input('Escala',value='5x2');hours=st.number_input('Horas semanais',min_value=1,max_value=60,value=44)
            benefits=st.text_input('Benefícios');skills=st.text_input('Competências / requisitos');source=st.text_input('Fonte',value='Cadastro sintético manual')
            published=st.date_input('Data de publicação',value=end,max_value=end);collected=st.date_input('Data de coleta',value=end,max_value=end)
            if st.form_submit_button('Revisar e salvar oferta sintética'):
                try:
                    row=validate_offer({'operation_id':opid,'occupation':occ,'title':name,'kind':kind,'salary':salary if salary_known else None,'city':op['city'],'schedule':scale,'hours':hours,'benefits':benefits,'skills':skills,'source':source,'published':published.isoformat(),'collected':collected.isoformat()})
                    store.add('offer',row,fingerprint=fingerprint(row));st.success('Oferta salva. Ela aparecerá no recorte após atualização.');st.rerun()
                except ValueError as exc:st.error(str(exc))
    with tabs[2]:
        ad=st.text_area('Cole um anúncio fictício para testar a extração',height=150)
        st.caption('Somente anúncios fictícios nesta demonstração. A extração exige revisão; nenhum cadastro é automático.')
        if st.button('Extrair campos com IA',disabled=not bool(ad)):
            if not get_ai().configured or not st.session_state.get('allow_synthetic_ai'):st.warning('Configure o provedor e autorize o envio sintético em Dados e configurações.')
            else:
                try:
                    result,meta=get_ai().extract_offer(ad);st.session_state['extraction']=result
                    store.add('ai_run',{'operation_id':opid,'occupation':occ,**meta,'task':'extract_offer'})
                except Exception as exc:st.error(str(exc) if isinstance(exc,AIError) else 'Extração inválida; revise o anúncio e tente novamente.')
        if st.session_state.get('extraction'):
            row=st.session_state['extraction'];st.caption('Prévia extraída • edite e confirme')
            with st.form('review_extracted'):
                name=st.text_input('Título revisado',value=row['title']);scale=st.text_input('Escala revisada',value=row.get('schedule') or '')
                salary=st.number_input('Salário extraído (zero significa não informado)',min_value=0.,value=float(row.get('salary') or 0))
                ben=st.text_input('Benefícios revisados',value=row.get('benefits') or 'Não informado');skills=st.text_input('Competências revisadas',value=row.get('skills') or 'Não informado')
                st.write('**Trecho literal:**');st.write(row['source_excerpt'])
                if st.form_submit_button('Confirmar e cadastrar como oferta externa sintética'):
                    try:
                        offer=validate_offer({'operation_id':opid,'occupation':occ,'title':name,'kind':'Externa','salary':salary or None,'city':op['city'],'schedule':scale,'source':'Anúncio sintético revisado','published':end.isoformat(),'collected':end.isoformat(),'benefits':ben,'skills':skills,'source_excerpt':row['source_excerpt']})
                        store.add('offer',offer,fingerprint=fingerprint(offer));st.success('Oferta confirmada e salva.')
                    except ValueError as exc:st.error(str(exc))

elif page in ['Permanência','Atratividade']:
    audience='Interna' if page=='Permanência' else 'Externa'
    title('MOTOR 02 · PERMANÊNCIA' if audience=='Interna' else 'MOTOR 03 · ATRATIVIDADE','O que faz permanecer?' if audience=='Interna' else 'Quem ainda não chega?','Escuta voluntária, agregada e conectada às decisões da operação.')
    tabs=st.tabs(['Leitura agregada','Campanhas','Responder pesquisa (demo)'])
    responses=[r for r in store.all('response',opid,occ) if r['audience']==audience]
    safe=safe_listening(responses,start,end)
    campaigns=[r for r in store.all('campaign',opid,occ) if r['audience']==audience]
    with tabs[0]:
        if safe['suppressed']:st.warning(safe['reason'])
        else:
            l,r=st.columns([1,2]);l.metric('Respostas no período',safe['n']);l.caption('Participações agregadas • base sintética')
            if audience=='Externa':l.metric('Interesse declarado',pct(safe['interested']/safe['n']));l.caption('Intenção não equivale a candidatura ou contratação.')
            with r:
                df=pd.DataFrame({'Tema':list(safe['themes']),'Respostas':list(safe['themes'].values())})
                fig=px.bar(df,x='Respostas',y='Tema',orientation='h',color_discrete_sequence=['#268d7e']);fig.update_layout(height=300,margin=dict(t=10,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)');st.plotly_chart(fig,width='stretch')
            st.info('Leitura descritiva: os temas acima são categorias declaradas nas respostas. Frequência não demonstra o efeito de uma mudança sobre permanência ou contratação.')
            st.caption('Canais: '+', '.join(safe['channels'])+' • amostra voluntária de conveniência')
        if st.button('Sintetizar escutas com IA',disabled=safe['suppressed']):ai_generate('summary')
        if st.session_state.get('analysis'):render_analysis(st.session_state['analysis'],st.session_state['ai_meta'])
    with tabs[1]:
        for campaign in campaigns:
            with st.expander(campaign['name']):
                st.write('Elegibilidade: '+campaign['criteria']);st.write('Canal: '+campaign['channel'])
                n=sum(r['campaign_id']==campaign['id'] for r in responses)
                if n>=10:st.write(f"Participações: {n} / público convidado: {campaign['eligible']}")
                else:st.caption('Participação protegida por grupo pequeno.')
                st.caption('Novas respostas neste formulário são simulações, sem verificação de unicidade de respondente.')
        with st.form('campaign'):
            name=st.text_input('Nome da nova campanha');eligible=st.number_input('Público convidado',min_value=10,value=30);criteria=st.text_input('Critérios de participação',value='Participação voluntária na demonstração');channel=st.selectbox('Canal de convite',['Presencial','Link interno','Parceiro territorial'])
            if st.form_submit_button('Criar campanha'):
                if not name.strip():st.error('Informe um nome.')
                else:store.add('campaign',{'operation_id':opid,'occupation':occ,'name':name,'audience':audience,'eligible':eligible,'criteria':criteria,'channel':channel,'date':end.isoformat()});st.rerun()
    with tabs[2]:
        st.info('Formulário de demonstração. Não insira dados pessoais. Respostas são registradas como sintéticas; não há envio externo automático.')
        if not campaigns:st.write('Crie uma campanha primeiro.')
        else:
            with st.form('response'):
                camp=st.selectbox('Campanha',campaigns,format_func=lambda x:x['name']);theme=st.selectbox('O que mais pesa hoje?',THEMES)
                text=st.text_area('Comentário fictício (opcional)');interested=st.checkbox('Tenho interesse nesta oferta (exemplo)');alt=st.selectbox('Alternativa considerada',['Comércio','Logística','Indústria','Serviços','Nenhuma declarada'])
                consent=st.checkbox('Entendo que este é um teste com resposta fictícia e participação voluntária.')
                if st.form_submit_button('Registrar resposta sintética'):
                    if not consent:st.error('Confirme a participação voluntária.')
                    else:store.add('response',{'operation_id':opid,'occupation':occ,'campaign_id':camp['id'],'audience':audience,'theme':theme,'date':end.isoformat(),'channel':camp['channel'],'interested':interested,'alternative':alt,'text':text[:2000],'synthetic':True});st.success('Resposta registrada; somente agregados elegíveis ficam visíveis.')

elif page=='Laboratório de intervenções':
    title('DA EVIDÊNCIA À AÇÃO','Teste uma mudança possível.','Rascunho → revisão humana → execução → avaliação. Todas as alterações são registradas.')
    interventions=store.all('intervention',opid,occ)
    a,b=st.columns([2,1]);a.caption(f'{len(interventions)} intervenções no recorte de operação e ocupação')
    if b.button('Nova intervenção'):
        store.add('intervention',{'operation_id':opid,'occupation':occ,'title':'Nova hipótese para revisão','problem':'','hypothesis':'','action':'','owner':'','cost':0,'autonomy':'','dependencies':'','metric':'Aceitação de ofertas','baseline':'','target':'','comparison':'','start':end.isoformat(),'end':(end+timedelta(days=30)).isoformat(),'state':'Rascunho','evidence_ids':[],'evaluation':''});st.rerun()
    for row in interventions:
        with st.expander(f"{row['state']} · {row['title']}",expanded=len(interventions)==1):
            with st.form('edit_'+row['id']):
                updated=dict(row)
                for key,label in [('title','Título'),('problem','Problema'),('hypothesis','Hipótese'),('action','Ação'),('owner','Responsável'),('autonomy','Autonomia'),('dependencies','Dependências do cliente'),('baseline','Linha de base'),('target','Meta e critério de decisão'),('comparison','Plano de comparação'),('evaluation','Avaliação / resultados observados')]:
                    updated[key]=st.text_area(label,value=str(row.get(key,'')),height=68) if key in ['action','evaluation','comparison'] else st.text_input(label,value=str(row.get(key,'')))
                updated['cost']=st.number_input('Custo incremental previsto (R$)',min_value=0.,value=float(row.get('cost',0)))
                updated['metric']=st.selectbox('Indicador primário',['Aceitação de ofertas','Turnover voluntário','Tempo de preenchimento','Permanência'],index=['Aceitação de ofertas','Turnover voluntário','Tempo de preenchimento','Permanência'].index(row.get('metric','Aceitação de ofertas')))
                available={e['id']:e['title'] for e in ctx['evidence']}
                updated['evidence_ids']=st.multiselect('Evidências deste recorte',list(available),default=[v for v in row.get('evidence_ids',[]) if v in available],format_func=lambda v:available[v])
                col1,col2=st.columns(2)
                updated['start']=col1.date_input('Início',value=dt(row['start'])).isoformat();updated['end']=col2.date_input('Fim previsto',value=dt(row['end'])).isoformat()
                current=STATES.index(row['state']);next_states=STATES[current:current+2]
                updated['state']=st.selectbox('Estado atual ou próximo estado',next_states)
                confirmed=st.checkbox('Revisei a alteração e confirmo o registro em meu perfil demonstrativo.')
                if st.form_submit_button('Salvar revisão humana'):
                    if not confirmed:st.error('Confirme a revisão.')
                    elif updated['end']<updated['start']:st.error('Fim anterior ao início.')
                    elif updated['state'] in STATES[2:] and not all(updated[x].strip() for x in ['action','owner','autonomy','baseline','target','comparison']):st.error('Antes de aprovar, preencha ação, responsável, autonomia, linha de base, meta e comparação.')
                    else:store.update('intervention',row['id'],updated,actor=st.session_state['profile']);st.success('Revisão salva com trilha de auditoria.')
            st.download_button('Exportar intervenção',json.dumps(row,ensure_ascii=False,indent=2),file_name='TRAMA_Intervencao.json',key='export_'+row['id'])
    st.caption('Resultados registrados são observações do teste. Um formulário preenchido não comprova efeito causal.')
    with st.expander('Métricas atuais para acompanhamento'):st.json(ctx['metrics'])

elif page=='Valor econômico':
    title('ECONOMIA VERIFICÁVEL','Quanto vale uma decisão melhor?','Simulação exploratória. Os valores abaixo são premissas editáveis, não resultados realizados.')
    st.info('Inclua apenas efeitos distintos. Capacidade, margem, vendas e licenciamento exigem evidência específica; não entram automaticamente no total.')
    default=pd.DataFrame([{'canal':'A · Custos evitáveis','effect_id':'reposicao','value':0.,'included':True},{'canal':'B · Capacidade produtiva','effect_id':'capacidade','value':0.,'included':False},{'canal':'C · Margem contratual','effect_id':'margem','value':0.,'included':False},{'canal':'D · Comercial','effect_id':'comercial','value':0.,'included':False},{'canal':'E · Licenciamento','effect_id':'licenca','value':0.,'included':False}])
    edited=st.data_editor(default,hide_index=True,width='stretch',disabled=['canal'],key='channels_'+SCOPE,column_config={'value':st.column_config.NumberColumn('Benefício incremental anual (R$)',min_value=0),'effect_id':'Identificador do efeito','included':'Incluir no cenário'})
    c1,c2,c3=st.columns(3);initial=c1.number_input('Investimento inicial (R$)',min_value=0.,value=0.);recurring=c2.number_input('Solução: custo mensal (R$)',min_value=0.,value=0.);intervention_cost=c3.number_input('Intervenções: custo anual (R$)',min_value=0.,value=0.)
    try:
        values=unique_benefits(edited.to_dict('records'));res=economic(values,[initial,recurring*12,intervention_cost])
        cols=st.columns(4)
        for col,label,value in zip(cols,['Benefício anual potencial','Custos no ano','Resultado potencial','ROI do cenário'],[money(res['benefit']),money(res['cost']),money(res['net']),pct(res['roi'])]):col.metric(label,value)
        monthly=res['benefit']/12-recurring-intervention_cost/12;pb=payback(initial,[monthly]*12)
        st.caption('Payback não aplicável: não há investimento inicial.' if initial==0 else (f'Payback: {pb} meses' if pb is not None else 'Payback não alcançado no horizonte de 12 meses.'))
        st.caption('Premissa de fluxo uniforme mensal; sem atraso de maturação. Valide a distribuição temporal no piloto. Identificadores duplicados bloqueiam a soma; efeitos diferentes com nomes distintos ainda exigem revisão de sobreposição.')
        scenario={'operation_id':opid,'occupation':occ,'period':'12 meses','channels':edited.to_dict('records'),'investment':initial,'monthly_cost':recurring,'intervention_cost':intervention_cost,'result':res,'payback':pb}
        if st.button('Salvar cenário exploratório'):store.add('scenario',scenario);st.success('Cenário salvo.')
        st.download_button('Exportar premissas e cálculo',json.dumps(scenario,ensure_ascii=False,indent=2),file_name='TRAMA_Cenario.json')
    except ValueError as exc:st.error(str(exc))
    with st.expander('Cenários salvos'):
        for row in store.all('scenario',opid,occ):st.json(row)

elif page=='Copiloto TRAMA':
    title('INTELIGÊNCIA CONTEXTUAL','Uma conversa com as evidências.','Investigue o recorte atual, formule hipóteses e prepare decisões para revisão.')
    if get_ai().configured:st.info('Provedor configurado. Uma resposta só será identificada como IA real após chamada bem-sucedida.')
    else:st.info('IA generativa não configurada. Você pode explorar evidências e gerar o relatório descritivo.')
    question=st.selectbox('Comece por uma pergunta',['Quais diferenças entre nossas ofertas e as alternativas merecem investigação?','O que as escutas sugerem sobre jornada e deslocamento?','Qual intervenção é viável neste contrato e como testá-la?','Que dados faltam para avaliar retorno?','Prepare um briefing para direção com evidências e próximos passos.'])
    custom=st.text_area('Ou escreva sua pergunta',height=90)
    a,b=st.columns(2)
    if a.button('Consultar com IA',type='primary'):ai_generate('copilot',custom or question)
    if b.button('Propor intervenção com IA'):ai_generate('intervention')
    with st.expander('Explorar exemplo demonstrativo sem IA'):
        st.caption('Texto predefinido para apresentar o fluxo; não é resultado de uma chamada de IA.')
        if st.button('Carregar exemplo rotulado'):
            refs=[ctx['evidence'][0]['id']]
            st.session_state['analysis']={'title':'Investigar clareza da oferta','scope':ctx['scope'],'summary':'O recorte permite formular uma hipótese sobre comunicação, mas exige validação operacional.','evidence_ids':refs,'observations':[{'text':'Há registros sintéticos de contratação e ofertas para comparação.','evidence_ids':refs}],'hypotheses':['A explicitação da escala e do acesso pode melhorar a compreensão da vaga.'],'data_gaps':['Validar a barreira com o público e verificar autonomia do contrato.'],'proposed_intervention':{'action':'Testar anúncio com condições reais mais claras, após revisão da operação.','dependencies':['Validação de RH e da gestão do contrato'],'cost_status':'não estimado','primary_metric_id':'acceptance','comparison_plan':'Comparar ofertas semelhantes e documentar mudanças concorrentes.'},'limitations':ctx['limitations'],'metric_ids':['acceptance'],'review_status':'draft'}
            st.session_state['ai_meta']={'provider':'Exemplo predefinido','status':'draft'}
    if st.session_state.get('analysis'):
        result=st.session_state['analysis'];meta=st.session_state['ai_meta'];render_analysis(result,meta)
        with st.form('save_analysis'):
            reviewed=st.text_area('Edite a síntese para revisão',value=result['summary'])
            confirm=st.checkbox('Revisei a síntese e as evidências; manter como rascunho.')
            if st.form_submit_button('Salvar análise revisada'):
                if not confirm:st.error('Confirme a revisão.')
                else:
                    result={**result,'summary':reviewed};st.session_state['analysis']=result
                    store.add('analysis',{'operation_id':opid,'occupation':occ,'result':result,'meta':meta,'reviewer':st.session_state['profile']});st.success('Análise salva como rascunho revisado.')
        if st.button('Criar intervenção em rascunho a partir desta análise'):
            action=result['proposed_intervention']
            store.add('intervention',{'operation_id':opid,'occupation':occ,'title':result['title'],'problem':result['summary'],'hypothesis':' '.join(result['hypotheses']),'action':action['action'],'owner':'','cost':0,'autonomy':'A validar','dependencies':'; '.join(action['dependencies']),'metric':{'acceptance':'Aceitação de ofertas','turnover':'Turnover voluntário','fill':'Tempo de preenchimento','retention_90':'Permanência','retention_180':'Permanência'}.get(action.get('primary_metric_id'),'Aceitação de ofertas'),'baseline':'A preencher','target':'A pactuar','comparison':action['comparison_plan'],'start':end.isoformat(),'end':(end+timedelta(days=30)).isoformat(),'state':'Rascunho','evidence_ids':result['evidence_ids'],'evaluation':''})
            st.success('Rascunho criado. Abra o laboratório para revisar e definir responsável, custo e meta.')
        st.download_button('Exportar análise e evidências',json.dumps({'analysis':result,'meta':meta,'evidence':ctx['evidence']},ensure_ascii=False,indent=2),file_name='TRAMA_Analise.json')
    st.download_button('Exportar relatório descritivo do recorte',report(ctx),file_name='TRAMA_Sintese.md')
    with st.expander('Evidências disponíveis neste recorte'):evidence_browser()
    with st.expander('Análises salvas'):
        for row in store.all('analysis',opid,occ):st.json(row)

elif page=='Dados e configurações':
    title('FONTES · MÉTODO · CONTROLE','Uma base em que você pode confiar.','Importação revisada, configuração da IA e transparência sobre a demonstração.')
    tabs=st.tabs(['Fontes e método','Importar ofertas','IA generativa','Auditoria'])
    with tabs[0]:
        panel('Base sintética reproduzível','Horizonte Serviços é uma empresa fictícia. A base é gerada em código, com data de referência fixa. Fontes e anúncios não representam vagas reais.')
        panel('Persistência desta instalação','Registros ficam em SQLite no diretório configurado por TRAMA_DB_PATH. A durabilidade depende do disco da instalação; em hospedagem efêmera o banco pode ser perdido.')
        panel('Limites de acesso','Versão local de organização única e sem autenticação. Os perfis são ilustrativos. Não use dados pessoais ou confidenciais; um piloto compartilhado exige identidade e autorização reais.')
        st.caption('Comentários abertos são armazenados apenas para demonstrar captura. A síntese desta versão usa categorias agregadas; não envia textos brutos ao modelo.')
        with st.expander('Fontes do recorte'):evidence_browser()
    with tabs[1]:
        st.info('Nesta versão, importe apenas ofertas sintéticas. CSV/XLSX; não há OCR ou leitura de PDF/DOCX.')
        sample={'operation_id':opid,'occupation':occ,'title':'Oferta de exemplo','kind':'Externa','city':op['city'],'salary':2100,'schedule':'5x2','source':'Exemplo sintético','published':end.isoformat(),'collected':end.isoformat(),'benefits':'Vale-transporte','skills':'Organização'}
        st.download_button('Baixar modelo CSV',pd.DataFrame([sample]).to_csv(index=False).encode('utf-8-sig'),file_name='TRAMA_Modelo_Ofertas.csv')
        upload=st.file_uploader('Arquivo de ofertas',type=['csv','xlsx'])
        if upload and upload.size>5*1024*1024:st.error('Limite: 5 MB.')
        elif upload:
            try:
                frame=pd.read_csv(upload) if upload.name.endswith('.csv') else pd.read_excel(upload)
                if len(frame)>2000:raise ValueError('Limite de 2.000 linhas por importação.')
                frame=frame.astype(object).where(pd.notna(frame),None)
                valid=[];errors=[]
                for idx,row in frame.iterrows():
                    try:
                        data={k:(v.isoformat()[:10] if hasattr(v,'isoformat') else v) for k,v in row.to_dict().items()}
                        if data.get('operation_id')!=opid or data.get('occupation')!=occ:raise ValueError('Linha fora do recorte ativo de operação/ocupação.')
                        valid.append(validate_offer(data))
                    except (ValueError,TypeError) as exc:errors.append({'linha':idx+2,'erro':str(exc)})
                st.dataframe(frame,hide_index=True);st.caption(f'{len(valid)} válidas • {len(errors)} com erro')
                if errors:st.dataframe(pd.DataFrame(errors),hide_index=True)
                confirmed=st.checkbox('Revisei a prévia e confirmo que estes são dados fictícios.')
                if st.button('Confirmar importação das linhas válidas',disabled=not confirmed or not valid):
                    before=len(store.all('offer',opid,occ))
                    for row in valid:store.add('offer',row,fingerprint=fingerprint(row))
                    added=len(store.all('offer',opid,occ))-before;st.success(f'{added} ofertas novas; {len(valid)-added} duplicadas ignoradas.')
            except Exception as exc:st.error(f'Não foi possível ler o arquivo: {exc}')
    with tabs[2]:
        with st.form('configure_ai'):
            api_key_input=st.text_input('Gemini API key (somente nesta sessão)',type='password',value=st.session_state.get('stored_api_key',''))
            model_input=st.text_input('Identificador do modelo disponível na sua conta',value=st.session_state.get('stored_model',''),help='Use um modelo com suporte a saída JSON estruturada. Também aceita GEMINI_MODEL no ambiente ou secrets.toml.')
            allow_input=st.checkbox('Autorizo enviar somente o contexto sintético necessário ao Gemini nesta demonstração.',value=st.session_state.get('allow_synthetic_ai',False))
            if st.form_submit_button('Aplicar configuração nesta sessão'):
                st.session_state['stored_api_key']=api_key_input
                st.session_state['stored_model']=model_input
                st.session_state['allow_synthetic_ai']=allow_input
                st.success('Configuração aplicada. Ela permanece ao navegar entre módulos, sem gravação em disco.')
        st.caption('Segredos não são gravados no SQLite ou nas exportações. Chamadas ocorrem apenas ao clicar em gerar. Consulte limites, custos e condições do seu provedor.')
        st.success('Configuração presente. A conexão será validada na primeira geração.') if get_ai().configured else st.warning('Informe chave e modelo ou configure-os no ambiente.')
        st.markdown('[Documentação oficial do Gemini](https://ai.google.dev/api/generate-content)')
        st.caption('Capacidades: extração de anúncio, síntese de escutas agregadas, recomendação de intervenção e copiloto. As saídas têm validação de esquema, escopo e referências; a sustentação semântica exige revisão humana.')
    with tabs[3]:
        rows=store.all('audit',opid)
        if rows:st.dataframe(pd.DataFrame(rows)[['date','actor','action','kind','record']],hide_index=True,width='stretch')
        else:st.info('A base inicial não gera eventos. Cadastros e revisões aparecerão aqui.')
        runs=store.all('ai_run',opid,occ)
        if runs:
            with st.expander('Execuções de IA (sem chave e sem texto bruto)'):
                for run in runs:st.json(run)

st.divider();st.caption('TRAMA · Inteligência do Trabalho | Demonstração com dados sintéticos · Decisões humanas, evidências rastreáveis.')
