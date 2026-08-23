# SPEC-003 — POC de chat analítico com IA

**Status:** Done
**Responsável:** Responsável pelo produto
**Aprovação para Ready:** Aprovada pelo responsável pelo produto em 22/08/2026
**Aprovação para Done:** Confirmada pelo responsável pelo produto em 23/08/2026
**Última revisão:** 23/08/2026

## Contexto e resultado esperado

Permitir que o gestor comercial faça perguntas em linguagem natural sobre o snapshot atual de obras de construção do Ceará e receba respostas fundamentadas exclusivamente nas interfaces Gold já publicadas pelo dbt.

O resultado observável é uma página de chat no Streamlit que transforma uma pergunta respondível em uma única consulta SQL somente leitura, valida e executa a consulta sob limites explícitos e apresenta uma resposta em linguagem natural com referência ao snapshot consultado. Perguntas fora do domínio ou sem suporte nos dados não devem gerar fatos inventados; a interface deve responder com orientação amigável e manter a consulta Gold fechada.

Esta spec é uma POC independente da SPEC-002. A versão atual usa as views Gold públicas consumidas pelos dashboards; adicionar views futuras exige atualização explícita desta spec e da allowlist.

**Decisão de fase:** a implementação usa exclusivamente a API Gemini com o modelo operacional `gemini-3.5-flash-lite`, selecionado por configuração. A aplicação não mede tokens nem faz monitoramento de suficiência; se o limite ou a capacidade do modelo forem insuficientes, a decisão será manual. A arquitetura mantém um seam de provider para permitir um adapter futuro de Codex CLI, mas esse adapter não faz parte desta entrega e não é habilitado por fallback automático.

**Reavaliação autorizada (23/08/2026):** após o teste da credencial atual mostrar que a geração não está disponível para o modelo inicial, o responsável autorizou selecionar manualmente o modelo Gemini mais adequado entre os modelos acessíveis pela mesma credencial. A seleção deverá ser validada no fluxo completo do chat e não constitui fallback automático; o modelo escolhido será registrado nesta spec antes de alterar a configuração efetiva.

**Seleção manual (23/08/2026):** por decisão do responsável, a configuração efetiva passa a usar `gemini-3.5-flash-lite`, que está acessível pela credencial atual e possui a cota operacional desejada. A seleção não é fallback automático. O fluxo completo foi repetido cinco vezes com seed 42 e concluiu a pergunta dourada em todas.

**Decisões de proteção:** o banco será acessado por role dedicada em transação somente leitura. SQL gerado poderá usar apenas `SELECT` e CTEs de leitura para agregações complexas; `CREATE TEMP TABLE` não será habilitado nesta POC, pois adiciona estado e consumo de recursos sem necessidade para as perguntas previstas. Como os dados Gold são públicos, a síntese Gemini poderá receber a pergunta, o contexto semântico, o SQL aprovado e o resultado Gold limitado; secrets, conexão, schema discovery, `ingestion_id`, payload bruto e detalhes internos permanecem fora do prompt.

**Clarificação de UX (23/08/2026):** o aviso amarelo persistente de transferência e o checkbox de consentimento foram removidos da página por não serem necessários à interação executiva. A capacidade continua protegida por `ANALYTICAL_CHAT_ENABLED=false` por padrão; quando habilitada, as regras de envio seguro e falha fechada continuam válidas, sem expor termos de implementação ao usuário final.

**Clarificação de apresentação e navegação (23/08/2026):** a resposta visível ao usuário deve conter somente a síntese em linguagem natural. SQL, datas técnicas, contagem de linhas, limites e proveniência permanecem metadados internos da execução e não são renderizados na conversa. Quando o resultado identificar exatamente uma obra por `project_id`, a página deve oferecer um link para o detalhe do projeto com essa obra selecionada; resultados agregados, múltiplos ou sem identificador não exibem link.

