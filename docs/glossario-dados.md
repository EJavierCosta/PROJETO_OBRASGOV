# Glossário de dados

**Última revisão:** 23/08/2026

As definições abaixo refletem a implementação atual e distinguem o que é informado
pela fonte do que é cálculo analítico.

| Termo | Definição no projeto |
|---|---|
| Projeto de investimento | Registro identificado por `id_projeto_investimento`; unidade usada para contar obras. |
| Obra do recorte | Projeto com `uf_principal = CE`, `natureza_intervencao = Obra` e `especie_intervencao = Construção`. |
| Fonte | API pública nova do ObrasGov. |
| Snapshot | Fotografia observada em uma execução completa; não é histórico de eventos. |
| `ingestion_id` | Identificador imutável da execução; separa versões e não é KPI. |
| `source_updated_at` | Atualização declarada pela API em `data-atualizacao`; data de referência do snapshot. |
| `ingested_at` | Término registrado da ingestão; pode diferir da data da fonte. |
| Snapshot atual | Última execução `succeeded` com os oito recursos publicados; única usada pelas views `current`. |
| Ingestão completa | Coleta reconciliada de `data-atualizacao`, `projeto-investimento`, `geometria`, `contrato`, `empenho`, `execucao-fisica`, `historico-situacao-cancelada-paralisada` e `estudo-viabilidade`. |
| `succeeded` | Execução completa, reconciliada e elegível para publicação. |
| `failed` | Execução incompleta ou inconsistente, preservada e excluída das views atuais. |
| `skipped` | Repetição de snapshot lógico já publicado; não recarregada sem `--force`. |
| Bronze | Camada nacional append-only que preserva payloads e metadados de coleta. |
| Silver | Camada dbt de staging/intermediate com tipagem, limpeza, deduplicação e explosão de relações. |
| Gold | Camada dbt de 23 tabelas e 18 views públicas no recorte Ceará/Obra/Construção. |
| Payload raw | JSON recebido da API, preservado sem renomeação na Bronze. |
| View `current` | View Gold filtrada pela última ingestão integral `succeeded`. |
| View Gold pública | Uma das 18 `gold.vw_*_current` publicadas para consumo do frontend; a role do chat recebe as 17 views geráveis e somente colunas públicas da view de metadados. |
| Situação original | Valor de `situacao` recebido da API, sem reclassificação comercial. |
| Obra em execução | Projeto cujo `source_status` coincide exatamente com `Em execução`. |
| Porcentagem de conclusão | `physical_execution_percentage` informado pela fonte na execução física; percentuais ausentes não atendem a filtros de limiar. |
| Investimento previsto | Soma de `investimentos_previstos` por projeto e fonte; não é contrato, empenho, liquidação ou pagamento. |
| Fonte de recurso | Origem informada para uma parcela do investimento previsto. |
| Organização responsável | Valor de `organizacao_resp` normalizado na dimensão de organização. |
| Participante | Organização associada ao projeto por papel explícito da fonte. |
| Papel do participante | Um de `responsible`, `transferor`, `recipient` ou `executor`; permanece na bridge. |
| Eixo, tipo e subtipo | Classificações originais da intervenção. |
| Data de cadastro | `registration_date`, derivada de `dt_cadastro`. |
| Ano de cadastro | `registration_year`, derivado de `ano_cadastro`. |
| Data prevista | `expected_start_date` ou `expected_end_date`, conforme a fonte. |
| Data efetiva | `actual_start_date` ou `actual_end_date`; cobertura limitada e sem KPI de atraso. |
| Geometria | Associação territorial do endpoint `geometria`, com município, IBGE, UF e origem. |
| Município alcançado | Município distinto por `ibge_code` nas associações territoriais selecionadas. |
| Pin | Coordenada pontual aninhada no projeto; não é município principal. |
| Município principal | Não é inferido; o detalhe preserva todos os municípios associados. |
| Fato | Modelo Gold com uma observação ou medida em granularidade definida. |
| Dimensão | Modelo Gold de atributos descritivos ou identidade conformada. |
| Bridge | Relação Gold para coleções multivaloradas sem duplicar medidas. |
| Granularidade | O que uma linha representa; por exemplo, `fct_planned_investment` é projeto + fonte + ingestão. |
| Fanout | Multiplicação de linhas ao juntar relações 1:N, inflando contagens ou valores. |
| Deduplicação | Remoção de cópias dentro da mesma `ingestion_id`; snapshots diferentes permanecem. |
| Dados parciais | Cobertura incompleta informada pela ausência de registros, coordenadas ou valores; não é preenchida por inferência. |
| Cobertura | Indicador da presença de registros de contrato, empenho, execução física, histórico ou estudo no snapshot atual. |
| Total de obras | `count(distinct project_id)` no recorte filtrado. |
| Municípios alcançados | `count(distinct ibge_code)` nas localizações dos projetos selecionados. |
| Distribuição por situação | Contagem de projetos agrupada pelo texto original de `source_status`. |
| Execução física | Registro da API por `id_execucao_fisica`; não é percentual agregado entre snapshots. |
| Histórico de situação | Recurso específico de cancelamento/paralisação; não é uma linha histórica completa da situação. |
| Estudo de viabilidade | Registro com tipo e especificação; a fonte observada não fornece status, data ou conclusão. |
| PPA | Tipo e descrição recebidos em `ppas`; não implica programa orçamentário além do texto. |
| Área de restrição | Texto recebido em `areas_restricao`; não é polígono nem impedimento jurídico calculado. |
| Indicador de foto | `ind_foto` recebido em `fotos`; não contém imagem ou URL. |
| Chat analítico | Página opcional da SPEC-003 para perguntas sobre o snapshot Gold atual. |
| Provider LLM | Adapter com contrato independente do SDK; o provider de produção da POC é Gemini. |
| `GEMINI_MODEL` | Modelo selecionado por ambiente. `.env.example`, `.env` local, fallback Python e fallback do Compose usam `gemini-3.5-flash-lite`. |
| SQL aprovado | `SELECT` ou CTE de leitura que passou pelo SQLGuard, allowlist e limites. |
| Catálogo gerável | 17 das 18 views públicas; `vw_snapshot_metadata_current` é consultada apenas pelo adaptador estático. |
| Resultado Gold limitado | Resultado sem colunas internas, limitado antes de ser enviado ao provider. |
| Limites do chat | Pergunta 4.000 caracteres; histórico de seis turnos; provider 30 s; resultado do provider 100 linhas, 20 colunas, 32.000 bytes e 1.000 caracteres por célula; executor 5 s, 100 linhas, 20 colunas, 2.000 células e 1 MiB. |
| SPEC-001 | Pipeline e visão geral do recorte Ceará; capacidade concluída em 23/08/2026. |
| SPEC-002 | Detalhe completo por projeto; implementação em `Verifying`. |
| SPEC-003 | POC de chat Gemini opt-in e SQL seguro; implementação em `Done` após aprovação em 23/08/2026. |
