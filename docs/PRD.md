# PRD — Inteligência de Obras Públicas para Construção

**Status:** Draft
**Data:** 18/08/2026
**Última revisão:** 21/08/2026

## 1. Contexto

A Vertere AI atua com tecnologia, dados e inteligência artificial no ecossistema GM GROUP. O case será desenvolvido no contexto do braço de construção civil do grupo, usando dados públicos do Obrasgov.br.

O Obrasgov.br registra projetos de investimento em infraestrutura, incluindo obras, projetos, estudos, execução física, dados financeiros, contratos e localização.

## 2. Problema

Gestores comerciais de uma construtora precisam consolidar informações dispersas sobre obras públicas para entender onde estão os investimentos, quais órgãos demandam obras e quais projetos merecem análise comercial.

## 3. Objetivo do produto

Disponibilizar uma visão atualizada do mercado de obras públicas de construção no Ceará, com possibilidade de comparação nacional, permitindo explorar projetos por localização, órgão, tipo, situação, investimento e estágio informado pela fonte.

O produto não terá como objetivo afirmar que uma licitação está aberta nem gerar uma lista completa de oportunidades comerciais.

## 4. Usuário principal

Gerente ou diretor comercial de novos negócios da construtora.

## 5. Perguntas de negócio

- Onde estão concentradas as obras públicas de construção no Ceará?
- Quais municípios, órgãos e tipos de intervenção concentram mais projetos?
- Qual o volume de investimento previsto por região, órgão e situação?
- Quais projetos merecem análise individual pelo time comercial?
- Quais contratos, fornecedores, empenhos e dados de execução estão associados aos projetos selecionados?

## 6. Escopo da entrega do case

- Fonte principal: nova API pública do Obrasgov.br.
- Ingestão Bronze nacional de todos os endpoints; filtros de negócio aplicados na Silver/Gold.
- Natureza da intervenção: `Obra`.
- Espécie da intervenção: `Construção`.
- Recorte principal: `uf_principal = CE`.
- Comparação nacional opcional.
- Snapshot atual, com data de atualização da API e data da ingestão.
- Situações exibidas com os valores originais da API, sem reclassificação comercial automática.
- Visão agregada de mercado e detalhamento de projetos.

### KPIs principais

- **Total de obras:** contagem distinta de `id_projeto_investimento`.
- **Investimento previsto:** soma de `vl_investimento_previsto` nos registros de investimento dos projetos filtrados.
- **Municípios alcançados:** contagem distinta de `cod_ibge` nas geometrias associadas.
- **Obras em execução:** contagem distinta de projetos com `situacao = Em execução`.
- **Distribuição por situação:** contagem dos valores originais de `situacao`, sem reclassificação.

### Filtros

- Município.
- Organização responsável.
- Situação original.
- Eixo, tipo e subtipo da intervenção.
- Faixa de investimento previsto.
- Ano de cadastro.
- Período da data de cadastro, com seleção única: último mês, últimos 3 meses, últimos 6 meses, últimos 12 meses ou ano corrente.

### Detalhe do projeto

Ao selecionar uma obra, o usuário verá identificação, órgão responsável, situação original, município, mapa, eixo/tipo/subtipo, datas previstas e investimento por fonte. Dados de execução física, contratos, fornecedores, empenhos, estudo de viabilidade e histórico serão exibidos quando houver associação na fonte.

## 7. Dados utilizados

### Projeto de investimento

Identificação, descrição, órgão responsável, UF, datas, situação, tipo de intervenção, investimento previsto, beneficiários, BIM, executores, repassadores, tomadores e localização.

### Dados relacionados

- Contratos e fornecedores.
- Empenhos e valores financeiros.
- Execução física.
- Geometria e município.
- Histórico de cancelamento ou paralisação.
- Estudos de viabilidade.

## 8. Modelo analítico

