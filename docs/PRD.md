# PRD — Inteligência de Obras Públicas para Construção

**Status:** Em verificação — capacidade da SPEC-001 implementada; aprovação humana para Done pendente
**Data:** 18/08/2026
**Última revisão:** 22/08/2026

## 1. Contexto

A Vertere AI atua com tecnologia, dados e inteligência artificial no ecossistema GM GROUP. O case será desenvolvido no contexto do braço de construção civil do grupo, usando dados públicos do Obrasgov.br.

O Obrasgov.br registra projetos de investimento em infraestrutura, com situação, investimento previsto e localização, entre outros campos. A capacidade atual usa a API pública para construir um snapshot nacional e disponibilizar o recorte de obras de construção do Ceará.

## 2. Problema

Gestores comerciais de uma construtora precisam consolidar informações dispersas sobre obras públicas para entender onde estão os investimentos, quais órgãos demandam obras e quais projetos merecem análise comercial.

## 3. Objetivo do produto

Disponibilizar uma visão atualizada do mercado de obras públicas de construção no Ceará, permitindo explorar projetos por localização, órgão, tipo, situação, investimento e data de cadastro informados pela fonte.

A comparação nacional, o detalhamento completo do projeto e os enriquecimentos operacionais permanecem evoluções futuras; não fazem parte da capacidade entregue na SPEC-001.

O produto não terá como objetivo afirmar que uma licitação está aberta nem gerar uma lista completa de oportunidades comerciais.

## 4. Usuário principal

Gerente ou diretor comercial de novos negócios da construtora.

## 5. Perguntas de negócio

- Onde estão concentradas as obras públicas de construção no Ceará?
- Quais municípios, organizações e tipos de obra concentram mais projetos?
- Qual o volume de investimento previsto por município, organização e situação?
- Quais obras merecem análise individual pelo time comercial a partir da lista filtrada?

Contratos, fornecedores, empenhos e dados de execução permanecem perguntas de uma etapa futura, fora da capacidade atual.

## 6. Escopo da entrega do case

### Capacidade entregue na SPEC-001

- Fonte principal: nova API pública do Obrasgov.br.
- Ingestão nacional paginada de `/data-atualizacao`, `/projeto-investimento` e `/geometria`; filtros de negócio aplicados na Silver/Gold.
- Natureza da intervenção: `Obra`.
- Espécie da intervenção: `Construção`.
- Recorte principal: `uf_principal = CE`.
- Snapshot atual, com data de atualização da API e data da ingestão.
- Situações exibidas com os valores originais da API, sem reclassificação comercial automática.
- Fluxo local reproduzível em serviços Docker Compose separados para PostgreSQL, ingestão Python, dbt e Streamlit.
- Bronze append-only, Silver tipada e deduplicada, e Gold dimensional consumida pelo frontend em modo somente leitura.
- Visão geral executiva do mercado, com KPIs, filtros, mapa, distribuição por situação e tabela de obras.
- A navegação de detalhe existe como placeholder informativo; o detalhe completo do projeto ainda não foi entregue.

### KPIs principais

- **Total de obras:** contagem distinta de `id_projeto_investimento`.
- **Investimento previsto:** soma dos valores de investimento previsto por fonte dos projetos filtrados.
- **Municípios alcançados:** contagem distinta de `cod_ibge` nas localizações associadas.
- **Obras em execução:** contagem distinta de projetos com `situacao = Em execução`.
- **Distribuição por situação:** contagem dos valores originais de `situacao`, sem reclassificação.

Os quatro KPIs são recalculados para o recorte filtrado; investimento previsto não é combinado com valores contratados, empenhados, liquidados ou pagos.

### Filtros

- Município.
- Organização responsável.
- Situação da obra.
- Área de atuação, tipo de obra e detalhamento do tipo.
- Faixa de investimento previsto.
- Ano de registro.
- Período de registro, com seleção única de `Sem filtro`, último mês, últimos 3 meses, últimos 6 meses, últimos 12 meses ou ano corrente.

O período usa `registration_date` e a data de atualização do snapshot atual como referência; registros sem data ficam fora de um período definido.

### Componentes da visão geral

- KPIs de total de obras, investimento previsto, municípios alcançados e obras em execução.
- Mapa de municípios com coordenadas disponíveis; localizações ausentes são sinalizadas como dados parciais.
- Gráfico de barras da distribuição por situação original.
- Tabela filtrada com obra, município, organização responsável, situação e investimento previsto.
- Linguagem executiva, cabeçalho com datas de referência e atualização, identidade visual Vertere e suporte legível aos temas claro e escuro.

### Detalhe do projeto — fora da capacidade atual

O detalhe completo deverá exibir identificação, organização responsável, situação, município, mapa, eixo/tipo/subtipo, datas previstas e investimento por fonte. Dados de execução física, contratos, fornecedores, empenhos, estudo de viabilidade e histórico somente poderão ser exibidos após ingestão e modelagem específicas; não foram carregados na SPEC-001.

