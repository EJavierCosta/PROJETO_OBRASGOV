# Verificação — SPEC-001

**Status:** Done
**Data:** 23/08/2026
**Aprovação humana explícita para Done:** Confirmada pelo usuário em 23/08/2026 ("finalizamos a spec 1")

| Critério | Procedimento ou comando | Resultado | Evidência |
|---|---|---|---|
| AC-001 | `docker compose config`; execução dos serviços em containers separados | Passou: Compose validado e ETL, dbt e Streamlit executados em containers separados; rebuild limpo final ficou limitado por timeout de download externo | `compose.yaml`; execução real abaixo |
| AC-002 | Carga nacional real no container `ingestion`; consulta de `bronze.ingestion_resource` | Passou nos recursos da SPEC-001: projetos 651/651 e 130.147/130.147; geometrias 1.076/1.076 e 215.146/215.146 | `ingestion_id=469701dc-d03e-43b8-b6de-8dd3f1713f33` |
| AC-003 | `test_failure_is_auditable_and_is_not_published` | Passou; falha e tentativa forçada interrompida ficaram registradas como `failed`, sem substituir o snapshot sucedido | `pytest`; `bronze.ingestion_run` |
| AC-004 | `dbt build --project-dir /app/dbt --profiles-dir /app/dbt` no container | Passou: 37 modelos de tabela, 18 views e 180 testes; `PASS=235`, `WARN=0`, `ERROR=0` | saída dbt registrada em 23/08/2026 |
| AC-005 | Teste dbt `assert_silver_gold_reconciliation` no snapshot real | Passou em 0,13s após Silver materializada | saída dbt: PASS |
| AC-006 | `pytest` frontend e abertura do Streamlit no container | Passou: 136 testes frontend, endpoint de saúde `200 ok` e consultas Gold reais validadas | `tests/frontend/test_smoke.py`; `http://127.0.0.1:8501/_stcore/health` |
| AC-007 | `pytest`; Ruff; compileall; dbt build | Passou: suíte atual `154 passed`, Ruff limpo e dbt `PASS=235`; a compilação permanece coberta pela evidência anterior | comandos executados em 23/08/2026 |
| AC-008 | Auditoria de status do Git e `.gitignore` | Passou; segredos e artefatos temporários excluídos; PDF preexistente preservado | `.gitignore`; `git status --short` |
| AC-009 | Testes de repetição, página duplicada e `--force`; segunda execução real | Passou no contrato unitário e na repetição real (`Ingestão skipped`); a coleta forçada foi iniciada no container, mas interrompida por lentidão da API antes da publicação | `tests/ingestion/test_pipeline.py`; `bronze.ingestion_run` |
| AC-010 | `test_source_update_change_marks_run_failed` | Passou | `tests/ingestion`: 18 passed |
| AC-011 | Contratos append-only, snapshots por `ingestion_id` e preservação por ingestão | Passou no contrato automatizado; segunda carga real com alteração/ausência não foi forçada contra a API pública | `assert_staging_keeps_project_snapshots_by_ingestion.sql`; chaves Bronze |
| AC-012 | `assert_current_ingestion_is_latest_succeeded`, `assert_current_views_use_current_ingestion` e consulta Gold | Passou: somente o snapshot sucedido publicado | saída dbt e `gold.vw_snapshot_metadata_current` |
| AC-013 | Renderização e submissão dos filtros no Streamlit em container | Passou: a seleção deixou de ser descartada no rerun; Município `Abaiara` alterou KPI, investimento, mapa/tabela e distribuição de situação com dados Gold reais; interface com linguagem executiva, sem termos de camada técnica, KPIs de contagem exibidos como inteiros, card sem ID técnico, tag de dados parciais com motivo no hover/foco, mapa com `i` no rodapé e instruções exibidas somente no hover/foco, sem contagem técnica de registros, filtro municipal preservando os pins dos projetos selecionados, favicon compacto da Vertere e temas Light/Dark legíveis | `tests/frontend/test_smoke.py`; navegador no container em `http://127.0.0.1:8501/`; saúde `200` |
| AC-014 | Filtro único de período sobre `registration_date` com referência em `source_updated_at` | Passou: `selectbox` com `Sem filtro` e cinco opções; no snapshot atual, `Últimos 12 meses` resulta em 1.365 obras, R$ 8,59 bi, 192 municípios e 164 em execução; `Último mês` resulta em 22 obras, R$ 198,75 mi, 18 municípios e 0 em execução | `tests/frontend/test_smoke.py`; consulta Gold atual |

