# SPEC-001 — Pipeline mínimo de projetos do Ceará

**Status:** Done
**Responsável:** Responsável pelo produto
**Aprovação anterior:** Ready aprovado em 21/08/2026
**Aprovação para Ready:** Reaprovada após inclusão das referências de design em 21/08/2026
**Aprovação humana explícita para Done:** Confirmada pelo usuário em 23/08/2026 ("finalizamos a spec 1")
**Última revisão:** 23/08/2026

## Contexto e resultado esperado

Entregar a primeira capacidade funcional do case: executar localmente um fluxo reproduzível que coleta um snapshot nacional do ObrasGov, transforma o recorte de obras de construção do Ceará e apresenta uma visão geral em Streamlit.

O resultado deve demonstrar o caminho completo entre fonte, Bronze, Silver, Gold e frontend, sem antecipar todo o enriquecimento previsto no PRD.

## Escopo

- Fundação mínima do repositório, dependências e Docker Compose.
- Ingestão nacional de `/data-atualizacao`, `/projeto-investimento` e `/geometria`, com paginação quando aplicável.
- Registro da atualização informada pela fonte e dos metadados da ingestão.
- Bronze append-only com payload original e rastreabilidade por `ingestion_id`.
- Silver com tipagem, limpeza, deduplicação e relações necessárias ao incremento.
- Gold com o recorte `uf_principal = CE`, `natureza_intervencao = Obra` e `especie_intervencao = Construção`.
- Visão geral Streamlit consumindo somente Gold.
- Implementação visual orientada por `docs/DESIGN.md`, pela logo oficial e pela referência em `assets/design/dashboard-obras-publicas-vertere.png`.
- Testes e evidências do fluxo mínimo.

## Não escopo

- Detalhe completo do projeto.
- Comparação nacional no frontend.
- Classificação automática de oportunidade comercial.
- KPI de atraso.
- Orquestração em nuvem ou execução agendada.
- Enriquecimentos não necessários à visão geral desta fatia.
- Endpoints de contratos, empenhos, execução física, histórico de situação e estudos de viabilidade.

## Requisitos

- **REQ-001:** O ambiente completo deve ser executável localmente por Docker Compose, com versões de runtime e dependências fixadas.
- **REQ-002:** Cada nova atualização da fonte deve gerar full load nacional de `/projeto-investimento` e `/geometria`, além de `/data-atualizacao`, reconciliando todas as páginas e quantidades informadas pela API.
- **REQ-003:** Cada execução deve registrar `ingestion_id`, `source_updated_at`, `started_at`, `finished_at`, status e erro, preservando o payload original na Bronze.
- **REQ-004:** Uma execução incompleta ou inconsistente deve ser marcada como falha e não pode se tornar o snapshot atual.
- **REQ-005:** O dbt deve publicar Silver tipada e deduplicada e Gold dimensional sem unir diretamente relações que provoquem fanout.
- **REQ-006:** A Gold deve aplicar o recorte do Ceará e preservar situação, intervenção e valores financeiros originais da fonte.
- **REQ-007:** O Streamlit deve consultar apenas views Gold da última ingestão bem-sucedida e apresentar os KPIs disponíveis nesta fatia.
- **REQ-008:** Regras de negócio e cálculos dos KPIs devem permanecer no dbt; o frontend apenas consulta e apresenta.
- **REQ-009:** Logs, testes e documentação devem permitir reproduzir e explicar a execução do snapshot até os KPIs.
- **REQ-010:** A repetição da mesma coleta deve ser idempotente por padrão e permitir reprocessamento explícito com `--force`.
- **REQ-011:** A ingestão deve rejeitar uma carga quando `source_updated_at` mudar entre o início e o fim da paginação.
- **REQ-012:** O case deve reter integralmente snapshots bem-sucedidos e falhos, isolando o consumo atual pela última execução `succeeded`.
- **REQ-013:** A visão geral deve seguir `docs/DESIGN.md`, usar `assets/brand/vertere-ai-logo.png` como marca e `assets/design/dashboard-obras-publicas-vertere.png` como referência de composição, hierarquia e distribuição dos componentes.
- **REQ-014:** A visão geral deve oferecer filtro de seleção única de período da data de cadastro com as opções último mês, últimos 3 meses, últimos 6 meses, últimos 12 meses e ano corrente, aplicadas sobre `registration_date`.

## Regras e contratos de dados

