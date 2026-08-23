# ADR 0001 — Arquitetura do repositório

**Status:** Aceita
**Data:** 23/08/2026

## Contexto

O case precisa executar localmente ingestão Python, PostgreSQL, dbt e Streamlit,
com fronteiras claras entre Bronze, Silver e Gold. A implementação atual também
possui detalhe de projeto e uma POC de chat analítico opt-in.

## Decisão

- Separar os serviços `postgres`, `ingestion`, `dbt` e `frontend` no Docker Compose.
- Usar `ingestion/`, `dbt/` e `frontend/` como módulos de execução concretos.
- Manter Bronze como seam entre ingestão e dbt e Gold como seam entre dbt e frontend.
- Usar os schemas PostgreSQL `bronze`, `silver` e `gold`; o frontend não acessa raw
  nem Silver.
- Manter um `pyproject.toml` e um `uv.lock`, com extras `ingestion`, `transform` e
  `frontend` e ferramentas no grupo `dev`.
- Usar `src` layout somente no pacote de ingestão; testes ficam fora da aplicação.
- Organizar dbt em `models/staging`, `models/intermediate` e `models/marts`,
  materializando staging/intermediate em Silver e marts em Gold.
- Manter SQL de negócio no dbt e acesso do Streamlit somente por interfaces Gold
  allowlisted; não usar ORM nem criar módulos genéricos sem variação concreta.
- Manter o chat em `frontend/analytical_chat/`, com provider independente do SDK e
  execução SQL dedicada em `frontend/gold.py`.

## Estado implementado

- Bronze coleta oito recursos da API nova e preserva snapshots por `ingestion_id`.
- Gold possui 23 modelos de tabela e 18 views `gold.vw_*_current` públicas.
- O frontend tem as páginas de visão geral, detalhe do projeto e chat com os dados.
- PostgreSQL e os jobs one-shot são containers separados, com dependências por
  healthcheck e sucesso do serviço anterior.
- Roles separam ingestão, dbt, frontend e chat; o chat não recebe acesso a Bronze ou
  Silver.

## Consequências

- A Gold é a única interface de dados do frontend.
- Regras de negócio e cálculos dos KPIs permanecem no dbt ou nas consultas
  agregadoras Gold, não em uma cópia de regra no Streamlit.
- Cada imagem instala somente o extra necessário e executa como usuário não-root.
- Bootstrap cria roles, schemas e grants; scripts em `infra/postgres/upgrade/` são
  aplicados explicitamente quando necessários, pois o bootstrap da imagem só roda
  em volume vazio.
- A separação de jobs exige execução ordenada: PostgreSQL saudável, ingestão,
  dbt e então frontend.

## Evolução futura

Agendamento, observabilidade, operação em nuvem, autenticação/rate limiting e novos
adapters são decisões futuras. Um provider além de Gemini exige nova spec e seus
próprios gates de segurança; a arquitetura atual não cria fallback implícito.

## Referências

- [`docs/arquitetura.md`](../arquitetura.md)
- [`docs/modelagem-dados.md`](../modelagem-dados.md)
- [`compose.yaml`](../../compose.yaml)