## 7. Dados utilizados

### Recursos usados na SPEC-001

`/data-atualizacao`, `/projeto-investimento` e `/geometria`, preservando payloads e metadados de ingestão na Bronze. O recorte usa identificação, descrição, organização responsável, UF, datas, situação, intervenção, investimento previsto e localização.

### Dados relacionados efetivamente modelados

- Investimento previsto por fonte de recurso.
- Geometria, município e coordenadas quando disponíveis.
- Eixo, tipo e subtipo de intervenção.

Contratos, fornecedores, empenhos, execução física, histórico de situação e estudos de viabilidade permanecem fora do carregamento atual.

## 8. Modelo analítico

Na capacidade atual, o Gold publica uma constelação mínima de fatos, dimensões, bridges e views atuais.

- `fct_project_snapshot`: uma linha por projeto por ingestão.
- `fct_planned_investment`: uma linha por projeto e fonte de recurso.
- Dimensões e bridges mínimas de organização, localização, intervenção, eixo/tipo/subtipo, fonte de recurso e coordenadas.
- Views Gold atuais para visão de mercado, investimentos, localização, distribuição por situação e metadados do snapshot.

O frontend consulta somente as views Gold da última ingestão bem-sucedida. Fatos de contratos, execução física, empenhos e histórico não fazem parte desta modelagem.

## 9. Limitações conhecidas

- A API não informa de forma suficiente se uma licitação está aberta.
- O frontend atual consome somente a última ingestão bem-sucedida; a retenção de snapshots não equivale a uma série histórica pronta para análise.
- Parte das localizações não possui coordenadas e parte dos investimentos previstos não possui valor; o dashboard sinaliza dados parciais.
- A baixa cobertura de datas efetivas impede um KPI confiável de atraso.
- Contratos, fornecedores, empenhos, execução física, histórico e estudos não foram ingeridos nesta fatia.
- A base também possui projetos, estudos e outras intervenções; por isso o filtro de natureza e espécie é obrigatório para o recorte do case.

## 10. Requisitos do case

- Ingestão em Python em container próprio.
- Transformações em SQL com dbt em container próprio.
- PostgreSQL em container próprio.
- Arquitetura Bronze, Silver e Gold.
- Modelo dimensional na camada Gold.
- Frontend local em Python com Streamlit em container próprio, consumindo a Gold em modo somente leitura.
- Visão geral do mercado implementada; detalhe do projeto permanece como etapa futura.
- Transformações de negócio restritas ao dbt; o Streamlit apenas consulta e apresenta dados.
- Ambiente completo via Docker Compose.
- README com execução, decisões, limitações e pontos de melhoria.

### Arquitetura macro

`Obrasgov → ingestão Python → Bronze → dbt staging/intermediate → Silver → dbt marts → Gold → Streamlit`

- Bronze preserva os dados recebidos e metadados da ingestão.
- Silver padroniza, tipa, deduplica e integra os dados necessários.
- Gold publica fatos e dimensões consumidos pelo Streamlit em modo somente leitura.
- A estrutura detalhada do repositório está registrada em `docs/arquitetura.md`.

## 11. Validação da capacidade atual

Na carga real verificada em 22/08/2026, com `source_updated_at = 2026-08-21T00:00:00Z`, `uf_principal = CE`, `natureza_intervencao = Obra` e `especie_intervencao = Construção`:

- 3.205 projetos.
- 3.244 registros de investimento previsto, totalizando R$ 25.161.698.700,05.
- 5.186 localidades associadas, correspondendo a 193 municípios.
- 695 obras em execução.
- 905 registros sem coordenadas, sinalizados no dashboard como dados parciais.

Os números acima são evidência do snapshot verificado, não valores fixos da aplicação. O filtro `Últimos 12 meses`, ancorado na data da fonte, resultou em 1.372 obras, R$ 8,63 bilhões, 192 municípios e 165 em execução; `Último mês` resultou em 38 obras, R$ 303,31 milhões, 29 municípios e nenhuma em execução.

### Status atual da capacidade

- `SPEC-001`: `Verifying`, com tarefas e critérios registrados como concluídos.
- Verificações passaram: Compose e serviços separados, carga nacional reconciliada, `dbt build` com 153/153, 26 testes no total (16 frontend), Ruff, compilação e healthcheck do Streamlit (`200 ok`).
- A aprovação humana para `Done` permanece pendente.
- A capacidade é local e demonstrável; não inclui orquestração em nuvem, execução agendada, comparação nacional no frontend ou detalhe completo do projeto.

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

- Comparação nacional no frontend.
- Detalhe completo do projeto e enriquecimentos com contratos, execução física, fornecedores e empenhos.
- Orquestração em nuvem e execução agendada.
- Estratégia operacional de atualização, retenção e observabilidade além do fluxo local verificado.
