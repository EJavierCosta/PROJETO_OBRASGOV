# PRD — Inteligência de Obras Públicas para Construção

**Status:** `SPEC-001`, `SPEC-002` e `SPEC-003` **Done**, com aprovação humana registrada em 23/08/2026.
**Data:** 18/08/2026
**Última revisão:** 23/08/2026

## 1. Contexto

A Vertere AI atua com tecnologia, dados e inteligência artificial no ecossistema GM GROUP. O case será desenvolvido no contexto do braço de construção civil do grupo, usando dados públicos do Obrasgov.br.

O Obrasgov.br registra projetos de investimento em infraestrutura, com situação, investimento previsto e localização, entre outros campos. A capacidade atual usa a API pública para construir um snapshot nacional e disponibilizar o recorte de obras de construção do Ceará.

## 2. Problema

Gestores comerciais de uma construtora precisam consolidar informações dispersas sobre obras públicas para entender onde estão os investimentos, quais órgãos demandam obras e quais projetos merecem análise comercial.

## 3. Objetivo do produto

Disponibilizar uma visão atualizada do mercado de obras públicas de construção no Ceará, permitindo explorar projetos por localização, órgão, tipo, situação, investimento e data de cadastro informados pela fonte.

A comparação nacional e os enriquecimentos operacionais permanecem evoluções futuras. O detalhamento completo do projeto foi implementado e aprovado na SPEC-002.

O produto não terá como objetivo afirmar que uma licitação está aberta nem gerar uma lista completa de oportunidades comerciais.

## 4. Usuário principal

Gerente ou diretor comercial de novos negócios da construtora.

## 5. Perguntas de negócio

- Onde estão concentradas as obras públicas de construção no Ceará?
- Quais municípios, organizações e tipos de obra concentram mais projetos?
- Qual o volume de investimento previsto por município, organização e situação?
- Quais obras merecem análise individual pelo time comercial a partir da lista filtrada?

Contratos, fornecedores, empenhos, execução física, estudos e histórico de cancelamento/paralisação são perguntas atendidas na página de detalhe da SPEC-002, sempre com os campos efetivamente informados pela fonte.

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
- A navegação de detalhe abre uma obra por `project_id`; a implementação ponta a ponta da SPEC-002 está em `Done`.

### KPIs principais

- **Total de obras:** contagem distinta de `id_projeto_investimento`.
- **Investimento previsto:** soma do valor previsto por projeto no recorte filtrado; a abertura por fonte é apresentada no detalhe.
- **Municípios alcançados:** contagem distinta de `cod_ibge` nas localizações associadas.
- **Obras em execução:** contagem distinta de projetos com `situacao = Em execução`.
- **Distribuição por situação:** contagem dos valores originais de `situacao`, sem reclassificação.

Os quatro KPIs são recalculados para o recorte filtrado; o investimento previsto não é combinado com valores contratados, empenhados, liquidados ou pagos.

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
- Mapa de pontos com coordenadas informadas pela fonte; as demais associações de localização permanecem disponíveis na lista de obras.
- Gráfico de barras da distribuição por situação original.
- Tabela filtrada com obra, município, organização responsável, situação e investimento previsto.
- Linguagem executiva, cabeçalho com datas de referência e atualização, identidade visual Vertere e suporte legível aos temas claro e escuro.

### Detalhe do projeto — SPEC-002 entregue

A SPEC-002 implementa o detalhe de uma obra por vez, exibindo somente dados do snapshot atual fornecidos pela API: identificação, participantes por papel, localização completa, contexto e intervenção, datas previstas e efetivas separadas, investimento previsto por fonte, execução física vigente, contratos, fornecedores, empenhos, estudos e histórico específico de cancelamento e paralisação.

PPA, áreas de restrição e indicador de foto serão apresentados conforme os rótulos da fonte. Não serão inferidos atraso, evolução entre snapshots, situação de estudo, geometria de restrição, conteúdo de foto ou total financeiro que combine conceitos distintos.

## 7. Dados utilizados

