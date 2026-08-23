# Tarefas — SPEC-002

**Status:** Done; validação ponta a ponta concluída
**Última revisão:** 23/08/2026

## Refinamento e contratos

- [x] **TASK-001 — REQ-003/REQ-005:** Inspecionar cobertura, schema e chaves dos cinco novos endpoints em amostras reais.
- [x] **TASK-002 — REQ-006/REQ-008:** Finalizar o modelo dimensional e atualizar ADR e documentação de modelagem; catálogo dbt será atualizado com os modelos na implementação.
- [x] **TASK-003 — REQ-001/REQ-010/REQ-011:** Validar o esboço, a navegação e os estados da página.

## Ingestão Python e Bronze

- [x] **TASK-004 — REQ-003:** Adicionar os cinco novos recursos e respectivas tabelas raw ao snapshot de oito recursos.
- [x] **TASK-005 — REQ-003/REQ-004:** Generalizar publicação, reconciliação e falha atômica pelo conjunto configurado de recursos.
- [x] **TASK-006 — REQ-003/REQ-004:** Testar paginação, repetição, falha e mudança da fonte nos novos recursos.

## dbt Silver/Gold

- [x] **TASK-007 — REQ-005:** Criar staging e relações aninhadas dos novos recursos.
- [x] **TASK-008 — REQ-006/REQ-007/REQ-008/REQ-023/REQ-024:** Criar dimensões, fatos e bridges conformadas do detalhe.
- [x] **TASK-009 — REQ-009/REQ-012/REQ-015/REQ-016/REQ-026:** Criar as views atuais de cabeçalho, coleções, cobertura, histórico agrupado e totais de empenho.
- [x] **TASK-010 — REQ-005/REQ-013:** Adicionar testes, contratos, catálogo e reconciliações sem fanout.

## Streamlit

- [x] **TASK-011 — REQ-001/REQ-002:** Implementar navegação por `project_id`, seletor alternativo e estado inválido.
- [x] **TASK-012 — REQ-009/REQ-012:** Ampliar a interface de acesso Gold com consultas parametrizadas por projeto.
- [x] **TASK-013 — REQ-010/REQ-011/REQ-014 a REQ-026:** Implementar os blocos completos de uma obra com os campos efetivamente fornecidos pela API.
- [x] **TASK-014 — REQ-001/REQ-002/REQ-011:** Testar navegação, dados, vazios, falhas, temas e responsividade.
- [x] **TASK-017 — REQ-010/REQ-011/REQ-017/REQ-021:** Revisar a linguagem executiva e a hierarquia visual do detalhe contra a referência, usando somente os campos Gold disponíveis.
- [x] **TASK-018 — AC-010:** Ajustar espaçamentos do cabeçalho, KPIs, títulos de seção e blocos financeiros conforme a grade visual da referência.
- [x] **TASK-019 — REQ-011/REQ-021/AC-020:** Reorganizar o card de localização, reduzir áreas ociosas e habilitar o tooltip do mapa em hover e foco.
- [x] **TASK-020 — REQ-011/AC-010:** Manter as tags de registro e situação na mesma linha e compactar o cartão de total previsto do investimento.
- [x] **TASK-021 — AC-010:** Impedir a navegação automática do diretório `pages/` e preservar logo e menu superior do shell Streamlit.
- [x] **TASK-022 — REQ-019/AC-010:** Afastar os indicadores financeiros das bordas e melhorar o cartão de execução física em desktop e mobile.

## Integração e documentação

- [x] **TASK-015 — REQ-003/REQ-013:** Executar carga real, dbt e reconciliações de amostras.
- [x] **TASK-016 — AC-001 a AC-025:** Executar validação ponta a ponta e registrar evidências reproduzíveis.