## Evidências da carga real

- `source_updated_at`: `2026-08-22T00:00:00Z`.
- Gold: 3.207 projetos, 3.246 investimentos, R$ 25.164.016.200,05 previstos, 5.189 localidades, 193 municípios e 698 em execução.
- Auditoria geográfica em 23/08/2026: 4.683 pins válidos foram carregados; 7 pins de 4 projetos ficaram fora de um envelope amplo de triagem do Ceará (`latitude -7,90 a -2,70`; `longitude -41,50 a -37,00`). As mesmas coordenadas aparecem no payload Bronze, indicando anomalia já presente na fonte/associação do projeto, não deslocamento introduzido pelo dbt. A Gold atual ainda não possui validação point-in-polygon contra o limite oficial nem classificação formal entre outro estado e mar.
- Dashboard: `R$ 25,16 bi`, 698 obras em execução e 5.543 associações sem coordenadas sinalizadas como dados parciais.
- Filtro real no container: `Abaiara` reduziu o recorte para 5 obras, R$ 9,79 mi, 1 município e 1 obra em execução; a seleção permaneceu após o rerun.
- Filtro de cadastro no snapshot atual: `Últimos 12 meses`, ancorado em `source_updated_at=2026-08-22`, resultou em 1.365 obras, R$ 8,59 bi, 192 municípios e 164 em execução.
- Filtro de cadastro no snapshot atual: `Último mês`, ancorado em `source_updated_at=2026-08-22`, resultou em 22 obras, R$ 198,75 mi, 18 municípios e 0 em execução; uma única opção permanece selecionada.
- Mapa no container: `i` ancorado ao contêiner visual do mapa com respiro da borda; atribuição nativa do Mapbox ocultada integralmente, sem textos reaparecendo na base; hover/foco exibiu as instruções, sem legenda fixa abaixo.
- Correção adicional em 23/08/2026: o filtro de município passou a manter as linhas de pin dos projetos selecionados, evitando o estado vazio no mapa; o tooltip passou a exibir somente a explicação aprovada sobre pontos e associações de localização, sem o contador técnico.
- Correção adicional em 23/08/2026: a coluna `Investimento previsto` da lista de obras passou a manter os valores numéricos para ordenação, preservando a formatação monetária compacta na apresentação e o texto para valores não informados.
- Temas no container: Light e Dark alternados pelas configurações do Streamlit; fundo, sidebar, KPIs, cards e gráfico de situação permaneceram legíveis nos dois temas, com fundo do Plotly transparente.
- Favicon no container: a aba passou a usar o mesmo `favicon.png` compacto do site oficial da Vertere, em vez da logo completa.
- Linguagem no container: textos visíveis revisados para público executivo; termos como `snapshot`, `Gold`, `ingestão`, `recorte filtrado` e `situação original` foram substituídos por descrições de negócio.
- Snapshot e rolagem no container: card exibido sem `ID`, com margem abaixo da barra superior; cabeçalho permaneceu no topo com fundo sólido durante a rolagem até a tabela.
- Repetição normal: `Ingestão skipped` para o mesmo `ingestion_id`; payload de `/data-atualizacao` preservado na Bronze.

## Limitações registradas

- O primeiro comando dbt falhou porque o Compose não informava `--project-dir`; o comando foi corrigido antes da execução válida.
- O rebuild posterior das imagens com Dockerfiles otimizados excedeu o tempo de download externo; as validações válidas foram executadas nos containers já construídos, montando o código atualizado.
- O serviço Streamlit foi reiniciado em container com `frontend/` montado para aplicar a correção enquanto o rebuild limpo aguardava downloads externos; Postgres permaneceu no container original.
- A execução `--force` real começou e persistiu páginas, mas foi encerrada por lentidão da API pública; ela foi marcada como `failed` e não alterou o snapshot atual.
- AC-011 não dispara uma segunda carga nacional artificial contra a API pública; a garantia automatizada cobre isolamento por `ingestion_id`, append-only e preservação de snapshots.

## Conclusão

Implementação, evidências e critérios aceitos. A aprovação humana explícita para `Done` foi confirmada pelo usuário em 23/08/2026; a SPEC-001 está `Done`.
