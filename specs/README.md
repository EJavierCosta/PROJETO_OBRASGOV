# Especificações

Cada incremento vertical possui uma pasta numerada com quatro artefatos:

```text
NNN-nome-do-incremento/
├── spec.md
├── plan.md
├── tasks.md
└── verification.md
```

Copie `_template`, atribua o próximo número sequencial e substitua os campos entre `< >`.

O processo completo, os gates e a hierarquia documental estão em [Desenvolvimento orientado por especificações](../docs/desenvolvimento-spec-driven.md).

## Specs

| ID | Incremento | Status | Resumo atual |
|---|---|---|---|
| [SPEC-001](001-pipeline-minimo-ceara/spec.md) | Pipeline mínimo de projetos do Ceará | **Done** | Pipeline nacional, recorte CE de construção, Gold e visão geral Streamlit; aprovação humana explícita em 23/08/2026. |
| [SPEC-002](002-detalhe-completo-projeto/spec.md) | Detalhe completo do projeto | **Verifying** | Detalhe de uma obra com as oito fontes do snapshot, fatos Gold separados e navegação por `project_id`; validação ponta a ponta registrada, aprovação pendente. |
| [SPEC-003](003-poc-chat-analitico-ia/spec.md) | POC de chat analítico com IA | **Done** | Chat Gemini-only, modelo operacional `gemini-3.5-flash-lite`, 17 views geráveis mais metadados estáticos, histórico natural e desabilitado por padrão; aprovação registrada em 23/08/2026. |

## Estado de validação registrado

- Snapshot atual: `ingestion_id=469701dc-d03e-43b8-b6de-8dd3f1713f33`, `source_updated_at=2026-08-22T00:00:00Z`, ingestão `succeeded`.
- Gold atual do recorte: 3.207 projetos, 3.246 investimentos, R$ 25.164.016.200,05 previstos, 5.189 localidades, 193 municípios e 698 obras em execução.
- Suíte local: `154 passed`; frontend: `136 passed`; ingestão: `18 passed`; Ruff direcionado: passou; spike SQL: `13/13`.
- `dbt build` registrado: 37 modelos de tabela, 18 views e 180 testes; `PASS=235`, `WARN=0`, `ERROR=0`. `uv lock --check` continua não confirmável porque `uv` não está disponível.
