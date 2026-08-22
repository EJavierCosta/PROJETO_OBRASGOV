# Glossário de dados

**Última revisão:** 22/08/2026

Os termos técnicos abaixo descrevem a implementação interna. As definições de negócio indicam como interpretar os dados no painel.

| Termo | Definição no projeto |
|---|---|
| Projeto de investimento | Registro identificado por `id_projeto_investimento`; é a unidade usada para contar obras. |
| Obra do recorte | Projeto com `natureza_intervencao = Obra`, `especie_intervencao = Construção` e `uf_principal = CE`. |
| Fonte | API pública do ObrasGov que informa projetos, atualização, geometrias e valores previstos. |
| Snapshot | Fotografia completa observada em uma execução da coleta; não é o histórico de eventos da obra. |
| `ingestion_id` | Identificador interno de uma execução. Serve para separar versões, auditar cargas e não é um KPI. |
| `source_updated_at` | Data/hora de atualização declarada pela API em `/data-atualizacao`; é a data de referência dos dados. |
| `ingested_at` | Data/hora em que a execução foi concluída e registrada; pode ser diferente da data da fonte. |
| Snapshot atual | Última execução com status `succeeded`; é a única versão usada pelas views `current`. |
| Ingestão completa | Coleta dos três recursos da SPEC-001 com todas as páginas e quantidades reconciliadas. |
| `succeeded` | Execução completa e publicada como candidata a snapshot atual. |
| `failed` | Execução incompleta ou inconsistente, preservada para auditoria e excluída das views atuais. |
| `skipped` | Tentativa não recarregada porque o mesmo snapshot lógico já estava publicado; `--force` permite nova tentativa. |
| Bronze | Camada que preserva nacionalmente os payloads originais e os metadados de coleta. |
| Silver | Camada que tipa, limpa, deduplica dentro da execução e separa relações multivaloradas. |
| Gold | Camada analítica do recorte do Ceará, com fatos, dimensões, relações e views para consumo. |
| Payload raw | Registro JSON recebido da API, mantido sem renomeação na Bronze. |
| View `current` | Interface Gold que esconde snapshots antigos e expõe somente a última execução `succeeded`. |
| Situação original | Valor de `situacao` informado pela fonte, sem reclassificação comercial. `Em execução` é contado somente por correspondência exata. |
| Investimento previsto | Soma dos valores de `investimentos_previstos` por projeto e fonte de recurso. É estimativa, não valor contratado ou pago. |
| Fonte de recurso | Origem informada pela API para cada parcela do investimento previsto. |
| Organização responsável | Órgão ou entidade informado em `organizacao_resp` como responsável pelo projeto. |
| Eixo, tipo e subtipo | Classificações originais da intervenção usadas para filtrar e segmentar as obras. |
| Data de cadastro | `registration_date`, derivada de `dt_cadastro`; indica quando o projeto foi cadastrado na fonte. |
| Ano de cadastro | `registration_year`, derivado de `ano_cadastro`; permite segmentação anual. |
| Data prevista | `expected_start_date` ou `expected_end_date`; prazo planejado informado pela fonte. |
| Data efetiva | `actual_start_date` ou `actual_end_date`; data ocorrida informada pela fonte. A cobertura é limitada e não sustenta KPI de atraso. |
| Geometria | Associação territorial do endpoint `/geometria`, com município, código IBGE, UF e origem. |
| Município alcançado | Município distinto identificado por `ibge_code` nas associações das obras selecionadas. |
| Pin | Coordenada pontual aninhada no projeto, separada da geometria municipal. |
| Coordenada ambígua | Situação com nenhum pin utilizável ou mais de um par distinto de latitude/longitude; a view deixa latitude e longitude nulas. |
| Localização principal | `uf_principal` do projeto. Não substitui os municípios associados pelas geometrias. |
| Fato | Modelo Gold que registra uma medida ou observação em uma granularidade definida, como projeto por ingestão. |
| Dimensão | Modelo Gold de atributos para descrever projetos, organizações, intervenções, fontes, localizações ou classificações. |
| Bridge | Relação Gold usada quando um projeto pode ter vários municípios, pins ou classificações, evitando duplicar medidas. |
| Granularidade | O que uma linha representa. Exemplo: `fct_planned_investment` representa projeto + fonte + ingestão. |
| Fanout | Multiplicação indevida de linhas ao juntar relações multivaloradas, inflando contagens ou valores. |
| Deduplicação | Remoção de cópias exatas dentro da mesma `ingestion_id`; mudanças entre snapshots não são apagadas. |
| Dados parciais | Aviso de cobertura incompleta, como municípios sem coordenada ou investimentos sem valor; não significa que o projeto foi descartado. |
| Total de obras | Contagem distinta de projetos no conjunto filtrado. |
| Investimento previsto total | Soma do valor previsto uma vez por projeto no conjunto filtrado. |
| Obras em execução | Projetos cujo status original é exatamente `Em execução`. |
| Distribuição por situação | Contagem de projetos agrupada pelo status original da API. |
| Estudo de viabilidade | Registro associado ao projeto com tipo e especificação; a API atual não fornece status, data ou conclusão do estudo. |
