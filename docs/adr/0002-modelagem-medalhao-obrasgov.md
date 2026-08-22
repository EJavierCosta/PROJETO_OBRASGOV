# ADR 0002 — Modelagem medalhão do ObrasGov

**Status:** Proposta
**Data:** 21/08/2026

## Contexto

O PRD exige ingestão nacional da nova API ObrasGov, arquitetura Bronze/Silver/Gold, PostgreSQL, dbt e star schema. A API é paginada, publica snapshots e contém recursos independentes e coleções aninhadas um-para-muitos. Alguns recursos não oferecem uma chave natural simples.

Unir diretamente executores, fontes de recurso, municípios, contratos e empenhos multiplicaria linhas e valores. Também é necessário distinguir a atualização informada pela fonte da data de ingestão.

## Decisão

- Persistir uma tabela raw por endpoint na Bronze, com payload `jsonb`, página, posição, hash e `ingestion_id`.
- Tornar a Bronze append-only e publicar apenas ingestões completas e reconciliadas.
- Explodir cada coleção aninhada em um modelo Silver separado.
- Manter snapshots por `ingestion_id`; views `current` selecionam a última execução bem-sucedida.
- Modelar a Gold como constelação de fatos com dimensões conformadas e bridges para relações multivaloradas.
- Separar investimento previsto, contratos, empenhos e execução física em fatos distintos.
- Preservar situações originais da API e aplicar o recorte do case somente na Silver/Gold.
- Usar hash determinístico como chave técnica quando a API não fornecer identidade suficiente, sem descartar colisões silenciosamente.

## Alternativas rejeitadas

### Tabela única desnormalizada

Rejeitada por causar fanout entre relações um-para-muitos e inviabilizar reconciliação financeira.

### Bronze já tipada e filtrada para o Ceará

Rejeitada porque perde fidelidade da fonte, impede comparação nacional e mistura ingestão com regra de negócio.

### Sobrescrever o estado atual

Rejeitada porque elimina rastreabilidade entre ingestões e impede explicar mudanças observadas.

### SCD tipo 2 em todas as dimensões

Adiada. Os fatos snapshot já preservam o estado observado e são mais simples para o primeiro incremento.

## Consequências

- O armazenamento cresce a cada snapshot e exigirá política de retenção.
- Consultas atuais permanecem simples por meio das views `current`.
- Reconciliação e auditoria são possíveis desde a resposta da API até cada KPI.
- O dbt terá mais modelos, porém cada um mantém granularidade clara e testes específicos.
- Empenhos e estudos sem identificador estável exigem monitoramento de colisões de chave.

## Referência

Detalhamento: [`docs/modelagem-dados.md`](../modelagem-dados.md).
