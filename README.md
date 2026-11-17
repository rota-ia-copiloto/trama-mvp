# TRAMA — Inteligência do Trabalho

Primeira versão funcional demonstrativa. Python + Streamlit, SQLite local e integração opcional com Gemini. Dados exclusivamente fictícios, da empresa Horizonte Serviços. Não representa implantação, parceria ou resultados da Manserv.

## Executar

Requer Python 3.11 ou superior. Extraia o ZIP e abra o terminal na pasta do projeto.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra o endereço exibido pelo Streamlit, normalmente http://localhost:8501. Em Windows, `iniciar_windows.bat` automatiza a instalação em ambiente virtual e a abertura. A instalação requer internet. Não precisa instalar Node.js para executar a aplicação.

## Os oito módulos

| Área | Implementação |
|---|---|
| Visão executiva | Métricas derivadas dos registros, coortes maduras/pendentes, origem e exportação Markdown |
| Radar ocupacional | Comparação por salário base/escala/benefícios, cadastro e extração de anúncio com revisão |
| Permanência | Campanhas, formulário sintético e leitura agregada por temas |
| Atratividade | Campanhas externas, barreiras e interesse declarado |
| Laboratório | Criação, edição, revisão humana, transições e exportação de intervenção |
| Valor econômico | Canais A–E opcionais, premissas, ROI, fluxo uniforme e payback |
| Copiloto | Contexto do recorte, referências, análise editável, rascunho de intervenção e exportação |
| Dados e configurações | CSV/XLSX, prévia, erros por linha, deduplicação, chave/modelo em sessão e auditoria |

Os filtros de operação, ocupação e período são compartilhados. Família e município derivam do recorte; empresa única. Cadastro inicial: três operações, três ocupações, 27 ofertas, 216 registros de vínculo, 126 eventos de recrutamento, 18 campanhas, 300 respostas e nove intervenções. Identificadores são gerados por instalação; conteúdo e datas são reproduzíveis.

## Ativar IA real

Em **Dados e configurações → IA generativa**, informe sua chave Gemini e o identificador de um modelo disponível em sua conta com suporte a JSON Schema. Marque a autorização de envio da base sintética e clique em **Aplicar configuração nesta sessão**. Não envie a chave no chat e não a coloque no código.

Alternativa: crie `.streamlit/secrets.toml`, usando `secrets.toml.example` como referência. Ou defina `GEMINI_API_KEY` e `GEMINI_MODEL` no ambiente. O modelo é configurável, sem nome obsoleto fixado no código.

As chamadas só ocorrem ao clicar. Capacidades implementadas:

- Extração de anúncio fictício para prévia revisável.
- Síntese de escutas agregadas.
- Recomendação de intervenção.
- Briefing e respostas contextuais do copiloto.

O adaptador usa Gemini REST `generateContent`, JSON Schema e validação Pydantic; referências: https://ai.google.dev/api/generate-content e https://ai.google.dev/gemini-api/docs/structured-output.

Saídas devem manter o recorte e referências válidas. Números não são aceitos na prosa gerada: o modelo referencia métricas e a aplicação exibe seus valores calculados. A validação de IDs não prova sustentação semântica; a revisão humana continua necessária. O copiloto não possui ferramentas de escrita, execução de comandos ou SQL.

**Sem chave/modelo**, navegação, importação, cadastros, cálculos, cenários, exportações e laboratório funcionam. Relatórios descritivos são identificados como determinísticos; existe um exemplo predefinido rotulado no copiloto. Respostas fixas não são apresentadas como IA ativa.

## Roteiro de cinco minutos

