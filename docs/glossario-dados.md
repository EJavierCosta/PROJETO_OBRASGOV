# Glossário de dados

**Última revisão:** 21/08/2026

| Termo | Definição no projeto |
|---|---|
| Projeto de investimento | Entidade identificada por `id_projeto_investimento`; pode representar diferentes naturezas de intervenção. |
| Obra do case | Projeto com natureza `Obra`, espécie `Construção` e UF principal `CE`. |
| Snapshot | Estado observado dos dados em uma ingestão concluída. Não implica histórico completo da fonte. |
| `source_updated_at` | Data/hora informada pelo endpoint `/data-atualizacao`. |
| `ingested_at` | Data/hora em que o pipeline recebeu o registro. |
| Ingestão completa | Execução `succeeded`, com todas as páginas e contagens reconciliadas. |
| Situação original | Valor de `situacao` fornecido pela API, sem reclassificação comercial. |
| Organização responsável | Organização principal informada no projeto. |
| Repassador | Organização que repassa recursos ao projeto. |
| Tomador | Organização que recebe os recursos. |
| Executor | Organização que executa a intervenção. |
| Fornecedor | Parte associada a um contrato; não é automaticamente o executor do projeto. |
| Investimento previsto | Valor planejado em `investimentos_previstos`, segmentado por fonte de recurso. |
| Empenhado | Valor reservado no orçamento por empenho; não equivale a pagamento. |
| Liquidado | Valor cuja entrega ou obrigação foi reconhecida. |
| Pago | Valor efetivamente pago segundo o registro de empenho. |
| Valor contratado | Valor de contrato; não deve ser somado ao investimento previsto como se fosse a mesma métrica. |
| Execução física | Registro de avanço percentual e datas da execução da intervenção. |
| Geometria | Associação territorial do endpoint `/geometria`; no modelo atual contém município e UF. |
| Pin | Coordenada pontual aninhada no projeto, usada no mapa. |
| Localização principal | `uf_principal` do projeto; pode coexistir com mais de um município associado. |
| Bridge | Tabela que representa relação multivalorada sem duplicar medidas de fatos. |
| Fanout | Multiplicação indevida de linhas e valores ao unir duas relações um-para-muitos. |
| Chave natural | Identificador de negócio fornecido pela fonte ou composto por campos da fonte. |
| Chave substituta | Hash determinístico usado para relacionamento dimensional. |
| Bronze | Dados recebidos, append-only, com payload e metadados de ingestão. |
| Silver | Dados tipados, deduplicados e normalizados por granularidade. |
| Gold | Fatos, dimensões, bridges e views próprias para consumo analítico. |
| Current view | View que expõe somente a última ingestão completa. |
