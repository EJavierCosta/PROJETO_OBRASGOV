# ADR 0003 — Chat analítico com provider Gemini e SQL seguro

**Status:** Aceita
**Data:** 23/08/2026

## Contexto

A SPEC-003 possui uma página opcional para perguntas em linguagem natural sobre o
snapshot Gold atual. O fluxo implementado é:

```text
pergunta → Gemini → SQLGuard AST → executor Psycopg read-only → Gold limitada → Gemini → resposta
```

O chat precisa consultar fatos e relações de granularidades diferentes sem fanout,
sem receber credenciais ou conexão e sem transformar indisponibilidade do provider
em escalonamento implícito.

## Decisão

- A primeira fase usa somente o provider Gemini com a biblioteca oficial
  `google-genai`.
- O contrato `LLMProvider`, a factory, os envelopes e os erros são independentes do
  SDK; `fake` é permitido para testes.
- `LLM_PROVIDER` aceita `gemini` e `fake`; `codex_cli` é rejeitado. Não há instalação,
  montagem ou execução do Codex CLI no frontend ou no Compose.
- `ANALYTICAL_CHAT_ENABLED=false` é o padrão. Quando habilitado, Gemini exige
  `GEMINI_API_KEY`; uma falha de configuração, provider, guard ou Gold termina o
  fluxo sem fallback automático.
- O provider recebe pergunta, histórico natural limitado, contexto semântico, SQL
  aprovado e resultado Gold limitado. Não recebe conexão, callable de banco, shell,
  secrets, payload raw, `ingestion_id` ou descoberta de schema.
- O catálogo expõe 18 views Gold públicas: 17 são geráveis pelo LLM e
  `gold.vw_snapshot_metadata_current` é acessada somente por consulta estática do
  adaptador para obter `source_updated_at` e `ingested_at`.
- O SQLGuard usa `sqlglot` no dialeto PostgreSQL e aceita somente `SELECT` ou CTE de
  leitura sobre views/colunas allowlisted.
- São rejeitados DDL/DML, múltiplas instruções, `CREATE TEMP TABLE`, `SELECT *`,
  `SELECT INTO`, locks, catálogos, funções/tabelas não allowlisted, CTE recursiva,
  subqueries, `CROSS JOIN`, `LATERAL`, funções de tabela e joins sem chave segura.
- Joins permitidos devem respeitar as chaves públicas e as relações do catálogo,
  normalmente `project_id`; relações 1:N independentes devem ser pré-agregadas
  antes de serem combinadas.
- O executor usa a role dedicada `obrasgov_chat`, conexão Psycopg separada,
  transação `READ ONLY`, `search_path = gold, pg_catalog`, timeout e rollback.

## Configuração Gemini auditada

O `.env.example`, o `.env` local, `compose.yaml` e os defaults de
`frontend/analytical_chat/config.py` usam `gemini-3.5-flash-lite`. O modelo foi
validado no fluxo completo; a aplicação não mede tokens nem executa telemetria de
suficiência e não faz fallback automático.

## Limites efetivos

- pergunta: 4.000 caracteres;
- histórico: seis turnos naturais;
- timeout do provider: 30 segundos;
- payload ao provider: até 100 linhas, 20 colunas, 32.000 bytes e 1.000 caracteres
  por célula;
- executor Gold: 5.000 ms, 100 linhas, 20 colunas, 2.000 células e 1 MiB;
- SQLGuard: 12.000 caracteres, 500 nós AST, profundidade 32, oito CTEs, seis
  subqueries, quatro relações, três joins, cinco colunas de agrupamento e oito
  agregações.

## UX e fronteira de exposição

O chat aparece como página própria e não exibe checkbox, SQL, limites, datas
 técnicas, proveniência ou erros internos na conversa. Quando o resultado identifica
 uma única obra sem truncamento, a página pode oferecer link para o detalhe usando
 `project_id`; agregações ou múltiplas obras não recebem esse link.

## Alternativas rejeitadas

### Gemini e Codex CLI juntos

Rejeitada na primeira fase por ampliar o risco operacional antes de existir evidência
de insuficiência do Gemini.

### Fallback automático para Codex CLI

Rejeitado porque criaria escalonamento implícito para um runtime com permissões e
política ainda não aprovadas.

### Acoplamento direto do `ChatAgent` ao Gemini

Rejeitado para preservar testes determinísticos, erros controlados e futura troca de
provider por decisão explícita.

## Consequências

- A capacidade fica desabilitada por padrão e depende de configuração explícita.
- Testes não dependem de rede ou créditos Gemini; o smoke real depende da chave e do
  modelo configurados no ambiente.
- O SQL aprovado continua sendo uma proposta do modelo, não uma prova de correção
  semântica; o guard, a Gold e as reconciliações são a fronteira técnica.
- O executor dedicado evita reutilizar a conexão cacheada da visão geral.
- Não há autenticação ou rate limiting de produção nesta POC local.

## Evolução futura

Qualquer provider adicional, mudança de catálogo, aumento de limites, autenticação,
rate limiting ou retenção de conversa exige nova decisão/spec. A adoção futura do
Codex CLI exigirá comprovação de isolamento, ambiente sanitizado e ausência de
acesso indevido antes de qualquer habilitação.

## Referências

- [`specs/003-poc-chat-analitico-ia/spec.md`](../../specs/003-poc-chat-analitico-ia/spec.md)
- [`docs/arquitetura.md`](../arquitetura.md)
- [`docs/modelagem-dados.md`](../modelagem-dados.md)
