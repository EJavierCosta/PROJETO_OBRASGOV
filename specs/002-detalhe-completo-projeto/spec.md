# SPEC-002 — Detalhe completo do projeto

**Status:** Verifying
**Responsável:** Responsável pelo produto
**Aprovação para Ready:** Aprovada pelo responsável pelo produto em 22/08/2026
**Referência visual:** Aprovada em 22/08/2026
**Última revisão:** 23/08/2026

## Contexto e resultado esperado

Permitir que o gestor comercial parta de uma obra da visão geral e investigue seu contexto completo sem confundir cadastro, execução, contratação e execução financeira.

O resultado observável é uma página de detalhe que consome somente a Gold atual e apresenta, quando associados na fonte, identificação, participantes, localização, intervenção, datas, investimento previsto por fonte, execução física vigente, contratos e fornecedores, empenhos, estudos de viabilidade e eventos de cancelamento ou paralisação.

## Esboço do dashboard

```text
┌ Voltar à visão geral                     Snapshot atual ┐
│ Nome do projeto                            [Situação]    │
│ Órgão responsável · ID da fonte · Município(s)          │
├ Investimento previsto ┬ Período previsto ┬ Cobertura     ┤
├ Identificação e participantes ───────────────────────────┤
├ Localização e mapa ────────┬ Intervenção e datas ───────┤
├ Investimento por fonte ──────────────────────────────────┤
├ Execução física ─────────────────────────────────────────┤
├ Contratos e fornecedores ────────────────────────────────┤
├ Empenhos e execução financeira ──────────────────────────┤
├ Estudos de viabilidade ┬ Cancelamento/paralisação ──────┤
└ Atualização da fonte · Ingestão · Estados de cobertura ──┘
```

Cada bloco multivalorado mantém sua própria tabela, lista ou cartão. O histórico de cancelamento/paralisação é agrupado semanticamente e a execução física é apresentada em um cartão por registro distinto, sem timeline de medições. Ausência de associação deve aparecer como `Não informado pela fonte`, sem converter nulos em zero.

A referência visual aprovada em [`assets/design/dashboard-detalhe-projeto-vertere.png`](../../assets/design/dashboard-detalhe-projeto-vertere.png) materializa esse esboço com dados marcados como `Simulação`. A implementação atual remove a timeline não sustentada pelo endpoint e usa os dados reais das views Gold `current`. Em caso de divergência, prevalecem esta spec, `docs/DESIGN.md` e os dados reais da Gold, nessa ordem.

## Critério para decisões de dados

Decisões de detalhamento podem ser fechadas sem nova validação de negócio quando estiverem sustentadas pelo contrato oficial da API, por amostras reais e pela granularidade comprovada no snapshot. A implementação deve preservar o valor original, separar conceitos diferentes e registrar cobertura. Quando a fonte não sustentar uma interpretação, o painel deve mostrar `Não informado pela fonte`, manter o rótulo original ou sinalizar a divergência; nunca completar o significado por inferência.

## Escopo

- Navegação da tabela da visão geral para um projeto identificado por `project_id`.
- Consulta direta de um projeto por seletor como alternativa de navegação.
- Ingestão nacional dos endpoints de contratos, empenhos, execução física, histórico de situação e estudos de viabilidade.
- Bronze append-only com as mesmas garantias de snapshot, reconciliação e idempotência da SPEC-001.
- Silver tipada e separada por granularidade para os novos recursos e coleções relacionadas.
- Expansão da constelação Gold existente com fatos, dimensões conformadas e views atuais próprias para cada bloco do detalhe.
- Página Streamlit completa conforme o esboço e `docs/DESIGN.md`.
- Cobertura, estados vazios, erros seguros e metadados do snapshot por seção.
- Testes e reconciliações ponta a ponta dos novos recursos.

## Não escopo

