# Verificação — SPEC-002

**Status:** Verifying
**Data:** 23/08/2026
**Aprovação para Done:** Pendente

| Critério | Procedimento ou comando | Resultado | Evidência |
|---|---|---|---|
| AC-001 | AppTest e smoke test da navegação por projeto | Validado no escopo | `tests/frontend/test_smoke.py: 23 passed; health/root HTTP 200` |
| AC-002/AC-003 | Testes de reconciliação e falha dos novos endpoints | Validado no escopo | `pytest -q -p no:cacheprovider: 154 passed; coleta real de 8 recursos concluída` |
| AC-004 a AC-006 | `dbt build` e testes singulares | Validado | `37 modelos de tabela, 18 views e 180 testes; PASS=235 WARN=0 ERROR=0; assert_spec_002_integrity PASS` |
| AC-007 a AC-010 | Testes e inspeção visual do Streamlit | Validado | `tests/frontend/test_smoke.py: 23 passed; Chrome headless desktop/mobile; sem overflow horizontal` |
| AC-011 | Reconciliação de amostras reais Bronze → Silver → Gold | Validado | `ingestion_id 469701dc-d03e-43b8-b6de-8dd3f1713f33; Gold current reconciliado` |
| AC-012 | Execução completa via Docker Compose | Validado com limitação de orquestração | `ingestion run + dbt run sequenciais; ambos código 0` |
| AC-013 | Inspeção de ausência de histórico reconstruído ou inferido | Validado | `datas e estados somente da API; sem derivação de atraso` |
| AC-014 | Reconciliação dos eventos-fonte com o agrupamento semântico e expansão da interface | Validado | `IDs-fonte preservados; status agrupado por chave semântica` |
| AC-015 | Reconciliação dos totais e linhas individuais de empenho | Validado | `medidas separadas; totais e empenhos individuais no detalhe` |
| AC-016 | Isolamento de uma obra e exibição de todos os contratos distintos | Validado | `project_id parametrizado e ordenação determinística` |
| AC-017 | Reconciliação da contagem, tabela e expansão individual dos contratos | Validado | `fct_contract/current view e expansão individual` |
| AC-018 | Reconciliação dos estudos e ausência de campos não fornecidos | Validado | `fct_feasibility_study; somente tipo/especificação recebidos` |
| AC-019 | Deduplicação e apresentação de todos os registros distintos de execução física | Validado | `id_execucao_fisica distinto; source_record_count auditável` |
| AC-020 | Reconciliação de todos os municípios e pins da obra na lista e no mapa | Validado | `bridge_project_location e pontos completos sem inventar coordenadas` |
| AC-021 | Reconciliação do total de investimento previsto com a abertura por fonte | Validado | `fct_planned_investment e view current por fonte` |
| AC-022 | Reconciliação de participantes por papel e chave conformada | Validado | `roles, nome/CNPJ e dim_organization conformados` |
| AC-023 | Reconciliação de contexto, classificações, PPA, restrições e indicador de foto | Validado | `views Gold current e seções correspondentes no Streamlit` |
| AC-024 | Inspeção das datas previstas e efetivas sem indicadores derivados | Validado | `datas exibidas separadamente; sem percentual/atraso agregado` |
| AC-025 | Teste de divergência entre indicador e registros de estudo | Validado | `vw_project_coverage_current e aviso de divergência` |

## Limitações reproduzíveis

- O runtime do navegador em aplicativo falhou ao carregar os assets do kernel em duas tentativas (`os error 3`). A inspeção visual foi concluída por Chrome headless local; o bloqueio limita somente o navegador integrado do aplicativo.
- `docker compose up --build --abort-on-container-exit --exit-code-from dbt ingestion dbt` encerra o serviço `dbt` quando a ingestão termina com sucesso. O fluxo sequencial `docker compose run` foi executado com código 0 em cada etapa.
- `pytest` em Windows emitiu `PytestCacheWarning` por acesso negado ao cache.
- Na validação documental de 23/08/2026, `pytest -q -p no:cacheprovider` terminou com 154 testes aprovados; a opção evita o aviso de cache do Windows e não altera o escopo dos testes.
- O `dbt build` registra deprecações do adaptador sem falhas; o resultado final foi `PASS=235 WARN=0 ERROR=0` para 37 modelos de tabela, 18 views e 180 testes.
- Após a recriação do container Postgres, a primeira execução do `dbt build` encontrou o papel ausente `obrasgov_chat` em quatro grants de views. Os scripts versionados `infra/postgres/initdb/00_roles.sql` e `infra/postgres/initdb/20_grants.sql` foram reaplicados idempotentemente; a segunda execução terminou com `PASS=235 WARN=0 ERROR=0`.
- Em 23/08/2026, os logs reproduziram `AttributeError` após o processo Streamlit manter `frontend.gold` antigo em memória enquanto `project_detail.py` já estava atualizado. O container frontend foi reiniciado sem alterar banco ou dados; a nova instância iniciou com health HTTP 200 e sem nova ocorrência de `AttributeError`.
- Após a recriação do frontend, o log também pode registrar `MediaFileStorageError` para um identificador de mídia antigo durante a primeira navegação; a logo, a rota de detalhe e o card de localização carregaram normalmente, sem `AttributeError`.
- A navegação automática do Streamlit no diretório `pages/` foi desativada por configuração; a validação Docker confirmou logo presente, menu superior customizado presente e os itens `streamlit app`/`overview` ausentes.