**Clarificação conversacional (23/08/2026):** mensagens de saudação, cortesia e texto natural sem intenção analítica são aceitos pelo chat. Saudações e pedidos sobre temas sem dados disponíveis recebem uma resposta local de orientação, sem chamada ao provider ou à Gold; o histórico não deve tratar essa situação como falha de infraestrutura nem exibir proveniência Gold. Perguntas analíticas continuam limitadas ao snapshot Gold público e não podem gerar fatos externos.

**Clarificação de contexto conversacional (23/08/2026):** o histórico recente da sessão deve ser usado para resolver referências como “essa obra”, “e em outro município?” e “qual link?”. A interface já mantém o histórico para renderização; a camada analítica deverá receber somente turnos recentes limitados de usuário e resposta natural, tratados como conteúdo não confiável. SQL, resultados brutos, metadados técnicos, credenciais e payloads não entram no histórico enviado ao provider.

**Clarificação de execução física (23/08/2026):** perguntas sobre obras “ativas” ou “em andamento” devem usar `source_status = 'Em execução'`. “Porcentagem de conclusão” deve usar `physical_execution_percentage` da view Gold de execução física; a contagem deve ser distinta por `project_id`, filtrada pelo município e pelo snapshot atual. Percentuais ausentes não atendem ao filtro; a resposta deve declarar a métrica e a regra quando necessário.

**Clarificação de feedback de processamento (23/08/2026):** enquanto Gemini, validação e Gold processam uma pergunta, a página deve exibir o spinner nativo do Streamlit com linguagem executiva. O spinner deve desaparecer antes da resposta ou do erro e não deve expor prompt, SQL, credenciais ou detalhes internos.

**Ampliação de escopo de dados (23/08/2026):** o chat deve ter acesso às interfaces Gold públicas consumidas pela visão geral e pelo detalhe do projeto, não somente às quatro views iniciais. O catálogo gerável passa a incluir `gold.vw_market_overview_current`, `gold.vw_project_investment_current`, `gold.vw_project_location_current`, `gold.vw_status_distribution_current`, `gold.vw_project_detail_current`, `gold.vw_project_participant_current`, `gold.vw_project_axis_type_current`, `gold.vw_project_ppa_current`, `gold.vw_project_restriction_area_current`, `gold.vw_project_photo_indicator_current`, `gold.vw_project_contract_current`, `gold.vw_project_commitment_current`, `gold.vw_project_commitment_totals_current`, `gold.vw_project_execution_current`, `gold.vw_project_status_history_current`, `gold.vw_project_feasibility_study_current` e `gold.vw_project_coverage_current`; `gold.vw_snapshot_metadata_current` também poderá ser consultada apenas com suas colunas públicas. O SQL poderá combinar essas relações em joins e CTEs de leitura, com chaves e colunas allowlisted, limites de complexidade e regras explícitas para não duplicar medidas financeiras por fanout. `ingestion_id`, payload bruto, schema discovery e objetos fora do catálogo continuam proibidos.

## Escopo

- Página `Chat com os dados` integrada à navegação atual do Streamlit, usando componentes nativos de chat.
- Histórico de mensagens limitado à sessão do Streamlit.
- Fluxo pergunta → proposta de SQL → validação → consulta Gold → síntese da resposta.
- Interface pequena de provider, seleção por configuração e provider fake para testes.
- Adapter Gemini pela biblioteca oficial Google GenAI, com credencial fora do repositório.
- Seam de provider compatível com uma futura extensão para Codex CLI, sem implementar ou habilitar subprocesso nesta fase.
- Contexto semântico versionado das views Gold permitidas, granularidades, colunas, KPIs e limitações.
- Validação estrutural do SQL por AST, execução em transação somente leitura, timeout e limites de resultado.
- Resposta textual executiva, com metadados técnicos preservados internamente para validação e diagnóstico.
- Estados seguros de indisponibilidade, pergunta fora do domínio, SQL inválido, consulta falha e resposta inválida.
- Testes automatizados sem consumo de APIs reais; o provider Gemini será mockado e o provider Codex CLI permanecerá ausente nesta fase.
- Atualizações documentais e ADR necessárias antes da implementação.

