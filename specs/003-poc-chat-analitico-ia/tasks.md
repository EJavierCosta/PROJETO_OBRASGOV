# Tarefas — SPEC-003

**Status:** Done; implementação, evidências e aprovação final registradas
**Última revisão:** 23/08/2026

## Refinamento e governança

- [x] **TASK-001 — REQ-003/REQ-005/AC-003/AC-005:** Registrar a decisão Gemini-first, manter o contrato/factory de provider independente de SDK e fazer `codex_cli` falhar fechado como extensão futura.
- [x] **TASK-002 — REQ-008/REQ-009/AC-008/AC-009:** Executar spike do parser PostgreSQL com aliases, CTEs, locks, funções, schema qualification, complexidade e falha fechada.
- [x] **TASK-003 — REQ-018/AC-018:** Atualizar PRD e arquitetura, criar ADR 0003 e documentar Gemini-first, transferência restrita ao Gold público e guardrails de banco antes de solicitar `Ready`.
- [x] **TASK-004 — REQ-006/REQ-011/AC-006:** Fechar o catálogo semântico, subconjuntos geráveis, granularidades e gramática por view.

## Dependências e configuração

- [x] **TASK-005 — REQ-004/REQ-008/REQ-018:** Adicionar dependências frontend, atualizar lockfile e documentar opt-in, `GEMINI_MODEL=gemini-3.5-flash-lite`, timeouts, variáveis e limites sem secrets, sem monitoramento de tokens.
- [x] **TASK-006 — REQ-003/REQ-015/REQ-016/AC-003:** Implementar opt-in, validação de configuração e factory restrita de providers.

## Providers e agente

- [x] **TASK-007 — REQ-003/REQ-017:** Criar protocolo, erros sanitizados e provider fake determinístico.
- [x] **TASK-008 — REQ-004/AC-004:** Implementar e testar adapter Gemini com cliente mockado.
- [x] **TASK-009 — REQ-005/AC-005:** Testar a rejeição segura de `codex_cli`, a ausência do runtime no Compose e a independência do `ChatAgent` em relação a subprocessos.
- [x] **TASK-010 — REQ-002/REQ-007/REQ-012/REQ-014:** Implementar `ChatAgent`, envelopes, classificação de answerability e fluxo de uma consulta.

## SQL e Gold

- [x] **TASK-011 — REQ-008/REQ-009:** Implementar parser AST, complexidade, allowlist das 17 views geráveis, joins seguros por `project_id`, CTEs/agregações e allowlists de statements, colunas e funções.
- [x] **TASK-012 — REQ-010/REQ-013/REQ-016:** Criar role do chat, executor Psycopg read-only e consulta estática de metadados no seam Gold.
- [x] **TASK-013 — AC-008/AC-009/AC-014:** Criar corpus automatizado de SQL permitido, proibido, semanticamente inválido e adversarial.
- [x] **TASK-014 — AC-010/AC-015:** Validar grants, transação, rollback, timeout, cursor, limites e ausência de secrets em integração local.
- [x] **TASK-015 — REQ-011/AC-011/AC-012:** Criar perguntas douradas com medidas explícitas, SQL de referência, recusas e teste de fanout.

## Streamlit

- [x] **TASK-016 — REQ-001/REQ-015:** Criar página desabilitada por padrão, com habilitação por configuração e histórico somente em `st.session_state`.
- [x] **TASK-017 — REQ-013/REQ-016:** Implementar resposta executiva e estados seguros de resposta e erro; manter SQL, limites e proveniência fora da interface.
- [x] **TASK-018 — AC-001/AC-013/AC-016:** Criar AppTest do chat e regressão das páginas existentes.

## Integração e evidências

- [x] **TASK-019 — REQ-017/AC-002 a AC-007:** Executar testes do fluxo e dos providers sem rede, créditos ou autenticação real.
- [x] **TASK-020 — AC-017:** Executar Ruff, pytest, AppTest, lockfile e smoke test; concluir `dbt build` após fixar `agate==1.8.0` no extra transform.
- [x] **TASK-021 — REQ-018/AC-018:** Revalidar DESIGN, README e configuração após a implementação contra mudanças comportamentais aprovadas antes do encerramento.
- [x] **TASK-022 — AC-001 a AC-018:** Registrar comandos, resultados, limitações e evidências reproduzíveis em `verification.md`; a aprovação para `Done` foi registrada em 23/08/2026.
- [x] **TASK-023 — AC-010/AC-016:** Corrigir o grant estático de metadados, a URL Psycopg do Compose e a propagação distinta de timeout; adicionar regressões correspondentes.
- [x] **TASK-024 — REQ-004/REQ-016:** Registrar a seleção manual de `gemini-3.5-flash-lite` por disponibilidade/cota, sem fallback automático; o gate end-to-end passou com seed 42.
- [x] **TASK-025 — REQ-001/REQ-007/AC-019:** Permitir saudações e texto natural no histórico, com resposta local segura para conversa e sem chamada provider/Gold quando não houver intenção analítica.
- [x] **TASK-026 — REQ-006/REQ-009/REQ-011/AC-020:** Expandir catálogo e SQLGuard para todas as views Gold públicas dos dashboards, joins por chaves allowlisted, CTEs/agregações e prevenção de fanout financeiro.
- [x] **TASK-027 — REQ-010/AC-020:** Atualizar grants da role `obrasgov_chat` para todas as views Gold públicas do dashboard, mantendo read-only, timeout e limites.
- [x] **TASK-028 — AC-020:** Adicionar perguntas douradas de contratos, empenhos, execução, participantes, cobertura e joins/agregações com reconciliação de fanout.
- [x] **TASK-029 — REQ-013/REQ-015/AC-013/AC-023:** Remover o consentimento técnico da UI, apresentar apenas a resposta executiva e oferecer CTA contextual para o detalhe quando o resultado identificar uma única obra.
- [x] **TASK-030 — REQ-002/REQ-007/REQ-012/AC-021:** Propagar histórico natural recente e limitado da sessão ao agente/provider, preservando referências conversacionais sem enviar SQL, resultados brutos ou metadados internos.
- [x] **TASK-031 — REQ-006/REQ-011/AC-022:** Mapear execução física e status “Em execução” no contexto semântico, suportar contagem distinta por projeto acima de percentual e adicionar pergunta dourada/regressão.
- [x] **TASK-032 — REQ-001/REQ-016/AC-024:** Exibir feedback visual de processamento com spinner executivo durante o fluxo do agente, sem expor metadados internos.