- Comparação nacional no frontend.
- Classificação automática, score ou recomendação de oportunidade comercial.
- Afirmação de licitação aberta ou disponibilidade comercial.
- KPI de atraso inferido.
- Soma de investimento previsto, valores contratuais, empenhados, liquidados e pagos.
- Download ou visualização de documentos, fotos e vídeos.
- Edição de dados da fonte pelo frontend.
- Histórico reconstruído além dos eventos e snapshots efetivamente recebidos.
- Evolução do percentual de execução entre ingestões.
- Histórico completo do ciclo de situações da obra; a fonte específica cobre cancelamento e paralisação.

## Requisitos

- **REQ-001:** O usuário deve abrir o detalhe de um projeto a partir da visão geral, manter um seletor alternativo e persistir o `project_id` público na URL.
- **REQ-002:** Um `project_id` inexistente, ausente ou fora do recorte atual deve produzir estado vazio seguro, sem consultar Bronze ou Silver.
- **REQ-003:** A ingestão deve coletar e reconciliar integralmente `/contrato`, `/empenho`, `/execucao-fisica`, `/historico-situacao-cancelada-paralisada` e `/estudo-viabilidade` no mesmo snapshot lógico da SPEC-001.
- **REQ-004:** Falha ou mudança da fonte durante qualquer novo recurso deve impedir a publicação de toda a ingestão como atual.
- **REQ-005:** A Silver deve tipar e deduplicar cada recurso em sua granularidade, explodindo indicativos e motivos de execução em relações próprias quando aplicável.
- **REQ-006:** A Gold deve ampliar a constelação existente; não deve criar uma estrela isolada nem unir fatos diretamente.
- **REQ-007:** Contratos, empenhos, execução física, eventos de situação e estudos devem permanecer em fatos distintos e relacionados ao projeto e à ingestão.
- **REQ-008:** `fct_project_snapshot` e as dimensões de organização, fornecedor, localização, intervenção, fonte de recurso e data devem ser conformados e reutilizados quando a chave e a semântica coincidirem.
- **REQ-009:** O Streamlit deve consultar somente views `gold.vw_*_current`, com filtros parametrizados por um único `project_id`.
- **REQ-010:** A página deve preservar valores e rótulos originais, exibir medidas financeiras separadas e distinguir ausência, zero e dado parcial.
- **REQ-011:** Cada seção deve informar sua cobertura e oferecer estados de carregamento, vazio e erro conforme `docs/DESIGN.md`.
- **REQ-012:** Regras de seleção do registro vigente, agregação, cobertura e formatação semântica devem permanecer no dbt; o frontend apenas seleciona e apresenta.
- **REQ-013:** Testes, catálogo e evidências devem permitir reconciliar cada bloco desde a Bronze até a view Gold consumida.
- **REQ-014:** A página deve exibir somente campos fornecidos pela API no snapshot atual e agregações fiéis, sem reconstruir histórico pela comparação entre ingestões.
- **REQ-015:** O histórico de cancelamento e paralisação deve preservar todos os eventos-fonte, agrupar duplicatas semânticas na view e mostrar inicialmente os 10 eventos mais recentes com expansão do histórico completo.
- **REQ-016:** A seção de empenhos deve mostrar totais separados por medida e uma tabela expansível dos empenhos individuais do projeto no snapshot atual.
- **REQ-017:** A página deve mostrar exatamente uma obra por vez e incluir todas as relações associadas ao seu `project_id`, inclusive múltiplos contratos.
- **REQ-018:** A seção de contratos deve mostrar a quantidade distinta, listar todos os contratos da obra e permitir expandir cada contrato individualmente, sem total monetário combinado.
- **REQ-019:** A seção de estudos de viabilidade deve mostrar somente quantidade, tipo e especificação fornecidos pela API, sem situação, data ou conclusão inferidas.
- **REQ-020:** A execução física deve exibir cada `id_execucao_fisica` distinto da obra no snapshot atual, sem média, máximo ou seleção automática de um registro.
- **REQ-021:** A localização deve exibir todos os municípios, geometrias e pins associados à obra no snapshot atual, sem inferir ou selecionar um município principal.
- **REQ-022:** O investimento previsto deve mostrar o total da obra e sua discriminação por fonte de recurso, sem combiná-lo com valores de contratos ou empenhos.
- **REQ-023:** Participantes devem ser exibidos por papel informado pela API — responsável, repassador, tomador e executor — preservando a mesma organização em todos os papéis que ela ocupar.
- **REQ-024:** O detalhe deve apresentar os atributos descritivos e coleções do projeto disponíveis na fonte, incluindo eixo/tipo/subtipo, PPA, áreas de restrição e indicador de foto, sem inventar conteúdo, geometria ou interpretação jurídica ausente.
- **REQ-025:** Datas previstas e efetivas devem ser exibidas separadamente, sem calcular atraso ou aderência ao prazo quando a fonte não fornecer regra suficiente.
- **REQ-026:** Indicadores declaratórios do projeto e registros dos endpoints relacionados devem permanecer auditáveis separadamente; divergências de cobertura devem ser sinalizadas, não corrigidas por inferência.