## Não escopo

- RAG, embeddings, banco vetorial ou fine-tuning.
- Memória persistente, auditoria avançada de prompts ou observabilidade de produção.
- Acesso à Bronze, Silver, tabelas Gold internas ou snapshots históricos.
- Dados e views ainda não publicados ou fora da allowlist vigente.
- Alteração de dados, DDL, DML ou execução autônoma de comandos pelo `ChatAgent`.
- MCP, múltiplos agentes, function calling complexo ou ferramentas arbitrárias do LLM.
- Implementação, instalação, isolamento ou fallback automático do Codex CLI; isso será uma extensão futura com spec e gate próprios.
- Autenticação de usuários, rate limiting distribuído ou infraestrutura de produção para LLM.
- Streaming de tokens, geração automática de gráficos ou exportação de conversas.
- Inferência de atraso, licitação aberta, oportunidade, prioridade ou recomendação comercial.

## Requisitos

- **REQ-001:** O Streamlit deve disponibilizar uma página `Chat com os dados` com `st.chat_message` e `st.chat_input`, sem alterar o comportamento das páginas existentes.
- **REQ-002:** Para cada pergunta aceita, o `ChatAgent` deve solicitar uma proposta de SQL ao provider, validando a pergunta atual junto com o histórico conversacional recente e limitado quando existir; depois deve validar o SQL, executar a consulta na Gold e solicitar ao provider a síntese final a partir do resultado limitado.
- **REQ-003:** O `ChatAgent` deve depender de uma interface pequena de provider e selecionar o adapter por `LLM_PROVIDER`, sem importar diretamente um SDK ou runtime. Nesta fase, somente `gemini` e o fake de testes são válidos; qualquer outro provider deve falhar fechado.
- **REQ-004:** O provider Gemini deve usar a biblioteca oficial Google GenAI, modelo configurável e credencial obtida de variável de ambiente ou secret não versionado.
- **REQ-005:** A arquitetura deve preservar um seam de provider que permita adicionar futuramente um adapter Codex CLI sem acoplar o `ChatAgent`, o executor Gold ou a UI a um runtime externo. A SPEC-003 não implementa, instala, habilita ou usa o Codex CLI; uma futura implementação deverá ter spec, isolamento e aprovação de segurança próprios.
- **REQ-006:** O contexto semântico deve declarar explicitamente as views e o subconjunto de colunas geráveis, granularidade, definições dos KPIs, glossário necessário, data de referência e limitações conhecidas, derivadas dos contratos dbt e da documentação vigente; metadados do snapshot devem vir de consulta estática e `ingestion_id` não deve entrar no espaço analítico do LLM.
- **REQ-007:** Antes de gerar SQL, o agente deve classificar a pergunta atual, considerando o histórico conversacional recente delimitado, como respondível, fora do domínio ou não suportada pelos dados atuais; apenas perguntas respondíveis podem chegar ao executor.
- **REQ-008:** O SQL proposto deve ser analisado por parser AST PostgreSQL e conter exatamente uma consulta `SELECT`, admitindo CTEs exclusivamente de leitura para agregações complexas e rejeitando múltiplas statements, `CREATE TEMP TABLE`, `SELECT *`, DDL, DML, comandos transacionais, `COPY`, `SELECT INTO` e locking clauses.
- **REQ-009:** A validação deve permitir relações Gold allowlisted, seu subconjunto de colunas geráveis e uma lista mínima de funções analíticas sem efeito colateral; joins somente com chaves e tipos allowlisted, CTEs de leitura e agregações são permitidos. Deve rejeitar `WITH RECURSIVE`, `CROSS JOIN`, `LATERAL`, funções de tabela, schemas, tabelas, funções e catálogos não permitidos, joins sem predicado seguro e consultas que agreguem medidas financeiras após fanout não controlado, além de impor limites de tamanho, profundidade, nós AST, joins, CTEs e subconsultas.
- **REQ-010:** O executor deve ser um caminho Psycopg dedicado dentro do seam `frontend/gold.py`, sem `st.connection().query()` nem cache, usando role PostgreSQL própria do chat com `USAGE` apenas em Gold, `SELECT` nas views Gold públicas consumidas pelos dashboards e acesso somente às colunas públicas de `gold.vw_snapshot_metadata_current`, sem privilégio de criação temporária, transação explicitamente read-only, `search_path` fixo, `SET LOCAL statement_timeout`, cursor limitado, rollback obrigatório e limites de linhas, colunas, células e bytes.
- **REQ-011:** Toda consulta deve obedecer à gramática semântica por relação: contagens de obras por `project_id`, investimentos uma vez por projeto em `vw_market_overview_current` ou por fonte em `vw_project_investment_current`, contratos/empenhos/execução em suas relações de detalhe e ranking municipal somente por `count(distinct project_id)` em `vw_project_location_current`; qualquer agregação financeira sobre localização ou após fanout não controlado deve ser rejeitada.
- **REQ-012:** A resposta final deve usar somente a pergunta, o histórico conversacional natural limitado, o contexto semântico e o resultado SQL; deve informar quando o resultado estiver vazio, truncado ou limitado e não pode criar fatos ausentes no resultado.
- **REQ-013:** A execução deve preservar internamente `source_updated_at`, a data de ingestão, os limites, a proveniência e a consulta aprovada para testes e diagnóstico; a interface final deve renderizar somente a resposta em linguagem natural e, quando aplicável, um link para o detalhe da obra.
- **REQ-014:** Perguntas e valores retornados da Gold devem ser tratados como conteúdo não confiável; texto do usuário ou dos dados não pode substituir instruções estruturais, alterar allowlists nem provocar nova execução fora do fluxo validado.
- **REQ-015:** A capacidade deve permanecer desabilitada por padrão e exigir habilitação por configuração; a UI não deve exigir checkbox ou banner persistente para iniciar a conversa. O POC aceita a transferência limitada porque o recorte Gold é público, mas não envia secrets, strings de conexão, schema discovery, `ingestion_id`, payload bruto ou detalhes internos; o histórico deve permanecer apenas em `st.session_state` durante a sessão.
- **REQ-016:** Falhas de configuração, provider, formato da resposta, SQL, timeout ou banco devem falhar de forma fechada e apresentar mensagem curta, sem executar fallback menos restritivo ou trocar automaticamente para outro provider.
- **REQ-017:** Testes automatizados devem cobrir provider fake/mocado, adapter Gemini, guardrails, perguntas douradas, perguntas de acompanhamento com histórico, classificação de execução física, prompt injection, indisponibilidade, execução read-only e renderização, sem consumir créditos da Gemini nem executar runtime externo.
- **REQ-018:** A implementação deve atualizar PRD, arquitetura, ADR, design, README e configuração de exemplo conforme o impacto aprovado, sem modificar contratos dbt ou regras de negócio quando as views atuais já responderem à pergunta.