O Gold será uma constelação de fatos, com dimensões conformadas compartilhadas quando fizer sentido.

- `fct_project_snapshot`: uma linha por projeto por ingestão.
- `fct_planned_investment`: uma linha por projeto e fonte de recurso.
- `fct_contract`: uma linha por contrato.
- `fct_physical_execution`: uma linha por registro de execução física.
- `fct_empenho`: uma linha por empenho.
- `fct_status_history`: uma linha por evento de cancelamento ou paralisação.

Dimensões candidatas: projeto, organização, localização, situação, intervenção, fornecedor, fonte orçamentária e data.

## 9. Limitações conhecidas

- A API não informa de forma suficiente se uma licitação está aberta.
- O histórico temporal completo da evolução dos projetos não está disponível.
- Contratos estão associados apenas a parte dos projetos.
- Campos financeiros e de execução podem conter nulos.
- A base também possui projetos, estudos e outras intervenções; por isso o filtro de natureza é obrigatório para a entrega do case.

## 10. Requisitos do case

- Ingestão em Python.
- Transformações em SQL com dbt.
- PostgreSQL.
- Arquitetura Bronze, Silver e Gold.
- Star schema na camada Gold.
- Frontend local em Python com Streamlit, consumindo a Gold em modo somente leitura.
- Duas visões no frontend: visão geral do mercado e detalhe do projeto.
- Transformações de negócio restritas ao dbt; o Streamlit apenas consulta e apresenta dados.
- Ambiente completo via Docker Compose.
- README com execução, decisões, limitações e pontos de melhoria.

### Arquitetura macro

`Obrasgov → ingestão Python → Bronze → dbt staging/intermediate → Silver → dbt marts → Gold → Streamlit`

- Bronze preserva os dados recebidos e metadados da ingestão.
- Silver padroniza, tipa, deduplica e integra os dados necessários.
- Gold publica fatos e dimensões consumidos pelo Streamlit em modo somente leitura.
- A estrutura detalhada do repositório está registrada em `docs/arquitetura.md`.

## 11. Validação preliminar do recorte local

Consulta realizada em 18/08/2026 com `uf_principal = CE`, `natureza_intervencao = Obra` e `especie_intervencao = Construção`:

- 3.202 projetos únicos.
- 1.822 cadastrados, 694 em execução, 589 concluídos, 76 cancelados, 15 inacabados e 6 paralisados.
- 184 municípios identificados por geometria.
- 3.192 projetos com geometria associada.
- 25 organizações responsáveis.
- 3.241 registros de investimento previsto, totalizando aproximadamente R$ 25,15 bilhões.
- 116 projetos com contratos associados, totalizando 189 contratos.
- Datas previstas preenchidas em todos os projetos; datas efetivas preenchidas em aproximadamente 1% dos registros.

Conclusão: o recorte local é suficiente para um dashboard analítico. A baixa cobertura de datas efetivas impede um KPI confiável de atraso; o dashboard deve priorizar distribuição, localização, situação original, investimento previsto e exploração de projetos.

## 12. Versionamento e governança da modelagem

- Git será a fonte de verdade para SQL, YAML, testes e documentação.
- O dbt será usado de forma declarativa para construir Silver e Gold.
- `sources.yml` e `schema.yml` formarão o catálogo, com descrições, linhagem e testes.
- Modelos Gold públicos terão contratos de schema quando estiverem estáveis.
- CI executará `dbt build` nos modelos alterados e dependências afetadas.
- Mudanças incompatíveis poderão criar versões de modelo com janela de depreciação.
- A Bronze será append-only, identificada por `ingestion_id`.
- Schemas PostgreSQL e objetos de infraestrutura serão criados por bootstrap SQL; migrations não serão usadas para a modelagem analítica.

## 13. Decisões pendentes

- Extensão da comparação nacional.
- Estratégia de atualização e idempotência da ingestão.
- Regras de qualidade e critérios de aceite.