1. Na visão executiva, mantenha Campus Campinas / Auxiliar de limpeza e 365 dias. Abra as definições dos indicadores e as coortes.
2. Abra Radar ocupacional; compare salário, escala e benefícios. Consulte os metadados de uma oferta.
3. Consulte Permanência e Atratividade para observar temas distintos e a ressalva sobre amostra de conveniência.
4. No Copiloto, gere uma análise se houver IA configurada. Sem credencial, abra **Explorar exemplo demonstrativo sem IA** e carregue o exemplo rotulado.
5. Abra suas referências, edite e salve a síntese, e crie a intervenção em rascunho.
6. No Laboratório, defina responsável, autonomia, custos, linha de base, meta e comparação. Confirme revisão humana para salvar. Avance um estado por vez; aprovação exige campos essenciais preenchidos.
7. Em Valor econômico, preencha benefícios e custos; não some o mesmo efeito em canais diferentes. Exporte as premissas.
8. Exporte a síntese descritiva ou análise. Em Dados, veja a auditoria.
9. Para conferir proteção de grupos pequenos, selecione Centro Sorocaba / Auxiliar de produção. As escutas devem aparecer protegidas, inclusive no contexto do copiloto e no relatório.

## Dados e persistência

O banco é criado na primeira execução em `data/trama.sqlite`. `TRAMA_DB_PATH` permite definir outro caminho. Não incluímos banco com dados de teste no pacote. Os registros persistem ao atualizar/reabrir a aplicação quando o disco é durável. Em hospedagem efêmera, o disco pode ser perdido; a versão não afirma durabilidade em nuvem.

Dados brutos não são exportados pelo painel. Comentários livres ficam armazenados no formulário para demonstrar captura, mas **esta versão resume categorias estruturadas, sem análise semântica de textos livres**. Nenhum texto bruto das escutas é enviado ao modelo. Isso reduz exposição, mas limita a profundidade das sínteses.

O padrão de supressão é dez respostas por operação/ocupação/período. É um parâmetro demonstrativo, não garantia de anonimato ou requisito legal. Para uso real, projetar proteção contra ataques por diferenças entre períodos/recortes, unicidade de respondentes e política de retenção. Formulários locais não possuem tokens individuais, distribuição externa ou verificação de duplicidade de participação.

Importe apenas arquivos sintéticos, com até 5 MB e 2.000 linhas. O modelo CSV pode ser baixado na aplicação. Reimportação de linhas iguais é idempotente. Não há OCR, PDF/DOCX, scraping nem conexão com vagas reais.

## Testes

```bash
python -m pytest -q
```

Os testes cobrem cálculos, maturidade das coortes, sobreposição econômica, persistência, duplicidade, escopo, privacidade do contexto, validação de IA, falhas simuladas e navegação Streamlit pelos oito módulos, incluindo criação de rascunho pelo copiloto. `VERIFICACAO.md` registra o resultado desta entrega.

## Arquitetura

- `app.py`: navegação, filtros, formulários e apresentação.
- `trama/domain.py`: cálculos e validação de domínio.
- `trama/store.py`: esquema SQLite, consultas parametrizadas e auditoria.
- `trama/seed.py`: base sintética.
- `trama/context.py`: contexto único para interface, exportação e IA.
- `trama/ai.py`: contrato de saída, prompts, adaptador Gemini e validação.
- `tests/`: testes automatizados.

## Para um piloto real

Esta é uma instalação local de organização única, **sem autenticação**; perfis são demonstrativos. Não é ambiente seguro multiempresa. Não inserir informações reais pessoais, financeiras ou confidenciais. O armazenamento filtra pela organização fixa da demonstração, mas não substitui identidade e autorização por usuário.

Antes de piloto compartilhado: definir autenticação, permissões, banco durável e backups; implementar isolamento entre clientes; governança e uso autorizado de dados; segurança de escutas e tokens de participação; fontes reais licenciadas; orçamento e observabilidade da IA; critérios de teste e validação econômica. Não há integração com Manserv, ferramentas de RH ou mensageria.

O cenário econômico assume benefícios e custos operacionais uniformes em doze meses. Os efeitos monetários são premissas manuais; o sistema não atribui causalidade ou deduz economias automaticamente. Duplicidades de effect_id são bloqueadas, mas a distinção substantiva dos efeitos requer revisão.

## Publicação

Esta entrega não foi publicada. Para hospedar em Streamlit, escolha arquivo de entrada `app.py`, instale `requirements.txt` e configure segredos fora do repositório. O banco local exige volume durável para preservar registros. O prompt não autorizou publicação automática.
