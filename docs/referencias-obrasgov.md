# Referências de análises e implementações com ObrasGov

**Última revisão:** 21/08/2026

## Fontes atuais

### API oficial

A [documentação OpenAPI atual](https://api-publica.obrasgov.gestao.gov.br/obras/docs) é a fonte de verdade para endpoints, filtros e schemas. O contrato consultado possui projetos, empenhos, execução física, contratos, geometrias, histórico de cancelamento/paralisação, estudos de viabilidade e data de atualização.

O [anúncio oficial da nova API](https://www.gov.br/obrasgov/pt-br/ferramentas-de-gestao-e-transparencia/api-de-dados-abertos-obrasgov-br_novo) informa que o ambiente anterior continua apenas durante a transição, com migração recomendada para o novo ambiente e prazo até 31/08/2026. Este projeto usa somente a API nova.

### Painéis oficiais

O [Painel ObrasGov](https://obrasgov.sistema.gov.br/) explora localização, situação e volume de recursos. A [Consulta Personalizada](https://dd-publico.serpro.gov.br/extensions/painel/ObrasgovbrConsulta.html) oferece visões de projeto, dados gerais, empenho e indicadores.

Aplicação no case:

- priorizar mapa, situação original e investimento;
- separar visão agregada de mercado e detalhe do projeto;
- não interpretar o cadastro como prova de licitação aberta.

## Implementações públicas encontradas

### `obrasgovr`

O pacote [`StrategicProjects/obrasgovr`](https://github.com/StrategicProjects/obrasgovr) fornece uma interface R para a API atual. A implementação e suas vignettes evidenciam:

- paginação explícita com até 200 registros por página;
- registro de metadados de consulta e data de atualização da fonte;
- tipagem de datas;
- retentativas e limitação de requisições;
- preservação das relações um-para-muitos em vez de selecionar apenas o primeiro item.

A vignette [Pagination and nested data](https://strategicprojects.github.io/obrasgovr/articles/pagination-and-nested-data.html) demonstra que executores, fontes de recurso e outras coleções devem ser normalizados separadamente. Essa prática fundamenta os modelos Silver separados e as bridges da Gold.

### MonitoraBSB

O projeto acadêmico [MonitoraBSB](https://unb-mds.github.io/MDS-MonitoraBSB/obras_gov/api/) documenta o uso do ObrasGov para monitoramento de projetos, georreferenciamento, execução física e financeira.

Limitação: a página usa o ambiente e os parâmetros da API anterior. Serve como referência de perguntas analíticas, não como contrato técnico nem como base para nomes de campos.

## Síntese aplicada à modelagem

| Evidência | Decisão adotada |
|---|---|
| API paginada e sujeita a atualização | armazenar execução, totais, página e timestamps |
| relações aninhadas N:N | explodir cada coleção em modelo Silver próprio |
| análise oficial orientada a mapa e situação | criar bridges de localização e dimensão de situação original |
| métricas financeiras distintas | fatos separados e proibição de soma entre naturezas |
| contratos e datas com cobertura parcial | nulabilidade explícita e testes de cobertura como alerta |
| migração da API anterior | usar apenas `api-publica.obrasgov.gestao.gov.br/obras` |

Não foi encontrada uma modelagem dimensional pública da nova API com o mesmo recorte comercial. A modelagem deste projeto deriva do contrato OpenAPI atual, do PRD e dos padrões observados nas implementações acima.
