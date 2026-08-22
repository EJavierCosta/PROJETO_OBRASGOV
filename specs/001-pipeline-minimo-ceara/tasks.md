# Tarefas — SPEC-001

**Status:** Verifying
**Última revisão:** 22/08/2026

## Fundação e infraestrutura

- [x] **TASK-001 — REQ-001:** Criar `pyproject.toml`, grupos de dependências, versão Python e `uv.lock`.
- [x] **TASK-002 — REQ-001:** Criar roles, schemas, privilégios e healthcheck do PostgreSQL.
- [x] **TASK-003 — REQ-001:** Criar Dockerfiles, `.dockerignore`, `.env.example` e serviços mínimos do Compose.

## Ingestão Python e Bronze

- [x] **TASK-004 — REQ-002:** Implementar cliente HTTP, paginação e full load dos três endpoints.
- [x] **TASK-005 — REQ-003/REQ-012:** Criar `ingestion_run` e tabelas raw append-only com rastreabilidade.
- [x] **TASK-006 — REQ-004/REQ-011:** Implementar reconciliação e publicação somente após carga consistente.
- [x] **TASK-007 — REQ-010:** Implementar identidade lógica, repetição idempotente, restrições únicas e `--force`.
- [x] **TASK-008 — REQ-002/REQ-004/REQ-010/REQ-011:** Testar paginação, retentativas, falhas, repetição e mudança da fonte.

## dbt Silver/Gold

- [x] **TASK-009 — REQ-005:** Declarar sources e criar staging/intermediate dos recursos selecionados.
- [x] **TASK-010 — REQ-005/REQ-006:** Criar dimensões, fatos e bridges mínimos sem fanout.
- [x] **TASK-011 — REQ-006/REQ-012:** Criar views atuais do recorte Ceará isoladas pela última execução bem-sucedida.
- [x] **TASK-012 — REQ-005/REQ-006/REQ-012:** Adicionar catálogo, testes dbt e reconciliações Bronze/Silver/Gold.

## Streamlit

- [x] **TASK-013 — REQ-007/REQ-008:** Implementar acesso somente leitura às views Gold.
- [x] **TASK-014 — REQ-007/REQ-008:** Implementar visão geral com KPIs, filtros e contexto do snapshot.
- [x] **TASK-015 — REQ-013:** Aplicar `DESIGN.md`, a logo oficial e a composição da imagem de referência à visão geral.
- [x] **TASK-016 — REQ-007/REQ-013:** Criar testes AppTest, smoke test e inspeção visual da aplicação.

## Testes e documentação

- [x] **TASK-017 — REQ-001/REQ-009:** Coordenar o fluxo ponta a ponta no Compose.
- [x] **TASK-018 — REQ-009/REQ-013:** Atualizar README, executar validações e registrar evidências, incluindo a inspeção visual.
