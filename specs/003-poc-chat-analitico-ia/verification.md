# Verificação — SPEC-003

**Status:** Done
**Data:** 23/08/2026
**Aprovação para Done:** Confirmada pelo responsável pelo produto em 23/08/2026

| Critério | Procedimento | Resultado | Evidência/limitação |
|---|---|---|---|
| AC-001 | `pytest tests/frontend -q` | Passou: 136 testes | AppTest do chat e smoke das páginas existentes |
| AC-002 | `pytest tests/frontend/test_analytical_chat_agent.py tests/frontend/test_chat_integration.py -q` | Passou | Ordem geração → validação → Gold → síntese e ponte real com fake |
| AC-003/AC-004/AC-005 | `pytest tests/frontend/test_providers.py -q` e inspeção de `compose.yaml` | Passou | Gemini mockado; `codex_cli` rejeitado; nenhum runtime Codex |
| AC-006 | `pytest tests/frontend/test_chat_integration.py -q` e `test_sql_guard.py` | Passou | Catálogo semântico cobre 17 views geráveis; `ingestion_id` excluído; contrato público e colunas dashboard conferidos |
| AC-007 | `pytest tests/frontend/test_analytical_chat_agent.py tests/frontend/test_chat_context.py -q` | Passou | Contratos, empenhos, pagamentos, fornecedores, execução, estudos e histórico são respondíveis; atraso/licitação continuam recusados |
| AC-008/AC-009 | `pytest tests/frontend/test_sql_guard.py -q`; spike parser | Passou: 42 testes; spike 13/13 | AST PostgreSQL, CTEs, joins `INNER/LEFT` por `project_id`, pré-agregação, anti-fanout, locks, wildcard, catálogos, funções e complexidade |
| AC-010 | `pytest tests/frontend/test_gold_executor.py -q`, ACL e smoke PostgreSQL | Passou | Role real `obrasgov_chat`: LOGIN, NOINHERIT, sem CREATEDB/CREATEROLE; SELECT nas 17 views geráveis e somente colunas públicas de metadados, sem CREATE. Login real, metadados, join/agregação Gold e `READ ONLY` passaram |
| AC-011/AC-012 | SQLs dourados contra Gold real, `dbt build` e teste de fanout | Passou | Join de projeto/contrato, CTEs de contratos/empenhos pré-agregados e teste de fanout executados sem expor valores; `dbt build` atual: PASS=235, WARN=0, ERROR=0 |
| AC-013 | `pytest tests/frontend/test_analytical_chat_page.py -q` | Passou: 20 testes | Resposta natural, estados vazios e falhas; SQL, datas, limites e proveniência não são renderizados |
| AC-014/AC-015 | `pytest tests/frontend/test_analytical_chat_page.py tests/frontend/test_analytical_chat_agent.py tests/frontend/test_providers.py -q` | Passou: 37 testes focados | Prompt injection tratado como dado; sem banner ou checkbox; conversa local não exibe metadados técnicos; nenhum segredo, conexão, payload bruto ou `ingestion_id` enviado pelo contrato |
| AC-016 | `pytest tests/frontend/test_analytical_chat_page.py tests/frontend/test_analytical_chat_agent.py tests/frontend/test_chat_integration.py -q` | Passou | Estados distintos, timeout preservado e falha fechada sem fallback |
| AC-017 | `pytest -p no:cacheprovider -q`; `ruff check .`; `uv lock --check`; `docker compose --env-file .env.example -f compose.yaml config --quiet`; `dbt build` | Passou: 154 testes; Ruff/Compose/dbt passaram; `uv` indisponível nesta máquina | Um primeiro dbt falhou apenas por permissão no `target/` montado; repetição com `--target-path /tmp/dbt-target` passou |
| AC-018 | revisão de PRD, arquitetura, ADR, DESIGN, README, `.env.example`, tasks e verification | Passou | Documentação e configuração sincronizadas; grants e upgrade idempotente cobrem as 18 views Gold públicas |
| AC-019 | testes de agente, contexto e AppTest; smoke no container | Passou | `oi` recebe resposta local em `conversation`; texto natural fora do domínio recebe orientação sem provider, Gold ou proveniência falsa |
| AC-020 | integração Gold, SQLGuard e grants | Passou | O chat consulta as 18 views Gold públicas allowlisted, permite joins/agregações read-only por `project_id` e bloqueia fanout |
| AC-021 | testes de contrato, agente e AppTest com dois turnos | Passou | Os seis últimos turnos naturais são propagados; follow-up recebe o histórico visível sem SQL, resultado bruto, snapshot ou secrets |
| AC-022 | SQL dourado, SQLGuard e smoke Gemini no container | Passou | “Quantas obras estão ativas hoje em Fortaleza com porcentagem de conclusão acima de 80%?” retornou 4; Gold reconciliou a contagem distinta por `project_id`, `source_status = 'Em execução'` e `physical_execution_percentage > 80` |
| AC-023 | AppTest da página e teste de normalização do resultado | Passou | Uma única linha com `project_id` oferece link codificado para `project_detail`; múltiplas obras não oferecem link |
| AC-024 | AppTest, inspeção da página e smoke no container | Passou | `st.spinner("Analisando os dados...")` cobre a chamada do agente; a animação não altera a resposta e desaparece antes do resultado/erro |