## Evidências de validação

- Em 22/08/2026, o OpenAPI informou 71.595 linhas em `/execucao-fisica` e 7.930 em `/historico-situacao-cancelada-paralisada`.
- Na mesma data, a API informou 7.622 contratos, 89.388 empenhos e 77.975 estudos de viabilidade.
- Contrato fornece `id_contrato`; empenho e estudo de viabilidade não fornecem identificador próprio e exigem chave determinística com teste de colisão.
- O cruzamento da API com a Gold atual encontrou obras do dashboard com 2, 3, 4, 16 e até 43 contratos distintos, confirmando a cardinalidade projeto 1:N contrato.
- Nas primeiras 2.000 linhas de execução, 74 projetos tinham múltiplas linhas, mas nenhum apresentou mais de uma data de atualização ou percentual; três projetos inspecionados repetiam exatamente o mesmo `id_execucao_fisica` duas ou três vezes.
- O projeto `1211.13-97` retornou 399 linhas de histórico de situação, 399 IDs, 354 eventos semânticos datados e os estados `Cancelada` e `Paralisada`.
- Outros quatro projetos amostrados retornaram de 93 a 122 IDs para um único evento semântico, evidenciando duplicidade relevante na fonte.
- No snapshot atual do recorte, 3.207 obras têm executor, 3.090 têm repassador, 822 têm tomador, 402 têm PPA, 1.916 têm área de restrição e 10 têm indicador de foto.
- As cardinalidades máximas observadas por obra foram 3 repassadores, 2 tomadores, 2 executores, 3 PPAs, 3 áreas de restrição e 1 indicador de foto.
- Entre 10.326 linhas de participantes, foram observados 384 identificadores distintos com 14 dígitos, 4.308 linhas sem CNPJ de 14 dígitos e 23 nomes normalizados distintos usados como fallback. Nenhum identificador de 14 dígitos apresentou nomes divergentes no snapshot.
- A coleção `fotos` forneceu somente `ind_foto = SIM`; não foram fornecidos arquivo, URL ou metadados de imagem.
- A amostra oficial confirmou os campos próprios de repassador, tomador e executor, validando que papel pertence à relação projeto-organização e não à organização isolada.
- O OpenAPI oficial confirmou filtro por `id_projeto_investimento` nos cinco endpoints relacionados. Para `5543.23-00`, a API retornou 43 contratos, 59 empenhos e 1 execução física, sustentando exibição completa com rolagem ou expansão.
- As consultas foram somente leitura e não persistiram respostas no projeto ou no banco.

## Evidências de execução ponta a ponta

