# Verificação — SPEC-001

**Status:** Verifying
**Data:** 22/08/2026
**Aprovação para Done:** Pendente de aprovação humana explícita

| Critério | Procedimento ou comando | Resultado | Evidência |
|---|---|---|---|
| AC-001 | `docker compose config`; execução dos serviços em containers separados | Passou: Compose validado e ETL, dbt e Streamlit executados em containers separados; rebuild limpo final ficou limitado por timeout de download externo | `compose.yaml`; execução real abaixo |
| AC-002 | Carga nacional real no container `ingestion`; consulta de `bronze.ingestion_resource` | Passou: projetos 651/651 e 130.101/130.101; geometrias 1.076/1.076 e 215.034/215.034 | `ingestion_id=31f70286-0988-49ac-9945-1b0d1bab77c6` |
| AC-003 | `test_failure_is_auditable_and_is_not_published` | Passou; falha e tentativa forçada interrompida ficaram registradas como `failed`, sem substituir o snapshot sucedido | `pytest`; `bronze.ingestion_run` |
| AC-004 | `dbt build --project-dir /app/dbt --profiles-dir /app/dbt` no container | Passou: 153/153, 0 erro | saída dbt de 22/08/2026 |
| AC-005 | Teste dbt `assert_silver_gold_reconciliation` no snapshot real | Passou em 0,13s após Silver materializada | saída dbt: PASS |
| AC-006 | `pytest` frontend e abertura do Streamlit no container | Passou: 10 testes frontend, endpoint de saúde `200 ok` e consultas Gold reais validadas | `tests/frontend/test_smoke.py`; `http://127.0.0.1:8501/_stcore/health` |
| AC-007 | `pytest`; Ruff; compileall; dbt build | Passou: 20 testes, lint e compilação limpos, dbt 153/153 | comandos executados em 22/08/2026 |
| AC-008 | Auditoria de status do Git e `.gitignore` | Passou; segredos e artefatos temporários excluídos; PDF preexistente preservado | `.gitignore`; `git status --short` |
| AC-009 | Testes de repetição, página duplicada e `--force`; segunda execução real | Passou no contrato unitário e na repetição real (`Ingestão skipped`); a coleta forçada foi iniciada no container, mas interrompida por lentidão da API antes da publicação | `tests/ingestion/test_pipeline.py`; `bronze.ingestion_run` |
| AC-010 | `test_source_update_change_marks_run_failed` | Passou | `pytest`: 20 passed |
| AC-011 | Contratos append-only, snapshots por `ingestion_id` e preservação por ingestão | Passou no contrato automatizado; segunda carga real com alteração/ausência não foi forçada contra a API pública | `assert_staging_keeps_project_snapshots_by_ingestion.sql`; chaves Bronze |
| AC-012 | `assert_current_ingestion_is_latest_succeeded`, `assert_current_views_use_current_ingestion` e consulta Gold | Passou: somente o snapshot sucedido publicado | saída dbt e `gold.vw_snapshot_metadata_current` |
| AC-013 | Renderização e submissão dos filtros no Streamlit em container | Passou: a seleção deixou de ser descartada no rerun; Município `Abaiara` alterou KPI, investimento, mapa/tabela e distribuição de situação com dados Gold reais | `tests/frontend/test_smoke.py`; AppTest no container; saúde `200` |
| AC-014 | Filtro único de período sobre `registration_date` com referência em `source_updated_at` | Passou: `selectbox` com `Sem filtro` e cinco opções, teste de intervalo para todos os períodos e `Último mês` no container resultando em 38 obras, R$ 303,31 mi, 29 municípios e 0 em execução | `tests/frontend/test_smoke.py`; AppTest no container |

## Evidências da carga real

- `source_updated_at`: `2026-08-21T00:00:00Z`.
- Gold: 3.205 projetos, 3.244 investimentos, R$ 25.161.698.700,05 previstos, 5.186 localidades, 193 municípios e 695 em execução.
- Dashboard: `R$ 25,16 bi`, 695 obras em execução e 905 registros sem coordenadas sinalizados como dados parciais.
- Filtro real no container: `Abaiara` reduziu o recorte para 5 obras, R$ 9,79 mi, 1 município e 1 obra em execução; a seleção permaneceu após o rerun.
- Filtro de cadastro real no container: `Últimos 12 meses`, ancorado em `source_updated_at=2026-08-21`, resultou em 1.372 obras, R$ 8,63 bi, 192 municípios e 165 em execução.
- Filtro de cadastro real no container: `Último mês`, ancorado em `source_updated_at=2026-08-21`, resultou em 38 obras, R$ 303,31 mi, 29 municípios e 0 em execução; uma única opção permaneceu selecionada.
- Repetição normal: `Ingestão skipped` para o mesmo `ingestion_id`; payload de `/data-atualizacao` preservado na Bronze.

## Limitações registradas

- O primeiro comando dbt falhou porque o Compose não informava `--project-dir`; o comando foi corrigido antes da execução válida.
- O rebuild posterior das imagens com Dockerfiles otimizados excedeu o tempo de download externo; as validações válidas foram executadas nos containers já construídos, montando o código atualizado.
- O serviço Streamlit foi reiniciado em container com `frontend/` montado para aplicar a correção enquanto o rebuild limpo aguardava downloads externos; Postgres permaneceu no container original.
- A execução `--force` real começou e persistiu páginas, mas foi encerrada por lentidão da API pública; ela foi marcada como `failed` e não alterou o snapshot atual.
- AC-011 não dispara uma segunda carga nacional artificial contra a API pública; a garantia automatizada cobre isolamento por `ingestion_id`, append-only e preservação de snapshots.

## Conclusão

Implementação em Verifying. A spec somente pode ser marcada `Done` após aprovação humana explícita.