## Comandos adicionais

- `pytest tests/frontend -q`: 119 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest tests/frontend -q` após a regressão de configuração Gemini: 123 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest tests/frontend -q` após a seleção do modelo: 125 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest tests/frontend/test_analytical_chat_page.py -q`: 16 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest tests/ingestion -q`: 18 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest tests -q` com `.venv`: 137 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest -q` após a regressão de configuração Gemini: 141 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `pytest -q` após o adapter estruturado, guardrail de operadores e seleção do modelo: 143 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `.venv\Scripts\python.exe -m pytest tests/frontend/test_analytical_chat_page.py -q`: 20 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `.venv\Scripts\python.exe -m pytest tests/frontend -q`: 128 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `.venv\Scripts\python.exe -m pytest -q`: 146 passed, 1 warning de permissão ao criar `.pytest_cache`.
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q` após contexto conversacional, regra de execução física e suporte a CTE `SELECT DISTINCT project_id`: 154 passed.
- `.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/frontend/test_analytical_chat_page.py -q` após o spinner: 22 passed.
- `.venv\Scripts\python.exe -m pytest tests/frontend/test_analytical_chat_page.py tests/frontend/test_analytical_chat_agent.py tests/frontend/test_providers.py -q`: 37 passed, 1 warning.
- `.venv\Scripts\python.exe -m pytest tests/frontend/test_analytical_chat_agent.py tests/frontend/test_providers.py -q`: 17 passed, 1 warning.
- `.venv\Scripts\python.exe -m ruff check .`: passou.
- `git diff --check`: passou após os ajustes de contexto e guardrail.
- `.venv/Scripts/ruff.exe check .`: passou.
- `.venv\Scripts\python.exe -m ruff check .`: passou.
- `uv lock --check`: não executado com sucesso; `uv` não está disponível no PATH nem em `.venv\Scripts`.
- `docker compose --env-file .env.example -f compose.yaml config --quiet`: passou sem iniciar containers.
- `docker compose --env-file .env -f compose.yaml config --quiet`: passou com a configuração local; frontend oficial recriado e PostgreSQL saudável.
- `docker compose --env-file .env -f compose.yaml build frontend` e `up -d --force-recreate --no-deps frontend`: passaram; a imagem ativa não contém banner, checkbox ou metadados técnicos na conversa.
- `Invoke-WebRequest http://127.0.0.1:8501`: HTTP 200.
- Contrato da URL dedicada: Compose usa `postgresql://` compatível com `psycopg.connect()`; a URL frontend continua separada para `st.connection()`.
- `docker compose run --rm --no-deps dbt build --project-dir /app/dbt --profiles-dir /app/dbt --target-path /tmp/dbt-target --select path:models/marts`: 23 tabelas, 18 views e 88 testes; `PASS=129`, `WARN=0`, `ERROR=0`.
- Evidência intermediária, antes do build completo atual, após a proteção por coluna da view de metadados: 23 tabelas, 18 views e 137 testes; `PASS=178`, `WARN=0`, `ERROR=0`.
- Após adicionar o grant estático de metadados: `dbt build --select vw_snapshot_metadata_current`: 1 view e 11 testes, `PASS=12`, `WARN=0`, `ERROR=0`.
- Role `obrasgov_chat` conectou em read-only; o catálogo atual contém 18 views Gold e `gold.vw_snapshot_metadata_current` existe.
- Frontend atual permanece ativo em HTTP 200; smoke completo de `gemini-3.5-flash-lite` com seed 42 passou 5/5 e a repetição final passou 3/3 em `answered`, etapa `completed`, com SQL e resultado presentes; nenhum valor foi impresso.
- Após a alteração de UX: `docker compose --env-file .env -f compose.yaml build frontend` e `up -d --force-recreate --no-deps frontend` passaram; `Invoke-WebRequest http://127.0.0.1:8501` retornou HTTP 200.
- Após a correção de contexto e do guardrail: `docker compose --env-file .env -f compose.yaml build frontend` e `up -d --force-recreate --no-deps frontend` passaram; as variantes digitada e acentuada da pergunta retornaram `answered`, etapa `completed`, resposta natural com 4 e uma linha Gold; `Invoke-WebRequest http://127.0.0.1:8501` retornou HTTP 200.
- Reprodução do erro reportado: três execuções consecutivas no container atualizado retornaram `answered/completed`, resposta com 4 e uma linha Gold; os logs não mostraram crash do Streamlit. O detalhe da falha original não tinha timestamp/log associado.
- O CTA de detalhe usa `project_detail?project_id=...` com URL encoding; a página de detalhe consome `st.query_params["project_id"]` e abre a obra diretamente.
- Revalidação da credencial: `models.list/get` retornaram modelos com `generateContent`; `gemini-3.5-flash-lite` respondeu com envelope estruturado, SQL aprovado, Gold e síntese nas execuções finais.
- Modelos candidatos observados: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.7-flash` e aliases Flash/Pro; o modelo operacional foi definido como `gemini-3.5-flash-lite` por decisão manual.
- Banco após o restart final: conexão read-only da role `obrasgov_chat` passou; catálogo com 18 views Gold e metadata disponível.
- ACL final da role: 17 privilégios de tabela Gold, 8 privilégios de coluna na view de metadados, `source_updated_at` permitido e `ingestion_id` negado.
- SQLs dourados no PostgreSQL: consultas de contrato, empenho e CTE pré-agregada executadas pela role dedicada sem imprimir valores; fanout de investimento validado como seguro.
- Timeout: `GoldTimeoutError` preserva estado distinto até o agente e a página, coberto por regressão integrada.
- `python specs/003-poc-chat-analitico-ia/parser_spike.py`: 13/13 casos passou com `sqlglot 30.17.0`, dialeto PostgreSQL.
- `python -m compileall -q frontend tests specs/003-poc-chat-analitico-ia/parser_spike.py`: passou.
- `git diff --check`: passou.

## Limitações e tarefas restantes

- `uv lock --check --no-cache` continua não executável porque `uv` não está disponível no PATH nem em `.venv\Scripts`; registrar essa limitação permanece necessário.
- Não há bloqueio técnico restante no smoke do modelo ou na UI; não há fallback automático.
- A validação em runtime depende do Gemini configurado no ambiente; os testes automatizados usam provider fake/mockado e não imprimem prompt, SQL integral ou credenciais.
- O `.env.example` continua com `ANALYTICAL_CHAT_ENABLED=false`; o `.env` local foi habilitado por autorização explícita e a página inicia a conversa sem checkbox, mantendo a proteção por configuração.

## Conclusão

A implementação da SPEC-003 está em `Done`, após aprovação explícita. A capacidade
continua desabilitada por padrão e não inclui Codex CLI, fallback automático,
monitoramento de tokens ou deploy de produção.
