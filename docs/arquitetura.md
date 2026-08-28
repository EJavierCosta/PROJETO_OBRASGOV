# Arquitetura do repositório

**Estado:** SPEC-001, SPEC-002 e SPEC-003 concluídas (`Done`)
**Última revisão:** 23/08/2026

## Capacidade entregue

O fluxo implementado é:

```text
ObrasGov → ingestão Python → Bronze → dbt staging/intermediate (Silver)
         → dbt marts (Gold) → views Gold current → Streamlit
```

- A ingestão coleta nacionalmente oito recursos da API nova: `data-atualizacao`,
  `projeto-investimento`, `geometria`, `contrato`, `empenho`, `execucao-fisica`,
  `historico-situacao-cancelada-paralisada` e `estudo-viabilidade`.
- A Bronze preserva payloads `jsonb`, páginas, hashes, timestamps e `ingestion_id`.
  Uma execução só é publicada como `succeeded` quando os oito recursos são
  reconciliados e `source_updated_at` permanece estável.
- A Silver é composta por modelos dbt de `staging` e `intermediate`, com tipagem,
  limpeza, deduplicação por ingestão e explosão separada das relações multivaloradas.
- A Gold aplica `uf_principal = CE`, `natureza_intervencao = Obra` e
  `especie_intervencao = Construção`. A Gold possui 23 modelos materializados como
  tabelas e 18 views `gold.vw_*_current` públicas.
- O Streamlit consulta somente a Gold. Há visão geral, detalhe de uma obra por
  `project_id` e página opcional de chat analítico.

SPEC-001 e SPEC-002 são capacidades concluídas e aprovadas pelo usuário em
23/08/2026. O chat da SPEC-003 está em `Done` após aprovação registrada na mesma
data.

## Módulos e fronteiras

| Módulo | Responsabilidade | Fronteira de dados |
|---|---|---|
| `ingestion/` | HTTP, paginação, retentativas, idempotência e persistência dos payloads | publica Bronze |
| `dbt/` | staging, intermediate, fatos, dimensões, bridges e views | lê Bronze; publica Silver/Gold |
| `frontend/` | consultas somente leitura, filtros, apresentação e chat | lê somente views Gold |
| `infra/postgres/` | roles, schemas, grants e scripts de upgrade | controla privilégios |
| `compose.yaml` | orquestra os serviços locais | mantém serviços separados |

O PostgreSQL usa os schemas `bronze`, `silver` e `gold`; o schema `public` não é
usado para os objetos analíticos. As regras de negócio ficam no dbt. O frontend não
consulta raw, Silver ou snapshots históricos diretamente.

## Estrutura verificada

```text
/
├── ingestion/
│   ├── Dockerfile
│   └── src/obrasgov_ingestion/
├── dbt/
│   ├── Dockerfile
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/staging/obrasgov/
│   ├── models/intermediate/
│   ├── models/marts/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── streamlit_app.py
│   ├── gold.py
│   ├── analytical_chat/
│   └── pages/
├── infra/postgres/
│   ├── initdb/
│   └── upgrade/
├── tests/ingestion/
├── tests/frontend/
├── assets/design/
├── docs/
├── specs/
├── .streamlit/config.toml
├── compose.yaml
├── pyproject.toml
└── uv.lock
```

`staging` e `intermediate` são schemas físicos Silver; `marts` é Gold. Os
Dockerfiles instalam apenas o extra correspondente (`ingestion`, `transform` ou
`frontend`) a partir do `pyproject.toml` e `uv.lock`, e executam como usuário não-root.

## Serviços Docker Compose

| Serviço | Tipo | Função |
|---|---|---|
| `postgres` | persistente | PostgreSQL 16, volume local, healthcheck e bootstrap de roles/schemas |
| `ingestion` | one-shot | executa `python -m obrasgov_ingestion` e depende do PostgreSQL saudável |
| `dbt` | one-shot | executa `dbt build` depois da ingestão bem-sucedida |
| `frontend` | aplicação | executa Streamlit em `127.0.0.1:8501` depois do dbt |