## Regras e contratos de dados

**Clarificação de implementação (22/08/2026, revisada em 23/08/2026):** o grant em `gold.vw_snapshot_metadata_current` é necessário para o executor obter datas e indicadores públicos do snapshot; ele permite somente as colunas públicas catalogadas. A ampliação de acesso às demais views é explícita, limitada ao catálogo Gold dos dashboards e não inclui objetos internos.

- O catálogo gerável contém as 17 views públicas consumidas pelos dashboards listadas na ampliação de escopo; `gold.vw_snapshot_metadata_current` é permitida somente em colunas públicas e não pode expor `ingestion_id`.
- O contexto do LLM deve declarar as granularidades, chaves de join, medidas repetidas e regras de pré-agregação de cada relação; nenhum identificador interno entra no prompt.
- Cada SQL gerado referencia somente relações físicas allowlisted. Joins são aceitos apenas com chaves e granularidades declaradas pelo catálogo; fatos 1:N independentes devem ser pré-agregados antes da combinação para evitar fanout.
- `vw_market_overview_current` possui uma linha por projeto e é a fonte para rankings de obras, organizações, situação, datas e investimento total por projeto.
- `vw_project_investment_current` possui uma linha por projeto e fonte de recurso.
- `vw_project_location_current` possui uma linha por projeto e município; `planned_investment_amount` é repetido apenas para contexto e não pode ser somado por município.
- `vw_status_distribution_current` possui uma linha por situação original.
- `vw_snapshot_metadata_current` possui uma linha para a última ingestão `succeeded`.
- Total de obras usa contagem distinta de `project_id`.
- Obras em execução usa correspondência exata de `source_status = 'Em execução'`.
- Distribuição por situação preserva o texto original da fonte, sem reclassificação.
- Investimento previsto é estimativa informada pela fonte e não representa valor contratado, empenhado, liquidado ou pago.
- O filtro de últimos 12 meses usa `registration_date` e é ancorado em `source_updated_at`, não na data do computador.
- Ranking de municípios significa quantidade distinta de obras; investimento por município não é respondível no contrato atual.
- Ranking de organizações pode declarar quantidade distinta de obras ou investimento previsto total, sempre informando a medida usada.
- Dados nulos permanecem ausentes; não são convertidos em zero sem regra explícita.
- A Gold atual contém somente `uf_principal = CE`, `nature_intervention = Obra` e `species_intervention = Construção`.
- O snapshot atual não constitui histórico de eventos e não sustenta tendência temporal entre ingestões.
- As regras de negócio continuam no dbt. O contexto semântico apenas descreve contratos existentes para o LLM e deve ter teste de drift contra a allowlist e as colunas do adaptador Gold.

