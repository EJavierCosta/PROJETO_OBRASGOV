---
version: "alpha"
name: Vertere Obras Públicas
description: Sistema visual do dashboard Streamlit de inteligência de obras públicas.
assets:
  logo: "../assets/brand/vertere-ai-logo.png"
  dashboard-reference: "../assets/design/dashboard-obras-publicas-vertere.png"
colors:
  primary: "#C44DFF"
  primary-start: "#FF4DFF"
  primary-end: "#8C1AFF"
  primary-soft: "rgba(196, 77, 255, 0.10)"
  ink: "#14161A"
  slate: "#4B5768"
  border: "#E5E7EB"
  canvas: "#FFFFFF"
  surface-muted: "#F9FAFB"
  success: "#16855B"
  warning: "#B56A09"
  danger: "#C2415B"
  on-primary: "#FFFFFF"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 2.25rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 1.25rem
    fontWeight: 700
    lineHeight: 1.25
  metric:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.1
  body:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 0.9375rem
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 0.8125rem
    fontWeight: 600
    lineHeight: 1.25
  caption:
    fontFamily: "ui-sans-serif, system-ui, sans-serif"
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.4
rounded:
  sm: 8px
  md: 10px
  lg: 12px
  xl: 16px
  pill: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
components:
  app-canvas:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: 24px
  sidebar:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: 16px
  card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: 16px
  card-accent:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-end}"
    rounded: "{rounded.pill}"
    padding: 12px
  button-primary:
    backgroundColor: "{colors.primary-end}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
  input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.slate}"
    rounded: "{rounded.sm}"
    padding: 10px
  status-success:
    backgroundColor: "rgba(22, 133, 91, 0.12)"
    textColor: "{colors.success}"
    rounded: "{rounded.pill}"
    padding: 6px
  status-warning:
    backgroundColor: "rgba(181, 106, 9, 0.12)"
    textColor: "{colors.warning}"
    rounded: "{rounded.pill}"
    padding: 6px
  status-danger:
    backgroundColor: "rgba(194, 65, 91, 0.12)"
    textColor: "{colors.danger}"
    rounded: "{rounded.pill}"
    padding: 6px
---

## Overview

Clareza analítica com energia tecnológica controlada. O dashboard traduz a identidade atual da Vertere AI — branco dominante, tinta profunda e gradiente magenta-violeta — para uma ferramenta de decisão comercial. A interface deve parecer confiável e operacional, não promocional.

A estrutura principal tem duas visões: **Visão geral**, orientada a mercado, e **Detalhe do projeto**, orientada à investigação de uma obra. O Streamlit apenas consulta e apresenta as views `gold.vw_*_current`; regras de negócio permanecem no dbt.

## Colors

- **Ink (`#14161A`)**: títulos, métricas e texto de maior importância.
- **Slate (`#4B5768`)**: metadados, descrições, eixos e rótulos secundários.
- **Primary (`#C44DFF`)**: seleção, foco, séries principais e pontos do mapa.
- **Gradient (`#FF4DFF` → `#8C1AFF`)**: somente ações primárias e destaques raros. Em CSS: `linear-gradient(135deg, #FF4DFF, #8C1AFF)`.
- **Canvas e bordas**: fundo branco, superfícies discretas e borda `#E5E7EB`.
- **Semânticas**: verde, âmbar e vermelho comunicam estado; nunca substituem o rótulo textual original da API.

Nos gráficos, usar violeta para a série principal e tons derivados por luminosidade. Cores semânticas ficam reservadas a estados. Não criar arco-íris categórico.

## Typography

Usar a pilha sans-serif do sistema, como no site atual. Títulos são fortes e compactos; corpo e metadados mantêm contraste mais baixo. Números de KPI usam alinhamento tabular quando disponível.

- Título de página: token `display`.
- Títulos de seção e gráfico: token `heading`.
- KPI: token `metric`, com rótulo `label` acima ou ao lado.
- Eixos, fonte e atualização: token `caption`.
- Evitar caixa alta extensa. Usar caixa alta apenas em micro-rótulos curtos, com espaçamento entre letras.

## Layout