As credenciais são fornecidas por ambiente. `obrasgov_frontend` recebe `USAGE` e
`SELECT` na Gold; `obrasgov_chat` usa uma conexão Psycopg dedicada, tem `USAGE` e
`SELECT` nas 18 views públicas e não possui `CREATE`, acesso à Bronze ou à Silver.
O grant por coluna de `gold.vw_snapshot_metadata_current` é reaplicado pelo hook
`on-run-end` do dbt após cada reconstrução, mantendo `ingestion_id` fora do acesso.

## Frontend e contratos Gold

`frontend/gold.py` mantém a allowlist das 18 views e separa duas conexões:

- `GOLD_DATABASE_URL`: `st.connection` para visão geral e detalhe;
- `GOLD_CHAT_DATABASE_URL`: Psycopg dedicado para o SQL aprovado do chat.

As consultas da visão geral usam mercado, localização, situação e metadados. O
detalhe consulta as interfaces próprias de identificação, participantes, localização,
intervenção, investimento, contratos, empenhos, execução física, histórico, estudos,
PPA, restrição, foto e cobertura, sempre filtradas por um único `project_id`.

## Chat analítico — SPEC-003

O chat é opt-in: `ANALYTICAL_CHAT_ENABLED=false` por padrão no Compose e no
`.env.example`. Os providers aceitos pelo código são `gemini` e `fake`; `fake` é
usado nos testes e `codex_cli` falha fechado. Não há fallback automático.

O provider Gemini recebe somente pergunta, contexto semântico, SQL aprovado e
resultado Gold limitado. O histórico enviado ao provider contém apenas os seis
últimos turnos naturais da sessão. Não recebe conexão, shell, secrets, payload raw,
`ingestion_id` ou descoberta de schema. O catálogo possui 17 views geráveis; a
`gold.vw_snapshot_metadata_current` é lida apenas por uma consulta estática do
adaptador para obter as datas públicas do snapshot.

Limites efetivos do código:

- pergunta: 4.000 caracteres; histórico: seis turnos naturais;
- provider: timeout de 30 segundos;
- resultado enviado ao provider: 100 linhas, 20 colunas, 32.000 bytes e 1.000
  caracteres por célula;
- executor Gold: `statement_timeout` de 5.000 ms, 100 linhas, 20 colunas, 2.000
  células e 1 MiB;
- SQLGuard: 12.000 caracteres, 500 nós AST, profundidade 32, até oito CTEs, seis
  subqueries, quatro relações, três joins, cinco colunas de agrupamento e oito
  agregações.

O guard aceita apenas `SELECT`/CTE de leitura sobre views allowlisted, rejeita
escrita, múltiplas instruções, wildcard, catálogos, funções ou tabelas não
allowlisted, locks, CTE recursiva, `CROSS JOIN`, `LATERAL` e fanout não pré-agregado.

Configuração Gemini auditada em 23/08/2026: `.env.example`, o fallback Python e o
fallback do Compose usam `gemini-3.5-flash-lite`; a seleção não é fallback de
provider. A interface removeu checkbox e banner técnico, exibe apenas a resposta
executiva e mostra o spinner “Analisando os dados...” durante o processamento.

## Evolução futura

- agendamento, observabilidade e operação em nuvem;
- comparação nacional no frontend e análise temporal explícita entre snapshots;
- política de retenção para a Bronze e monitoramento de colisões das chaves técnicas;
- autenticação, rate limiting e governança de uso do chat;
- validação territorial formal e enriquecimentos que tenham fonte aprovada;
- eventual provider adicional, inclusive Codex CLI, somente por nova spec e gate de
  isolamento.

Não fazem parte da capacidade entregue: inferir licitação aberta, atraso,
prioridade comercial, município principal, geometria de restrição, conteúdo de foto
ou situação/conclusão de estudo sem campo publicado pela fonte.

## Referências estruturais

- [`docs/modelagem-dados.md`](modelagem-dados.md)
- [`docs/adr/0001-arquitetura-do-repositorio.md`](adr/0001-arquitetura-do-repositorio.md)
- [`docs/adr/0002-modelagem-medalhao-obrasgov.md`](adr/0002-modelagem-medalhao-obrasgov.md)
- [`docs/adr/0003-chat-analitico-llm-e-sql-seguro.md`](adr/0003-chat-analitico-llm-e-sql-seguro.md)
