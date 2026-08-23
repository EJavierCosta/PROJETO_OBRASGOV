# Referências de análises e implementações com ObrasGov

**Última revisão:** 23/08/2026

## Fontes oficiais usadas como contrato

A [documentação OpenAPI da API nova](https://api-publica.obrasgov.gestao.gov.br/obras/docs)
é a fonte de verdade para endpoints, envelopes, filtros e schemas. O repositório
usa a base `https://api-publica.obrasgov.gestao.gov.br/obras` e registra estes
recursos no código de ingestão:

`data-atualizacao`, `projeto-investimento`, `geometria`, `contrato`, `empenho`,
`execucao-fisica`, `historico-situacao-cancelada-paralisada` e
`estudo-viabilidade`.

O [anúncio oficial da nova API](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo)
registra a migração do ambiente anterior. A implementação atual usa somente o
ambiente novo; referências ao contrato antigo não definem nomes de campos nem
comportamento do pipeline.

Os [painéis oficiais do ObrasGov](https://obrasgov.sistema.gov.br/) e a
[Consulta Personalizada](https://dd-publico.serpro.gov.br/extensions/painel/ObrasgovbrConsulta.html)
servem como referência de perguntas sobre localização, situação, recursos,
empenhos e indicadores. Eles não são usados como fonte de dados do pipeline.

## Implementações públicas consultadas

### `obrasgovr`

O pacote [`StrategicProjects/obrasgovr`](https://github.com/StrategicProjects/obrasgovr)
e a vignette [Pagination and nested data](https://strategicprojects.github.io/obrasgovr/articles/pagination-and-nested-data.html)
foram consultados para confirmar práticas de:

- paginação explícita;
- registro de atualização da fonte e metadados da consulta;
- tipagem de datas;
- retentativas limitadas;
- preservação de relações 1:N em modelos separados.

Essas referências apoiam a Bronze append-only, a reconciliação de páginas e a
explosão independente de investimentos, participantes, localidades e demais
coleções. Não definem o schema local.

### MonitoraBSB

O projeto [MonitoraBSB](https://unb-mds.github.io/MDS-MonitoraBSB/obras_gov/api/)
foi usado como referência de perguntas de monitoramento, georreferenciamento e
execução física/financeira. A página documenta a API anterior e, portanto, não é
contrato técnico para este repositório.

## Aplicação na capacidade entregue

| Evidência | Aplicação implementada |
|---|---|
| API paginada e sujeita a atualização | oito recursos reconciliados por ingestão; `source_updated_at` validado antes/depois |
| Payloads e snapshots | Bronze raw append-only com `ingestion_id`, páginas, hashes e status |
| Relações aninhadas N:N | Silver separada e Gold em fatos, dimensões e bridges |
| Análises oficiais de mapa e situação | views de localização e distribuição com valores originais |
| Medidas financeiras distintas | investimento, contratos e empenhos em fatos/views próprios |
| Cobertura parcial | nulos preservados e `vw_project_coverage_current` sinaliza presença/ausência dos cinco recursos detalhados |
| Recorte do produto | Gold filtra CE, `Obra` e `Construção`; a ingestão continua nacional |
| Consumo seguro | Streamlit lê 18 views Gold; chat usa role dedicada e SQLGuard sobre 17 views geráveis |

Não foi encontrada uma modelagem dimensional pública da API nova com o mesmo recorte
comercial. A modelagem local deriva do contrato OpenAPI, do PRD, do contexto de
domínio e das evidências de implementação; nomes e granularidades devem ser
confirmados no código/dbt local.

## Evolução futura

As referências não justificam inferir licitação aberta, atraso, prioridade
comercial, município principal, geometria de restrição, conteúdo de foto ou status
de estudo. Essas capacidades exigem campo publicado, nova fonte ou nova decisão.

Possíveis evoluções separadas da entrega atual:

- validação territorial com referência oficial e classificação de outliers;
- histórico temporal explícito entre snapshots e política de retenção;
- comparação nacional no frontend, agendamento e operação em nuvem;
- enriquecimentos e fontes adicionais com contrato documentado;
- autenticação, rate limiting e governança do chat.