### Recursos usados na SPEC-001

`/data-atualizacao`, `/projeto-investimento` e `/geometria`, preservando payloads e metadados de ingestão na Bronze. O recorte usa identificação, descrição, organização responsável, UF, datas, situação, intervenção, investimento previsto e localização.

### Dados relacionados efetivamente modelados

- Investimento previsto por fonte de recurso.
- Geometria, município e coordenadas quando disponíveis.
- Eixo, tipo e subtipo de intervenção.

Contratos, fornecedores, empenhos, execução física, histórico de situação e estudos de viabilidade integram o mesmo snapshot lógico dos três recursos-base e possuem fatos e views Gold próprios.

### Expansão implementada na SPEC-002

`/contrato`, `/empenho`, `/execucao-fisica`, `/historico-situacao-cancelada-paralisada` e `/estudo-viabilidade` integram o mesmo snapshot lógico dos três recursos atuais. Participantes, PPAs, áreas de restrição e indicadores de foto são normalizados a partir das coleções recebidas em `/projeto-investimento`.

## 8. Modelo analítico

Na capacidade atual, o Gold publica uma constelação de fatos, dimensões, bridges e views atuais.

- `fct_project_snapshot`: uma linha por projeto por ingestão.
- `fct_planned_investment`: uma linha por projeto e fonte de recurso.
- Dimensões e bridges mínimas de organização, localização, intervenção, eixo/tipo/subtipo, fonte de recurso e coordenadas.
- Views Gold atuais para visão de mercado, investimentos, localização, distribuição por situação, metadados do snapshot e os recursos detalhados publicados pela SPEC-002.

O frontend consulta somente as views Gold da última ingestão bem-sucedida. Contratos, fornecedores, empenhos, execução física, histórico, estudos e demais coleções da SPEC-002 são publicados por interfaces Gold próprias.

## 9. Limitações conhecidas

- A API não informa de forma suficiente se uma licitação está aberta.
- O frontend atual consome somente a última ingestão bem-sucedida; a retenção de snapshots não equivale a uma série histórica pronta para análise.
- Parte das localizações não possui coordenadas e parte dos investimentos previstos não possui valor; o dashboard sinaliza dados parciais.
- A baixa cobertura de datas efetivas impede um KPI confiável de atraso.
- A cobertura de contratos, fornecedores, empenhos, execução física, histórico e estudos pode ser parcial conforme os dados retornados pela fonte.
- A base também possui projetos, estudos e outras intervenções; por isso o filtro de natureza e espécie é obrigatório para o recorte do case.

## 10. Requisitos do case

- Ingestão em Python em container próprio.
- Transformações em SQL com dbt em container próprio.
- PostgreSQL em container próprio.
- Arquitetura Bronze, Silver e Gold.
- Modelo dimensional na camada Gold.
- Frontend local em Python com Streamlit em container próprio, consumindo a Gold em modo somente leitura.
- Visão geral e detalhe completo do projeto implementados; SPEC-002 está em `Done` após aprovação humana.
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

No snapshot atual consultado em 23/08/2026, com `source_updated_at = 2026-08-22T00:00:00Z`, `uf_principal = CE`, `natureza_intervencao = Obra` e `especie_intervencao = Construção`:

- 3.207 projetos.
- 3.246 registros de investimento previsto, totalizando R$ 25.164.016.200,05.
- 5.189 localidades associadas, correspondendo a 193 municípios.
- 698 obras em execução.
- 5.543 associações sem coordenadas, sinalizadas no dashboard como dados parciais.

Os números acima são evidência do snapshot verificado, não valores fixos da aplicação. O filtro `Últimos 12 meses`, ancorado na data da fonte, resultou em 1.365 obras, R$ 8,59 bilhões, 192 municípios e 164 em execução; `Último mês` resultou em 22 obras, R$ 198,75 milhões, 18 municípios e nenhuma em execução.

### Status atual da capacidade

