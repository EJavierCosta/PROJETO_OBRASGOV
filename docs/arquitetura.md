# Arquitetura do repositório

**Status:** Decisão-base aprovada; detalhamento incremental
**Última revisão:** 21/08/2026

## Decisões confirmadas

- O repositório será organizado por módulos de execução: ingestão Python, transformação dbt e frontend Streamlit.
- Bronze será o seam entre ingestão e dbt.
- Gold será o seam entre dbt e Streamlit.
- O repositório terá um único `pyproject.toml`, um `uv.lock` versionado e uma versão Python fixada.
- As dependências de execução serão separadas nos extras `ingestion`, `transform` e `frontend`; ferramentas de desenvolvimento ficarão no grupo `dev`.
- Cada imagem Docker instalará somente o grupo necessário ao seu módulo.
- Não serão criadas pastas genéricas `common`, `shared` ou `core` sem reutilização concreta.
- Não será usado ORM; SQL de negócio permanecerá no dbt.
- O mapeamento físico será: Bronze pela ingestão Python, Silver por modelos dbt de staging/intermediate e Gold por marts dbt.

## Princípios

- A interface da ingestão será pequena e esconderá paginação, repetição, idempotência e persistência.
- O Streamlit consultará a Gold em modo somente leitura.
- Testes atravessarão as mesmas interfaces usadas em execução.
- Um novo seam só será criado quando existir variação concreta ou mais de um adapter.

## Estrutura em definição

```text
/
├── ingestion/
│   ├── Dockerfile
│   └── src/
│       └── obrasgov_ingestion/
│           ├── __init__.py
│           ├── __main__.py
│           ├── cli.py
│           ├── pipeline.py
│           ├── obrasgov.py
│           └── postgres.py
├── dbt/
│   ├── Dockerfile
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   │   └── obrasgov/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── streamlit_app.py
│   ├── pages/
│   │   ├── overview.py
│   │   └── project_detail.py
│   ├── gold.py
│   └── .streamlit/
│       └── config.toml
├── infra/
│   └── postgres/
│       └── initdb/
│           ├── 00_roles.sql
│           ├── 10_schemas.sql
│           └── 20_grants.sql
├── tests/
│   ├── ingestion/
│   ├── frontend/
│   └── integration/
├── docs/
│   ├── arquitetura.md
│   ├── modelagem.md
│   └── adr/
├── .github/
│   └── workflows/
│       └── ci.yml
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── .python-version
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

## Práticas verificadas nas documentações oficiais

### Python, uv e pytest

- O código importável da ingestão usa `src` layout para evitar imports acidentais da cópia local.
- `pyproject.toml` centraliza build, dependências e configuração das ferramentas.
- `uv.lock` será versionado e os containers usarão sincronização bloqueada.
- Testes ficam fora do código da aplicação e o pytest usa `--import-mode=importlib`.

### Ingestão HTTP e PostgreSQL

- Um `httpx.Client` será reutilizado durante a execução para pooling de conexões, com timeout explícito.
- Retentativas serão limitadas a falhas transitórias; respostas e tentativas serão observáveis nos logs.
- Cargas em lote usarão `COPY` do Psycopg dentro de transações.

### dbt

- Bronze é fonte declarada com `source()` e permanece fora da implementação dbt.
- `models/staging/obrasgov` faz renomeação, tipagem e limpeza 1:1, sem agregações.
- `models/intermediate` concentra joins e transformações preparatórias apenas quando necessários.
- `models/marts` contém fatos e dimensões consumidos pelo frontend.
- Os schemas físicos serão `bronze`, `silver` e `gold`; as pastas seguem a convenção dbt `staging`, `intermediate` e `marts`.
- Testes e descrições YAML ficam próximos dos modelos; testes SQL específicos ficam em `dbt/tests`.

### Streamlit

- `streamlit_app.py` será o entrypoint e usará `st.Page` com `st.navigation`.
- `gold.py` esconderá consultas somente leitura à Gold atrás de uma interface pequena.
- A conexão usará `st.connection`; resultados terão TTL explícito.
- Testes das páginas usarão `streamlit.testing.v1.AppTest` com pytest.
- `.streamlit/config.toml` será versionado; `secrets.toml` não será commitado.

### PostgreSQL e Docker Compose

- Schemas e privilégios serão separados; o frontend terá somente `USAGE` e `SELECT` na Gold.
- O schema `public` não será usado para objetos da aplicação.
- Scripts em `infra/postgres/initdb` serão apenas bootstrap, pois a imagem oficial só os executa em volume vazio.
- Dockerfiles ficam próximos de cada módulo e usam a raiz como contexto de build para acessar `pyproject.toml` e `uv.lock`.
- Imagens serão fixadas por versão, usarão `.dockerignore`, cache de dependências e usuário não-root quando suportado.
- PostgreSQL terá `healthcheck`; ingestão e dbt serão execuções one-shot coordenadas por `service_healthy` e `service_completed_successfully`.
- Credenciais reais não serão versionadas; Compose secrets será preferido para valores sensíveis.

## Referências oficiais

- [PyPA — src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyPA — pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [uv — projetos e lockfile](https://docs.astral.sh/uv/guides/projects/)
- [uv — Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [pytest — boas práticas](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [HTTPX — Client](https://www.python-httpx.org/advanced/clients/)
- [HTTPX — timeouts](https://www.python-httpx.org/advanced/timeouts/)
- [Psycopg — COPY](https://www.psycopg.org/psycopg3/docs/basic/copy.html)
- [dbt — estrutura recomendada](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [dbt — staging](https://docs.getdbt.com/best-practices/how-we-structure/2-staging)
- [dbt — sources](https://docs.getdbt.com/docs/build/sources)
- [dbt — data tests](https://docs.getdbt.com/docs/build/data-tests)
- [Streamlit — navegação multipágina](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)
- [Streamlit — PostgreSQL](https://docs.streamlit.io/develop/tutorials/databases/postgresql)
- [Streamlit — testes](https://docs.streamlit.io/develop/concepts/app-testing)
- [Docker — Dockerfile](https://docs.docker.com/build/building/best-practices/)
- [Docker Compose — ordem de inicialização](https://docs.docker.com/compose/how-tos/startup-order/)
- [PostgreSQL — schemas e privilégios](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Imagem oficial PostgreSQL — inicialização](https://hub.docker.com/_/postgres)