## Regras e contratos de dados

- O snapshot atual continua sendo a última ingestão integral com status `succeeded`.
- Todas as views do detalhe filtram exclusivamente o `ingestion_id` atual; versões de ingestões anteriores não participam da página.
- Todos os novos recursos participam da atomicidade lógica da ingestão; não existe detalhe atual parcialmente publicado entre endpoints.
- A publicação é atômica para os oito recursos: falha em qualquer endpoint impede que a nova ingestão substitua o snapshot atual.
- `project_id + ingestion_id` é a referência comum entre fatos, bridges e a entidade do projeto.
- Nenhum bloco pode combinar registros de projetos diferentes; `project_id` é obrigatório em todas as consultas do detalhe.
- `fct_project_snapshot` permanece a espinha do detalhe e não recebe medidas de fatos filhos.
- A SPEC-002 não cria `dim_project`: os atributos da obra já existem na granularidade projeto + ingestão de `fct_project_snapshot`. Uma dimensão própria exigirá outra decisão caso surja semântica histórica diferente do snapshot.
- `dim_organization` é conformada entre responsável, repassador, tomador e executor. A chave usa o CNPJ normalizado quando houver 14 dígitos; sem esse identificador, usa o nome normalizado com teste explícito de colisão.
- `bridge_project_participant` tem uma linha por projeto, papel, organização e ingestão. Duplicatas exatas dentro do mesmo papel são removidas com contagem de origem preservada; papéis diferentes nunca são fundidos.
- O nome e o CNPJ originais permanecem disponíveis para auditoria mesmo quando a chave conformada usa valores normalizados.
- `fct_contract` tem uma linha por projeto, contrato e ingestão; sua chave considera `ingestion_id + project_id + contract_source_id` quando a fonte fornecer identificador estável.
- A seção de contratos lista todos os `id_contrato` distintos da obra selecionada; contrato não é a unidade de navegação da página.
- A tabela de contratos exibe número, fornecedor, situação e vigência; a expansão individual mostra objeto, processo, modalidade, órgão, categoria, licitação, link de transparência e valores disponíveis.
- `valor_global_contrato`, `valor_acumulado_contrato`, `valor_utilizado_pi_contrato` e `valor_incluido_contrato` permanecem medidas separadas por contrato e não são somados entre si.
- A quantidade de contratos usa `count(distinct id_contrato)` após deduplicação dentro do snapshot atual.
- Sem identificador estável de contrato, a Silver usa uma chave determinística composta pelos campos de identidade confirmados no payload e mantém teste explícito de colisão.
- `fct_commitment` tem uma linha por projeto, identidade determinística do empenho e ingestão; a chave combina projeto, sistema e base de origem, UG emitente, número do empenho, minuta e data de emissão.
- `fct_physical_execution` tem uma linha por projeto, registro de execução física e ingestão.
- `fct_status_event` tem uma linha por projeto, evento de situação e ingestão.
- `fct_feasibility_study` tem uma linha por projeto, tipo, hash da especificação normalizada e ingestão, pois a API não fornece ID próprio do estudo.
- A quantidade de estudos usa a chave determinística após deduplicação; especificação ausente aparece como `Não informado pela fonte`.
- O frontend não exibe status, data de referência, conclusão ou observação de estudo, pois esses campos não existem no endpoint atual.
- A execução física apresenta os registros vigentes de `/execucao-fisica` no snapshot atual; o endpoint não é tratado como histórico temporal de medições.
- Duplicatas exatas de `id_execucao_fisica` e conteúdo dentro da mesma ingestão são removidas na Silver, preservando a contagem de origem para reconciliação.
- Uma obra com um registro distinto usa um card; com vários registros, usa uma lista de cards identificados pelo `id_execucao_fisica` e instrumento quando disponível.
- Percentual, datas, instrumento, forma de execução, indicativos e motivos permanecem associados ao respectivo registro; percentuais de registros diferentes não são agregados.
- Snapshots de ingestões anteriores permanecem armazenados para auditoria, mas não são usados para reconstruir o histórico exibido no detalhe atual.
- `fct_physical_execution` e `fct_status_event` preservam todas as ingestões pela coluna `ingestion_id`; as views atuais selecionam somente os registros pertencentes ao último snapshot `succeeded`.
- Dimensões conformadas não armazenam o histórico de execução ou de situação e não usam SCD tipo 2 para reconstruí-lo nesta spec.
- O histórico de situação usa somente eventos datados de `/historico-situacao-cancelada-paralisada`; mudanças de percentual de execução não geram eventos de situação inferidos.
- O bloco deve ser rotulado como `Histórico de cancelamento e paralisação`, sem sugerir cobertura de todas as situações possíveis.
- Eventos de situação com IDs diferentes e conteúdo semântico igual permanecem auditáveis; a regra de apresentação deve evitar uma timeline enganosa sem apagar silenciosamente registros da fonte.
- `fct_status_event` mantém uma linha por `id_historico_situacao_investimento` e ingestão.
- A chave semântica da view considera projeto, data, situação, justificativa, indicador de tratativa e fase da tratativa, normalizando apenas espaços e strings vazias.
- A view agrupada publica `source_event_count` e os IDs-fonte associados; a soma de `source_event_count` deve reconciliar com o fato no mesmo snapshot.
- A página ordena os grupos por data decrescente, exibe os 10 mais recentes e oferece expansão para todos os grupos do projeto.
- Relações N:N usam bridges; o frontend não faz joins entre fatos.
- A seção de localização lista todas as associações de `gold.vw_project_location_current` e representa no mapa todas as coordenadas válidas da obra.
- `uf_principal` pode contextualizar a obra, mas não define município principal nem elimina outras localizações associadas.
- Localizações sem coordenada permanecem na lista com estado explícito; não são descartadas nem recebem coordenada inferida.
- Eixo, tipo e subtipo reutilizam a bridge existente e todas as combinações associadas à obra são exibidas.
- PPA é modelado por `dim_ppa` e `bridge_project_ppa`, usando tipo e descrição originais; não é convertido em exercício financeiro ou programa orçamentário sem campo explícito.
- Área de restrição é modelada por `dim_restriction_area` e `bridge_project_restriction_area`. O texto informa associação declarada pela fonte, não polígono, impedimento jurídico ou interseção calculada no mapa.
- A coleção `fotos` fornece apenas `ind_foto` no contrato observado. Seus valores distintos ficam em `bridge_project_photo_indicator`; a interface exibe disponibilidade declarada, sem galeria ou link inexistente.
- Descrição, endereço, CEP, função social, meta global, população beneficiada, descrição da população, empregos gerados, indicador BIM, projeto estruturante, sistema responsável e observações são atributos do cabeçalho detalhado quando informados.
- O resumo do projeto usa uma view de cabeçalho sem fanout; cada coleção usa uma view Gold própria.
- Valores financeiros negativos, chaves colidentes e percentuais fora de `0..100` são tratados conforme regras de qualidade documentadas, sem descarte silencioso.
- Os totais de empenho agregam separadamente `valor_empenho`, `aliquidar`, `liquidado`, `pago`, `rpinscrito`, `rpaliquidar`, `rpaliquidado` e `rppago` após deduplicação pela chave do empenho.
- O total de investimento previsto soma somente as linhas deduplicadas de `fct_planned_investment` da obra no snapshot atual; a abertura por fonte deve reconciliar com esse total.
- Investimento previsto, valores contratuais e medidas de empenho representam conceitos distintos e nunca compõem um total financeiro conjunto.
- `Restos a pagar` é um agrupamento visual, não uma medida única; inscrito, a liquidar, liquidado e pago permanecem distintos.
- A tabela individual preserva número, emissão, UG emitente, origem, natureza da despesa, credor, descrição e cada medida financeira disponível.
- Nulo aparece como `Não informado pela fonte`; zero permanece zero e não participa de preenchimento ou inferência.
- Todas as coleções retornam os registros completos da obra. Paginação, rolagem ou expansão podem organizar a interface, mas não aplicar corte arbitrário; valores sem data ficam após os registros datados.
- A ordenação é determinística: participantes por papel e nome; localizações por município; investimentos por fonte; contratos, empenhos e execuções pela data própria decrescente e chave como desempate; estudos, PPAs e áreas de restrição por seus rótulos originais.
- Identificadores permanecem armazenados como texto original. Formatação visual de CNPJ não altera o valor auditável.
- `link_transparencia` só é clicável quando possuir esquema `http` ou `https`; valores inválidos permanecem auditáveis na Gold, mas não são executados pela interface.
- Fornecedor não é apresentado como executor sem papel explícito na fonte.
- Datas previstas e efetivas permanecem distintas; ausência de data efetiva não significa atraso.
- `possui_estudo_viabilidade` é um indicador declaratório do projeto; a lista de estudos vem de `/estudo-viabilidade`. Se os dois não coincidirem, ambos permanecem preservados e a view de cobertura sinaliza a divergência.
- `source_updated_at` e `ingested_at` permanecem visíveis e semanticamente separados.