- A Bronze é nacional, append-only e identificada por `ingestion_id`.
- Cada atualização da fonte produz um snapshot completo; não há upsert entre snapshots Bronze.
- O filtro comercial é aplicado somente na Silver/Gold.
- O snapshot atual considera apenas a última ingestão com status `succeeded`.
- `source_updated_at` e `ingested_at` representam momentos diferentes e não podem ser substituídos um pelo outro.
- Total de obras usa contagem distinta de `id_projeto_investimento`.
- Obras em execução preserva o valor original `Em execução` da fonte.
- Investimento previsto não pode ser somado com valores contratados, empenhados, liquidados ou pagos.
- Relações multivaloradas devem manter granularidade própria ou bridge explícita.
- A identidade lógica do snapshot é composta por `source_updated_at` e pelo hash do escopo da consulta.
- Uma execução normal não recria um snapshot lógico já publicado com sucesso.
- `--force` cria nova ingestão do mesmo snapshot lógico sem apagar a anterior.
- Uma nova tentativa após falha recebe outro `ingestion_id`; a execução falha permanece auditável.
- Chaves únicas por execução, recurso, página e posição impedem duplicação ao repetir páginas.
- O desaparecimento de um registro é representado por sua ausência no novo snapshot, sem apagar snapshots anteriores.
- `source_updated_at` é consultado antes e depois da carga; valores diferentes tornam a execução `failed`.
- Uma execução com mudança da fonte permanece auditável, não é publicada e deve ser refeita integralmente com novo `ingestion_id`.
- Snapshots antigos e falhos permanecem armazenados, mas não participam das views `gold.vw_*_current`.
- O Streamlit não consulta tabelas históricas ou raw diretamente.
- O período de cadastro usa `registration_date` e considera como referência a data de atualização do snapshot atual; registros sem data não entram em um período definido.

## Referências obrigatórias de design

- [Sistema visual e regras de interface](../../docs/DESIGN.md): fonte normativa para cores, tipografia, espaçamento, componentes, estados e comportamento responsivo.
- [Logo oficial da Vertere AI](../../assets/brand/vertere-ai-logo.png): marca do cabeçalho, preservada sem alteração de proporção.
- [Referência visual do dashboard](../../assets/design/dashboard-obras-publicas-vertere.png): referência para cabeçalho, filtros, KPIs, mapa, gráfico de situação e tabela da visão geral.
- Em caso de divergência, prevalecem a spec, o `DESIGN.md` e os dados reais da Gold, nesta ordem.
- Os valores e registros exibidos na imagem não constituem dados de teste nem valores fixos da aplicação.
- O detalhe completo do projeto mostrado na navegação permanece fora do escopo desta spec.
- A referência visual orienta a implementação, sem exigir reprodução pixel a pixel das limitações do Streamlit.

## Critérios de aceitação

- **AC-001 — REQ-001:** Um comando documentado inicia o ambiente do zero e conclui PostgreSQL, ingestão, dbt e Streamlit sem intervenção manual adicional.
- **AC-002 — REQ-002:** Para cada recurso ingerido, páginas, itens recebidos e total informado pela fonte são reconciliados e registrados.
- **AC-003 — REQ-003/REQ-004:** Uma falha simulada gera execução `failed`, preserva a evidência do erro e não altera as views Gold atuais.
- **AC-004 — REQ-005/REQ-006:** `dbt build` conclui sem erro e os testes comprovam chaves, relacionamentos, granularidade e recorte do Ceará.
- **AC-005 — REQ-006:** Contagens e investimento previsto da Gold reconciliam com a Silver para o mesmo `ingestion_id` e filtros.
- **AC-006 — REQ-007/REQ-008:** A página de visão geral carrega somente dados Gold e exibe, no mínimo, total de obras, investimento previsto, obras em execução e distribuição por situação.
- **AC-007 — REQ-009:** Testes Python, lint, testes dbt e smoke test do Streamlit possuem comandos e resultados registrados em `verification.md`.
- **AC-008 — REQ-009:** Nenhum segredo, credencial real ou dado bruto gerado é versionado.
- **AC-009 — REQ-010:** Repetir uma coleta bem-sucedida não duplica dados; `--force` cria nova ingestão; repetir uma página na mesma execução preserva uma única cópia de cada item.
- **AC-010 — REQ-011:** Uma mudança simulada de `source_updated_at` durante a paginação marca a execução como `failed` e mantém inalterado o snapshot atual.
- **AC-011 — REQ-002:** Uma nova atualização executa full load, cria outro `ingestion_id` e reflete inclusões, alterações e ausências sem modificar o snapshot anterior.
- **AC-012 — REQ-012:** Com múltiplos snapshots e uma execução falha armazenados, os KPIs continuam usando exclusivamente a última execução bem-sucedida.
- **AC-013 — REQ-013:** A visão geral renderizada usa a logo oficial, é inspecionada contra a imagem de referência e atende aos tokens, à hierarquia, aos estados e ao layout aplicáveis definidos em `DESIGN.md`, sem valores simulados em produção.
- **AC-014 — REQ-014:** Ao selecionar um único período de cadastro, somente projetos cuja `registration_date` esteja no intervalo relativo à atualização do snapshot permanecem nos KPIs, mapa, distribuição e tabela; datas nulas ficam fora do recorte definido.

## Dependências e riscos

- Disponibilidade e estabilidade do contrato da API ObrasGov.
- Volume nacional e duração da carga inicial.
- Mudança da fonte durante a paginação.
- Campos nulos e relações sem identificador natural estável.
- Cobertura territorial necessária ao KPI de municípios e ao mapa.

## Dúvidas materiais

Nenhuma.
