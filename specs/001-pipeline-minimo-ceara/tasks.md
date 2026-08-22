# Tarefas — SPEC-001

**Status:** Não iniciada
**Última revisão:** 21/08/2026

## Fundação e infraestrutura

- [ ] **TASK-001 — REQ-001:** Criar `pyproject.toml`, grupos de dependências, versão Python e `uv.lock`.
- [ ] **TASK-002 — REQ-001:** Criar roles, schemas, privilégios e healthcheck do PostgreSQL.
- [ ] **TASK-003 — REQ-001:** Criar Dockerfiles, `.dockerignore`, `.env.example` e serviços mínimos do Compose.

## Ingestão Python e Bronze

- [ ] **TASK-004 — REQ-002:** Implementar cliente HTTP, paginação e full load dos três endpoints.
- [ ] **TASK-005 — REQ-003/REQ-012:** Criar `ingestion_run` e tabelas raw append-only com rastreabilidade.
- [ ] **TASK-006 — REQ-004/REQ-011:** Implementar reconciliação e publicação somente após carga consistente.
- [ ] **TASK-007 — REQ-010:** Implementar identidade lógica, repetição idempotente, restrições únicas e `--force`.
- [ ] **TASK-008 — REQ-002/REQ-004/REQ-010/REQ-011:** Testar paginação, retentativas, falhas, repetição e mudança da fonte.

## dbt Silver/Gold

- [ ] **TASK-009 — REQ-005:** Declarar sources e criar staging/intermediate dos recursos selecionados.
- [ ] **TASK-010 — REQ-005/REQ-006:** Criar dimensões, fatos e bridges mínimos sem fanout.
- [ ] **TASK-011 — REQ-006/REQ-012:** Criar views atuais do recorte Ceará isoladas pela última execução bem-sucedida.
- [ ] **TASK-012 — REQ-005/REQ-006/REQ-012:** Adicionar catálogo, testes dbt e reconciliações Bronze/Silver/Gold.

## Streamlit

- [ ] **TASK-013 — REQ-007/REQ-008:** Implementar acesso somente leitura às views Gold.
- [ ] **TASK-014 — REQ-007/REQ-008:** Implementar visão geral com KPIs, filtros e contexto do snapshot.
- [ ] **TASK-015 — REQ-007:** Criar testes AppTest e smoke test da aplicação.

## Testes e documentação

- [ ] **TASK-016 — REQ-001/REQ-009:** Coordenar o fluxo ponta a ponta no Compose.
- [ ] **TASK-017 — REQ-009:** Atualizar README, executar validações e registrar evidências.
