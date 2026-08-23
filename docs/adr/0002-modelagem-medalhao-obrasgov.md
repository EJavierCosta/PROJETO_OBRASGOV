# ADR 0002 — Modelagem medalhão do ObrasGov

**Status:** Aceita
**Data:** 23/08/2026

## Contexto

A API nova do ObrasGov publica snapshots paginados, recursos independentes e
coleções aninhadas. O repositório coleta oito recursos na mesma execução lógica:
projetos, geometrias, contratos, empenhos, execução física, histórico específico,
estudos e atualização da fonte.

Unir diretamente municípios, fontes de recurso, participantes, contratos,
empenhos e execução multiplicaria linhas e medidas. Também é necessário distinguir
`source_updated_at` de `ingested_at` e preservar execuções falhas para auditoria.

## Decisão

- Persistir uma tabela raw por recurso na Bronze, com payload `jsonb`, página,
  posição, hash, timestamps e `ingestion_id`.
- Manter Bronze append-only; somente uma execução completa, reconciliada e estável
  pode receber `succeeded`.
- Explodir coleções aninhadas em modelos Silver independentes.
- Manter snapshots por `ingestion_id`; `int_obrasgov_current_ingestion` seleciona a
  última execução `succeeded` que contém os oito recursos bem-sucedidos.
- Publicar a Gold como constelação de fatos, dimensões e bridges, com 23 modelos de
  tabela e 18 views `current`.
- Manter `fct_project_snapshot` como entidade de projeto por ingestão. Não criar
  `dim_project` sem uma semântica própria além do snapshot.
- Separar investimento previsto, contratos, empenhos, execução física, eventos de
  situação e estudos em fatos distintos.
- Conformar organizações em `dim_organization`; o papel (`responsible`,
  `transferor`, `recipient`, `executor`) pertence à bridge de participantes.
- Usar CNPJ normalizado como identidade de organização quando válido e nome
  normalizado como fallback.
- Modelar PPA, área de restrição e indicador de foto como relações próprias; não
  promovê-los a medidas nem misturá-los ao fato de projeto.
- Preservar situações e demais rótulos originais da API. O recorte do produto é
  aplicado no `fct_project_snapshot`: CE, Obra e Construção.
- Expor cada relação detalhada por uma view Gold própria, filtrada por um único
  `project_id`, sem juntar fatos filhos entre si.

## Granularidades implementadas

- `fct_project_snapshot`: projeto + ingestão.
- `fct_planned_investment`: projeto + fonte + ingestão.
- `fct_contract`: projeto + contrato + ingestão.
- `fct_commitment`: projeto + chave determinística do empenho + ingestão.
- `fct_physical_execution`: projeto + `id_execucao_fisica` + ingestão.
- `fct_status_event`: projeto + evento-fonte + ingestão.
- `fct_feasibility_study`: projeto + chave determinística do estudo + ingestão.
- bridges: relações de localização, pin, eixo/tipo, participante, PPA, restrição e
  foto em suas próprias granularidades.

## Alternativas rejeitadas

### Tabela única desnormalizada

Rejeitada por causar fanout entre relações 1:N e inflar contagens e valores.

### Bronze filtrada para o Ceará

Rejeitada porque perderia fidelidade da fonte e impediria comparação nacional futura.

### Sobrescrever o estado atual

Rejeitada porque eliminaria rastreabilidade entre ingestões e falhas.

### SCD tipo 2 em todas as dimensões

Adiada. Os fatos snapshot preservam o estado observado com menor complexidade para a
capacidade atual.

## Consequências

- O armazenamento cresce a cada snapshot e ainda não possui política de retenção.
- As views `current` simplificam o consumo sem apagar histórico físico.
- A reconciliação pode seguir da resposta da API até as views e KPIs.
- Fatos filhos com identificadores instáveis dependem de chaves determinísticas e
  monitoramento de colisões.
- Área de restrição e foto continuam declaratórios: não há polígono, imagem ou URL
  derivada.
- A view de cobertura informa presença/ausência dos registros de contrato, empenho,
  execução, histórico e estudo, sem converter ausência em informação negativa.

## Evolução futura

Retenção/particionamento, série temporal entre snapshots, validação territorial,
novos recursos e novos enriquecimentos exigem revisão do contrato e, quando houver
mudança material, nova spec. Nenhuma evolução pode inventar atraso, licitação,
geometria de restrição, conteúdo de foto ou situação de estudo.

## Referência

Detalhamento: [`docs/modelagem-dados.md`](../modelagem-dados.md).