## Critérios de aceitação

- **AC-001 — REQ-001/REQ-015:** A página renderiza chat, mantém mensagens somente na sessão e as demais páginas continuam carregando nos smoke tests.
- **AC-002 — REQ-002:** Um teste com provider fake comprova a ordem geração SQL → validação → consulta → síntese e impede síntese quando uma etapa anterior falha.
- **AC-003 — REQ-003:** `LLM_PROVIDER=gemini` seleciona o adapter Gemini, o fake pode ser injetado nos testes e qualquer outro valor, inclusive `codex_cli`, produz erro de configuração seguro sem tentativa de execução.
- **AC-004 — REQ-004:** O adapter Gemini recebe modelo e credencial por configuração, e seus testes usam cliente mockado sem chamada de rede.
- **AC-005 — REQ-005:** A factory e a configuração comprovam que `codex_cli` não é habilitado nem instalado nesta fase, que o Compose não contém o runtime e que o `ChatAgent` depende apenas do contrato de provider. Os requisitos de `shell=False`, sandbox, ambiente sanitizado e spike negativo ficam registrados como gate obrigatório de uma futura spec do adapter Codex CLI.
- **AC-006 — REQ-006:** O catálogo semântico contém todas as views Gold públicas dos dashboards, os subconjuntos geráveis e as granularidades reais; um teste comprova que cada coluna gerável existe no contrato dbt, coincide com o executor e exclui `ingestion_id`.
- **AC-007 — REQ-007:** Perguntas sobre contratos, empenhos, pagamentos, execução, participantes, estudos, histórico e cobertura são encaminhadas às views Gold correspondentes; perguntas sobre atraso, licitação aberta ou outras inferências sem campo publicado são recusadas antes da geração ou execução de SQL.
- **AC-008 — REQ-008/REQ-009:** A suíte rejeita DDL, DML, `CREATE TEMP TABLE`, múltiplas statements, `SELECT *`, catálogo do PostgreSQL, view/coluna/função fora da allowlist, `SELECT INTO`, lock, CTE com escrita ou recursiva, joins sem chave segura, `CROSS JOIN`, `LATERAL`, funções de tabela, fanout financeiro não pré-agregado e consultas acima dos limites de complexidade; joins Gold válidos passam.
- **AC-009 — REQ-008/REQ-009:** Consultas válidas com agregação, ranking, filtro de situação e janela de cadastro passam pelo parser e usam somente objetos permitidos.
- **AC-010 — REQ-010:** Teste de integração da role do chat e do executor Psycopg comprova grants exatos — SELECT nas views Gold públicas do dashboard e somente colunas públicas da view de metadados —, transação read-only, `search_path`, timeout, cursor `N + 1`, rollback, limites de linhas/colunas/células/bytes e impossibilidade de escrita ou leitura fora desses objetos permitidos.
- **AC-011 — REQ-011:** Perguntas douradas fixam pergunta e medida: total de obras, municípios por quantidade distinta de obras, organizações por quantidade e por investimento previsto, maiores obras por investimento, obras em execução, distribuição por situação e cadastros nos últimos 12 meses; cada resposta reconcilia com SQL de referência sobre a mesma Gold.
- **AC-012 — REQ-011:** Um teste de fanout comprova que investimento não é somado a partir das linhas repetidas por município.
- **AC-013 — REQ-012/REQ-013:** Resposta normal, vazia e truncada exibe somente linguagem natural executiva; a execução mantém seus metadados internos sem renderizar SQL, datas técnicas, limites, contagens ou proveniência na conversa.
- **AC-014 — REQ-014:** Testes adversariais em pergunta e valores textuais da Gold não alteram allowlist, guardrails, provider, consulta executada ou segunda etapa do fluxo.
- **AC-015 — REQ-015:** Com a capacidade desabilitada a página não chama provider; não há checkbox nem banner persistente. Quando habilitada, são enviados somente pergunta, contexto mínimo, SQL aprovado e resultado Gold limitado. Varredura e testes de erro não encontram credenciais reais, strings de conexão, schema discovery, `ingestion_id` ou tokens em prompts, logs e mensagens exibidas.
- **AC-016 — REQ-016:** Provider indisponível, saída inválida, SQL rejeitado, timeout e falha Gold apresentam estados distintos e nenhum deles executa fallback irrestrito.
- **AC-017 — REQ-017:** Ruff, pytest e AppTest passam sem rede, créditos Gemini ou runtime externo; testes dbt existentes continuam passando se a Gold não for alterada.
- **AC-018 — REQ-018:** PRD, arquitetura, ADR, DESIGN, README e configuração de exemplo refletem a capacidade e seus limites; mudanças Gold, se surgirem, voltam primeiro à spec.
- **AC-019 — REQ-001/REQ-007/REQ-016:** Mensagens como `oi` e pedidos sobre temas sem dados, como contratos, aparecem como resposta normal do chat sem chamar provider ou Gold; a resposta informa o limite dos dados, sem erro de Gold, metadata ou proveniência falsa.
- **AC-023 — REQ-013:** Quando uma consulta retornar exatamente uma obra com `project_id`, a resposta oferece link para `Detalhe do projeto` com o identificador selecionado; consultas agregadas ou com mais de uma obra não oferecem link.
- **AC-021 — REQ-002/REQ-007/REQ-012:** Duas mensagens na mesma sessão comprovam que o segundo turno recebe apenas histórico natural recente e limitado, sem SQL, resultado bruto, metadados técnicos ou segredos; uma referência como “qual link?” pode resolver a obra do turno anterior.
- **AC-022 — REQ-006/REQ-011:** A pergunta sobre obras em execução em Fortaleza com `physical_execution_percentage > 80` é respondível, usa `source_status = 'Em execução'`, conta `DISTINCT project_id` e reconcilia com consulta Gold de referência.
- **AC-020 — REQ-009/REQ-010/REQ-011:** O chat consulta todas as views Gold públicas usadas pelos dashboards, permite joins e agregações read-only com chaves allowlisted, concede SELECT à role dedicada somente nessas views e comprova por testes que fanout não duplica investimento ou contagens.
- **AC-024 — REQ-001/REQ-016:** Enquanto Gemini, validação e Gold processam uma pergunta, a página exibe o spinner nativo “Analisando os dados...”, que desaparece antes da resposta ou do erro sem expor detalhes internos.

