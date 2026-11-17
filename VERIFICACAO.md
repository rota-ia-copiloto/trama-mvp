# Verificação — TRAMA 1.0

Data: 17/11/2026.

## Resultado

Sete testes automatizados aprovados (`python -m pytest -q`), incluindo a execução do aplicativo via Streamlit AppTest. Dependências fixadas nas versões usadas nesta verificação.

| Verificação | Resultado |
|---|---|
| Métricas, denominadores e coortes maduras/pendentes | Aprovada |
| ROI, payback, valores inválidos e efeito econômico duplicado | Aprovada |
| Supressão de escutas pequenas no contexto de análise/exportação | Aprovada |
| SQLite: persistência, reimportação idempotente e escopo fixo | Aprovada |
| Saída de IA: recorte, referências, indicadores e números em prosa | Aprovada |
| Credencial ausente, erro HTTP e resposta vazia | Aprovada com chamadas simuladas |
| Navegação pelos oito módulos e rascunho pelo copiloto | Aprovada no AppTest |
| Configuração de IA preservada ao trocar de página | Aprovada no AppTest |
| Interface em navegador | Inspeção visual de painel, radar, escutas, copiloto, laboratório e simulador |

Um aviso de depreciação do plugin anyio/pytest instalado no ambiente não afetou os testes.

## O que não foi validado

- Nenhuma chamada real ao Gemini: não havia credencial configurada.
- Nenhuma publicação ou infraestrutura multiusuário.
- Nenhum dado real, envio de pesquisa ou integração corporativa.
- O iniciador Windows foi revisado, mas não executado em Windows nesta sessão.
- Não há autenticação, isolamento multiempresa de produção ou controle de unicidade dos respondentes.
- A proteção de contexto foi testada diretamente; não é prova de anonimização contra ataques por diferença entre períodos.
- A validação de referências da IA verifica existência/escopo, não a sustentação semântica integral. Revisão humana é obrigatória.
- Conteúdos maliciosos foram testados quanto à separação de instrução/contexto e ausência de ferramentas. Isso não comprova resistência universal a prompt injection.

## Escopo funcional

Esta versão contempla os oito módulos e o fluxo de análise → revisão → intervenção. Síntese das escutas utiliza temas agregados; análise semântica dos comentários livres permanece fora desta versão. Novas ofertas são importadas por CSV/XLSX ou cadastradas manualmente. O comparativo ocupacional é exploratório, sem índice proprietário de atratividade ou inferência automática de mobilidade.