## Views de consumo previstas

- `gold.vw_project_detail_current`: identificação, responsável, situação, datas e atributos de baixa cardinalidade.
- `gold.vw_project_participant_current`: organizações e seus papéis no projeto.
- `gold.vw_project_location_current`: localização e coordenadas, reutilizada da SPEC-001.
- `gold.vw_project_investment_current`: investimento previsto por fonte, reutilizada da SPEC-001.
- `gold.vw_project_axis_type_current`: todas as combinações de eixo, tipo e subtipo da obra.
- `gold.vw_project_ppa_current`: PPAs associados.
- `gold.vw_project_restriction_area_current`: áreas de restrição declaradas pela fonte.
- `gold.vw_project_photo_indicator_current`: indicadores de disponibilidade de foto, sem conteúdo de mídia.
- `gold.vw_project_contract_current`: contratos e fornecedores.
- `gold.vw_project_commitment_current`: valores financeiros por empenho.
- `gold.vw_project_execution_current`: registros e indicadores de execução física.
- `gold.vw_project_status_history_current`: eventos originais de situação.
- `gold.vw_project_feasibility_study_current`: estudos associados.
- `gold.vw_project_coverage_current`: contagem e disponibilidade de cada bloco.

## Critérios de aceitação

- **AC-001 — REQ-001/REQ-002:** Selecionar uma obra na visão geral abre o mesmo `project_id` no detalhe; URL ausente ou inválida produz estado vazio testado.
- **AC-002 — REQ-003:** Os cinco novos recursos reconciliam páginas e itens recebidos com os totais informados pela API.
- **AC-003 — REQ-004:** Uma falha simulada em qualquer novo endpoint marca a ingestão como `failed` e preserva todas as views atuais anteriores.
- **AC-004 — REQ-005/REQ-013:** `dbt build` passa com testes de chaves, relações, tipos, granularidade e órfãos dos novos modelos.
- **AC-005 — REQ-006/REQ-007:** Testes comprovam ausência de fanout e impedem soma cruzada entre fatos.
- **AC-006 — REQ-008:** As dimensões conformadas possuem uma única definição de chave e relacionamento válido com os fatos aplicáveis.
- **AC-007 — REQ-009/REQ-012:** O teste do frontend comprova que a página consulta somente views Gold permitidas e um único projeto por vez.
- **AC-008 — REQ-010:** Valores ausentes aparecem como `Não informado pela fonte`; zero permanece zero e as grandezas financeiras são exibidas em blocos separados.
- **AC-009 — REQ-011:** Todos os blocos renderizam estados com dados, vazio e erro sem quebrar a página completa.
- **AC-010 — REQ-010/REQ-011:** A inspeção visual confirma hierarquia, responsividade, tema claro/escuro e aderência a `docs/DESIGN.md`.
- **AC-011 — REQ-013:** Contratos, empenhos, execução, histórico e estudos exibidos para amostras reais reconciliam com Silver e Bronze no mesmo `ingestion_id`.
- **AC-012 — REQ-003/REQ-013:** O fluxo completo executa via Docker Compose e as evidências são registradas em `verification.md`.
- **AC-013 — REQ-014:** Testes e inspeção visual comprovam ausência de timeline de percentual, comparação entre snapshots ou histórico completo de situações não fornecido pela API.
- **AC-014 — REQ-015:** Um projeto com duplicatas semânticas mantém todos os IDs no fato, apresenta uma linha agrupada com `source_event_count`, reconcilia a contagem total e permite expandir além dos 10 eventos mais recentes.
- **AC-015 — REQ-016:** Os totais por medida reconciliam com os empenhos deduplicados do projeto, restos a pagar permanecem em quatro submedidas e a tabela expansível preserva nulos e zeros.
- **AC-016 — REQ-017:** Uma obra com múltiplos contratos exibe todos os contratos distintos e nenhuma consulta ou componente contém registros de outro `project_id`.
- **AC-017 — REQ-018:** A quantidade distinta reconcilia com a tabela, cada contrato pode ser expandido e nenhuma medida contratual é combinada em um total único.
- **AC-018 — REQ-019:** A quantidade e a lista de estudos reconciliam com a Gold e nenhum campo de situação, data ou conclusão aparece na página.
- **AC-019 — REQ-020:** Duplicatas exatas não multiplicam cards, todos os IDs distintos são exibidos e nenhum percentual agregado ou registro implicitamente selecionado aparece.
- **AC-020 — REQ-021:** Uma obra com múltiplos municípios ou pins exibe todas as associações na lista, todos os pontos válidos no mapa e nenhum município é apresentado como principal por inferência.
- **AC-021 — REQ-022:** O total de investimento previsto reconcilia com a soma das fontes deduplicadas da obra e nenhum valor contratual ou de empenho participa do cálculo.
- **AC-022 — REQ-023:** Participantes reconciliam com responsável e coleções da fonte, duplicatas no mesmo papel não se repetem e uma organização com papéis diferentes aparece em cada grupo aplicável.
- **AC-023 — REQ-024:** Atributos e coleções de contexto reconciliam com o snapshot, todas as associações multivaloradas são preservadas e área de restrição ou indicador de foto não geram mapa, mídia ou interpretação inexistente.
- **AC-024 — REQ-025:** Datas previstas e efetivas aparecem com rótulos distintos; data ausente não produz atraso, duração ou estado derivado.
- **AC-025 — REQ-026:** Divergência entre indicador de estudo e registros do endpoint é sinalizada sem alterar nenhum dos dois valores.

## Dependências e riscos

- Contrato e disponibilidade dos cinco novos endpoints da API pública, integrados aos três recursos-base.
- Aumento relevante do tempo e volume da carga nacional.
- Baixa cobertura de contratos, execução, histórico ou estudos para parte dos projetos.
- Identidade natural incompleta em empenhos e estudos.
- Mudanças de schema durante a transição para o novo ambiente da API.
- Limitações de navegação e estado do Streamlit.
- Valores declaratórios conflitantes entre o projeto e endpoints relacionados.

## Pendência para mudança de status

- Aprovação explícita do responsável pelo produto para mover a spec de `Verifying` para `Done`.
