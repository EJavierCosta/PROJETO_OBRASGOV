# Instruções do repositório

## Contexto obrigatório

Antes de alterar código, leia:

- `docs/PRD.md` e `CONTEXT.md`;
- `docs/arquitetura.md` e ADRs aplicáveis;
- `docs/desenvolvimento-spec-driven.md`;
- todos os artefatos da spec ativa.

## Spec-Driven Development

- Mudanças de comportamento, dados, modelagem, arquitetura, pipeline, KPIs ou frontend exigem spec.
- Cada spec representa uma capacidade vertical em `specs/NNN-nome/`.
- Não implemente uma spec em `Draft`; aguarde aprovação explícita para `Ready`.
- Agrupe plano e tarefas pelas stacks afetadas, sem dividir a spec por stack.
- Mantenha `tasks.md` atualizado durante a implementação.
- Registre comandos, resultados e limitações em `verification.md`.
- Nunca defina `Ready` ou `Done` sem aprovação explícita do responsável pelo produto.
- Mudanças materiais de requisito atualizam a spec antes do código.

## Arquitetura

- Ingestão Python publica Bronze; dbt transforma Silver e Gold; Streamlit lê somente Gold.
- Regras de negócio ficam no dbt e não são duplicadas no frontend.
- Não use ORM nem crie módulos genéricos `common`, `shared` ou `core` sem necessidade concreta.
- Preserve métricas financeiras distintas e valores originais da fonte.

## Verificação

- Execute os testes, lint, `dbt build` e smoke tests aplicáveis à alteração.
- Se uma validação não puder ser executada, registre o motivo e o próximo passo.
- Não declare uma entrega concluída sem evidência reproduzível.

## Git

- O desenvolvimento individual ocorre diretamente na `main`, sem PR obrigatório.
- Faça commits pequenos seguindo Conventional Commits com o identificador da spec, por exemplo `feat(spec-001): ingest projects`.
- Não versione segredos, credenciais ou dados brutos gerados.
