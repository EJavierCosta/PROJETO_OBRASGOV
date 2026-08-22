# ADR 0001 — Arquitetura do repositório

**Status:** Aceita

**Data:** 21/08/2026

## Contexto

O case exige ingestão Python, PostgreSQL, dbt, arquitetura medalhão, frontend simples e execução integral por Docker Compose. O repositório precisa ser reproduzível, navegável e proporcional ao escopo de uma entrega técnica.

## Decisão

- Separar os módulos de execução em ingestão Python, transformação dbt e frontend Streamlit.
- Usar Bronze e Gold como seams de dados entre os módulos.
- Manter um único `pyproject.toml` e um único `uv.lock`.
- Separar dependências nos extras `ingestion`, `transform` e `frontend`, com ferramentas no grupo `dev`.
- Usar `src` layout para o pacote de ingestão e testes fora do código da aplicação.
- Organizar dbt em `staging`, `intermediate` e `marts`, mapeados fisicamente para Silver e Gold.
- Manter Dockerfiles próximos aos módulos e `compose.yaml` na raiz.
- Não criar pastas genéricas ou interfaces abstratas sem variação concreta.

## Consequências

- A Gold se torna a única interface de dados do frontend.
- Regras de negócio permanecem no dbt e não são duplicadas no Streamlit.
- Cada imagem instala apenas suas dependências.
- Bootstrap PostgreSQL cria somente roles, schemas e privilégios; dbt gerencia os modelos analíticos.
- Novos seams exigirão uma variação concreta ou um segundo adapter.

## Referência

Detalhamento e fontes oficiais: [`docs/arquitetura.md`](../arquitetura.md).