- Desktop: sidebar de 248–280 px e conteúdo fluido; largura útil máxima próxima de 1600 px.
- Grade base de 8 px; espaçamentos preferenciais de 16, 24 e 32 px.
- Cabeçalho compacto com marca, abas e estado do snapshot.
- Primeira dobra: título, contexto do recorte e quatro KPIs.
- Segunda faixa: mapa territorial e distribuição por situação.
- Terceira faixa: tabela de obras para análise.
- Mobile: filtros em painel recolhível, KPIs em uma coluna, mapa antes dos gráficos e tabela com rolagem horizontal.

O mapa e a distribuição por situação devem ter peso visual equivalente. O mapa não pode dominar o dashboard nem sugerir precisão territorial ausente na fonte.

## Elevation & Depth

Usar bordas finas antes de sombras. Cartões comuns: `0 1px 2px rgba(20, 22, 26, 0.05)`. Destaques raros: `0 10px 40px -10px rgba(196, 77, 255, 0.20)`. Não usar glassmorphism, brilho neon ou sombras pesadas.

## Shapes

Campos e botões usam 8–10 px. Cartões usam 12–16 px. Chips e ícones circulares usam raio total. Linhas e ícones têm geometria simples, com espessura visual consistente.

## Components

### Navegação

Usar a logo oficial em `assets/brand/vertere-ai-logo.png`, preservando proporção e transparência. As abas **Visão geral** e **Detalhe do projeto** ficam no topo. A aba ativa usa texto violeta e sublinhado de 2 px. Exibir `Snapshot atual` como chip neutro, junto de `source_updated_at` e `ingested_at` quando disponíveis.

### Filtros

Ordem: município, organização responsável, situação original, eixo/tipo/subtipo, faixa de investimento, ano de cadastro e período da data de cadastro. O último filtro oferece últimos 3, 6 ou 12 meses e ano corrente. Filtros múltiplos devem mostrar quantidade selecionada. A ação **Aplicar filtros** recebe o gradiente; **Limpar filtros** é secundária.

### KPIs

Exibir somente:

1. Total de obras.
2. Investimento previsto.
3. Municípios alcançados.
4. Obras em execução.

Cada cartão deve ter rótulo, valor, ícone simples e tooltip com definição. Nenhum KPI deve somar investimento previsto, contratado, empenhado, liquidado ou pago.

### Visualizações

- Mapa: pontos ou municípios associados, legenda de investimento e indicação de ausência de geometria.
- Situação: barras horizontais ordenadas por contagem, preservando os valores originais da API.
- Rankings: mostrar contagem de projetos ou investimento previsto, sempre declarando a medida.
- Tooltips: projeto, município, organização, situação e investimento previsto quando existirem.
- Não mostrar atraso como KPI: a cobertura de datas efetivas é insuficiente.

### Tabela de obras

Colunas mínimas: projeto, município, organização responsável, situação original e investimento previsto. Permitir seleção de linha para abrir o detalhe. Valores ausentes aparecem como `Não informado`, nunca como zero.

### Detalhe do projeto

Ordem recomendada: identificação e situação; localização; intervenção; datas previstas; investimento por fonte; execução física; contratos e fornecedores; empenhos; estudos; histórico. Cada bloco relacionado mostra cobertura ou estado vazio. Fornecedor não deve ser rotulado como executor sem evidência.

### Estados

- Carregamento: skeleton discreto, sem alterar a grade.
- Vazio: mensagem que diferencia filtro sem resultado de dado ausente na fonte.
- Erro: causa curta, possibilidade de tentar novamente e identificador da ingestão.
- Dado parcial: badge neutro e explicação no tooltip.

## Do's and Don'ts

### Do

- Preservar `situacao` original e informar o recorte `UF principal = CE`, `natureza = Obra`, `espécie = Construção`.
- Mostrar a atualização da fonte separada da data de ingestão.
- Manter medidas financeiras em blocos distintos e rotulados.
- Usar espaços em branco, hierarquia forte e violeta com parcimônia.
- Marcar dados inventados para protótipo como `Simulação`.

### Don't

- Não chamar projetos cadastrados de licitações abertas ou oportunidades confirmadas.
- Não criar score comercial automático sem regra aprovada na Gold.
- Não somar projetos por município como se fossem aditivos ao total geral.
- Não inferir atraso com datas efetivas de baixa cobertura.
- Não usar gradiente em todos os cartões, gráficos ou fundos.
- Não ocultar nulos, cobertura parcial ou a granularidade da métrica.