- `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`: 154 passed.
- `.venv\Scripts\python.exe -m pytest -q tests\frontend\test_smoke.py`: 23 passed, 1 warning de cache no Windows.
- Regressão da navegação `Lista de obras → Detalhes`: `tests/frontend/test_smoke.py: 23 passed`; a seleção é preservada em `session_state` porque `st.switch_page` limpa query params, e a página restaura `project_id` na URL.
- `.venv\Scripts\python.exe -m ruff check .`: All checks passed.
- `docker compose run --rm --build ingestion`: API HTTP 200; execução idempotente ignorou a ingestão corrente `469701dc-d03e-43b8-b6de-8dd3f1713f33`.
- `docker compose --env-file .env.example build frontend`: imagem frontend reconstruída com `uv.lock` sincronizado ao manifesto existente; execução terminou com sucesso.
- Fluxo visual local via Chrome headless: navegação visão geral → detalhes → seletor → projeto abriu `project_id=31480.23-65`; back link visível no desktop/mobile e `innerWidth=390, document.documentElement.scrollWidth=390`.
- Após reconstruir o frontend, a rota Docker `project_detail?project_id=31480.23-65` abriu a obra real; Chrome headless confirmou nome, `project_id` e ausência de `AttributeError`.
- Em 23/08/2026, a primeira dobra foi revisada contra `assets/design/dashboard-detalhe-projeto-vertere.png`: navegação superior, título, status, atualização, três KPIs e localização/identificação seguem a hierarquia da referência; campos exibidos foram conferidos contra as views Gold `current`.
- Em 23/08/2026, a revisão de espaçamento foi validada no Docker: cabeçalhos de seção compactados, 12px entre situação e KPIs, 12px entre KPIs e localização, investimento sem folga vertical excessiva e `scrollWidth=innerWidth` no desktop.
- Em 23/08/2026, o card de localização foi revisado no Docker: 2 registros territoriais foram apresentados em cartões compactos, 1 ponto foi mantido no mapa, o `i` exibiu tooltip em hover e foco, e o texto confirmou que registros sem coordenadas permanecem listados; desktop e viewport de 390px ficaram sem overflow.
- Em 23/08/2026, o cabeçalho foi revisado no Docker: as tags `Registro oficial` e `Cadastrada` permaneceram na mesma linha; o card `Total previsto` ficou com 82,8px de altura no projeto `31480.23-65`, sem alteração dos valores Gold; desktop e viewport de 390px ficaram sem overflow.
- Em 23/08/2026, os cartões financeiros e de execução foram revisados no Docker: `Total previsto` ficou afastado da borda com 82,8px de altura, `Percentual informado` ficou com 116,9px de largura, a distância até a tabela caiu para 23,2px, cada execução manteve seu card próprio e o viewport de 390px ficou sem overflow.
- Em 23/08/2026, o card interno de cada execução recebeu espaçamento inferior próprio: no projeto `5543.23-00`, o cartão `Percentual informado` terminou 5,8px antes da borda do registro e manteve 23,2px de distância da tabela; viewport desktop sem overflow e sem `AttributeError`.
- Em 23/08/2026, o texto auxiliar redundante `Um card por registro` foi removido do indicador, mantendo apenas o percentual recebido pela fonte; Docker confirmou o cartão sem o texto e sem `AttributeError`.
- `docker compose run --rm --no-deps dbt build --project-dir /app/dbt --profiles-dir /app/dbt --target-path /tmp/dbt-target`: 37 modelos de tabela, 18 views e 180 testes; `PASS=235 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=235`.
- A carga real da API publicou os oito recursos: projetos 130.147, geometrias 215.146, contratos 7.622, empenhos 89.388, execuções físicas 71.595, situações 7.930, estudos 77.975 e data de atualização 1; todas as páginas recebidas e a ingestão terminou `succeeded`.
- As views correntes usam uma única ingestão: `469701dc-d03e-43b8-b6de-8dd3f1713f33`, com `source_updated_at=2026-08-22T00:00:00Z`. Gold current: 3.207 projetos, 189 contratos, 2.534 empenhos, 1.497 execuções físicas e 336 estudos. Contagens históricas de fatos permanecem auditáveis, mas não são usadas pelo detalhe.
- A cobertura Gold separa `source_record_count` (linhas recebidas) de `display_record_count` (registros exibidos); execução física usa um cartão por `id_execucao_fisica`, e o teste `assert_spec_002_integrity` impede cobertura invertida, órfãos e duplicidade semântica de situação.
- Reconciliação física: Bronze no escopo 1.499 linhas/1.497 IDs; Gold 1.497 cards/1.497 IDs e `sum(source_record_count)=1499`.
- Amostras reais: projeto `5543.23-00` com 43 contratos distintos e 43 valores globais informados; `42009.23-20` com situação `Paralisada` e ID-fonte `346839`; `105830.23-99` com estudos Ambiental, Econômica e Social.
- Localizações: 10.226 registros, 4.683 pontos completos e 5.189 registros com `geometry_origin`; participantes atuais por papel: executor 3.209, recipient 823, responsible 3.207 e transferor 3.093.
- Medidas financeiras permanecem separadas: 2.534 empenhos com `valor_empenho` e 643 com `rpinscrito`; o frontend exibe empenho e restos a pagar em tabelas distintas.
- O upgrade aditivo `infra/postgres/upgrade/002_spec_002.sql` foi aplicado com código 0. O frontend não possui USAGE em Bronze/Silver e possui USAGE em Gold.
- A função `load_project_detail` foi confirmada no checkout e no container reconstruído; o teste `pytest -q tests/frontend/test_smoke.py -k project_detail` terminou com `4 passed, 15 deselected`. A correção operacional é reiniciar/recriar o frontend após atualizar a imagem, evitando módulo Streamlit obsoleto em memória.
- A revisão Sol foi somente leitura; os achados comprovados foram corrigidos e revalidados. Não houve push, deploy, publicação nem marcação de `Done`.

## Conclusão

Implementação e validação ponta a ponta concluídas com evidências reproduzíveis. A SPEC-002 permanece em `Verifying`; a inspeção visual desktop/mobile foi validada por Chrome headless local. Aguarda-se aprovação humana explícita para mover `Verifying` para `Done`.