- `SPEC-001`: `Done` por aprovação explícita do usuário em 23/08/2026; a revalidação atual registra 154 testes, Ruff, compilação e healthcheck do Streamlit (`200 ok`), além das evidências de `dbt build` da entrega.
- `SPEC-002`: implementação ponta a ponta validada em `verification.md`, com ingestão dos oito recursos, Gold atual, detalhe por `project_id`, `dbt build` com 37 modelos de tabela, 18 views e 180 testes (`PASS=235`, `WARN=0`, `ERROR=0`), smoke direcionado com 23 testes, Ruff e healthcheck do Streamlit (`200 ok`).
- A suíte local atual tem 154 testes aprovados; a suíte frontend tem 136 testes aprovados. As evidências históricas de cada spec permanecem nos respectivos `verification.md`.
- `SPEC-003`: `Done`, após aprovação humana registrada em 23/08/2026; a capacidade continua desabilitada por padrão.
- A capacidade é local e demonstrável; não inclui orquestração em nuvem, execução agendada ou comparação nacional no frontend.

## 12. Versionamento e governança da modelagem

- Git é a fonte de verdade para SQL, YAML, testes e documentação.
- O dbt é usado de forma declarativa para construir Silver e Gold.
- `sources.yml` e `schema.yml` formam o catálogo, com descrições, linhagem e testes.
- Modelos Gold públicos têm contratos de schema e testes de qualidade versionados.
- Não há workflow de CI versionado neste checkout; a validação é reproduzível localmente por pytest, Ruff, dbt e Docker Compose.
- Mudanças incompatíveis poderão criar versões de modelo com janela de depreciação.
- A Bronze será append-only, identificada por `ingestion_id`.
- Schemas PostgreSQL e objetos de infraestrutura são criados por bootstrap SQL; upgrades aditivos ficam em `infra/postgres/upgrade/` e são aplicados manualmente em volumes existentes.

## 13. Decisões pendentes

- Comparação nacional no frontend.
- Orquestração em nuvem e execução agendada.
- Estratégia operacional de atualização, retenção e observabilidade além do fluxo local verificado.

## 14. POC de chat analítico com IA

A SPEC-003 implementa uma página opcional de chat para perguntas sobre o snapshot Gold atual. A primeira fase usa somente a API Gemini com o modelo operacional `gemini-3.5-flash-lite` e não toma decisões comerciais automaticamente.

- O agente poderá consultar as views Gold públicas usadas pela visão geral e pelo detalhe do projeto, incluindo contratos, empenhos, execução, participantes e cobertura; metadados do snapshot permanecem limitados às colunas públicas.
- A conversa preservará os últimos turnos naturais da sessão para resolver referências como “e em Fortaleza?” ou “qual link?”, sem enviar ao provider SQL, resultado bruto, conexão ou metadados internos.
- “Obra ativa” será interpretada como situação original `Em execução`; porcentagem de conclusão usará a execução física vigente e contagens combinarão localizações e execução por `project_id` distinto.
- O SQL será somente leitura, com `SELECT`, CTEs de leitura, joins seguros por `project_id` e agregações. Não serão permitidos DDL, DML, `CREATE TEMP TABLE`, locks, joins sem chave segura, fanout financeiro ou acesso a schemas e catálogos fora da allowlist.
- A síntese poderá receber pergunta, contexto mínimo, SQL aprovado e resultado Gold limitado, pois o recorte é público. Secrets, conexão, payload bruto e metadados internos não serão enviados.
- A capacidade ficará desabilitada por padrão e não haverá fallback automático para o Codex CLI.
- A interface será executiva: sem checkbox ou banner técnico, mostrando apenas a resposta em linguagem natural e um acesso ao detalhe quando a resposta identificar uma única obra.
- A SPEC-003 está em `Done`, com testes automatizados, validação Gold, smoke do Gemini e documentação registrados; a capacidade permanece desabilitada por padrão e sua habilitação depende da configuração explícita do ambiente.
- Durante uma pergunta, a página exibe o spinner “Analisando os dados...”; a interface não expõe SQL, metadados técnicos, limites ou proveniência.