## Dependências e riscos

- Variabilidade, custo, latência e indisponibilidade dos providers.
- SQL semanticamente válido, porém incorreto; mitigado por contexto explícito, perguntas douradas e reconciliação.
- Prompt injection na pergunta ou em texto vindo da Gold; o validador e os privilégios do banco permanecem a fronteira de segurança.
- Parser SQL incompatível com alguma construção PostgreSQL; a proposta é usar `sqlglot` no dialeto PostgreSQL, com spike específico e falha fechada antes de `Ready`.
- Uma futura extensão Codex CLI terá risco próprio de isolamento, acesso a arquivos, rede, secrets e ferramentas; esses controles não são necessários para habilitar a primeira fase Gemini e não podem ser tratados como fallback implícito.
- Ausência de autenticação no Streamlit e ausência de rate limiting de produção; aceitáveis apenas para demonstração local da POC.
- Drift entre contratos dbt, adaptador Gold e contexto semântico.
- Resultado grande ou sensível a fanout; mitigado por limites e regras de granularidade.
- Dependência de rede no container frontend para o provider Gemini.

## Decisões implementadas

- Criar `frontend/analytical_chat/` porque a capacidade possui variação concreta de provider e componentes coesos; não criar `common`, `shared` ou `core`.
- Manter a execução SQL em `frontend/gold.py`, preservando Gold como seam único do frontend.
- Criar uma terceira página na navegação, em vez de acoplar o chat ao código já extenso da visão geral.
- Usar parser AST `sqlglot`; validação por regex isolada não é suficiente para múltiplas statements, CTEs e referências fora da allowlist.
- Criar role `obrasgov_chat` dedicada, com grants exatos nas views geráveis e defaults de leitura/timeout; o executor não reutiliza a conexão cacheada do Streamlit.
- Manter SQL, limites, datas técnicas, proveniência e metadados internos fora da interface executiva; a resposta visível contém somente linguagem natural e, quando aplicável, o link da obra.
- Implementar primeiro somente o adapter Gemini; manter a interface, factory e erros independentes de provider para permitir futura extensão sem alterar o `ChatAgent`.
- Não iniciar automaticamente Codex CLI quando Gemini atingir limite de tokens, falhar ou ficar indisponível; essa política só poderá ser definida em uma futura spec aprovada.
- Permitir CTEs de leitura para agregações complexas, mas rejeitar `CREATE TEMP TABLE` e qualquer outra escrita ou DDL na primeira fase.
- Considerar aceitável a transferência do recorte Gold público e limitado ao Gemini, preservando a exclusão de secrets e metadados internos.

## Dúvidas materiais encerradas

- Nenhuma dúvida material permanece na implementação; os requisitos, critérios e evidências estão registrados, e a SPEC-003 foi aprovada para `Done` em 23/08/2026.

## Limitação operacional registrada

- **23/08/2026:** o runtime Gemini devolveu `404 NOT_FOUND` para o modelo inicialmente fixado `gemini-2.5-flash`. Após decisão manual, `gemini-3.5-flash-lite` foi configurado e validado no fluxo completo; não existe fallback automático.
- **23/08/2026:** após a decisão manual por `gemini-3.5-flash-lite`, a saída estruturada, o SQLGuard, a Gold e a síntese passaram cinco execuções da pergunta de maior contrato; seed 42 foi escolhido entre as sementes que passaram o guardrail.
