# Obrasgov e construção civil

Contexto de domínio para o case de dados da Vertere AI, relacionando dados públicos de obras a decisões de empresas de construção e infraestrutura.

## Organizações

**Vertere AI**:
Empresa de tecnologia e dados do ecossistema GM GROUP, com foco em inteligência artificial aplicada à gestão.

**Braço de construção civil**:
Empresa do grupo com atuação em obras civis e infraestrutura, incluindo drenagem, pavimentação, adutoras e obras associadas a parques solares e eólicos.

## Dados e negócio

**Obras públicas**:
Projetos e intervenções publicados na API do ObrasGov, com informações de localização, situação, investimento previsto e, quando informados pela fonte, execução física e financeira.

**Inteligência comercial de obras**:
Uso dos dados de obras públicas para identificar mercados, regiões, órgãos e projetos aderentes às capacidades da construtora.

## Recorte e linguagem do produto

- O recorte atual é `UF principal = CE`, `natureza = Obra` e `espécie = Construção`.
- O snapshot atual é a última ingestão integral com status `succeeded`; a data de atualização da fonte e a data de ingestão são distintas.
- “Em execução” significa correspondência exata ao valor de situação informado pela fonte. Não é sinônimo de atraso, prioridade comercial ou oportunidade confirmada.
- “Investimento previsto” é uma estimativa da fonte e permanece separado de contratado, empenhado, liquidado e pago.
- O detalhe do projeto consulta uma obra por `project_id` e preserva relações 1:N, nulos e papéis dos participantes.
- O histórico exibido é o recurso de cancelamento/paralisação recebido pela fonte; o snapshot atual não é uma linha do tempo completa entre ingestões.
- A página “Chat com os dados” é opt-in, fica desabilitada por padrão e responde somente com base nas views Gold públicas allowlisted. Não deve inferir licitação aberta, atraso ou recomendação comercial.

## Ambiguidades sinalizadas

- Os sites consultados usam “GM GROUP” e “Grupo GM Participações”. A DM Engenharia declara integrar o Grupo GM Participações, mas a relação jurídica exata com o GM GROUP que apresenta a Vertere AI não foi confirmada publicamente.
- “Construtora do grupo” ainda não identifica uma razão social única; confirmar antes de usar o nome no PRD.

## Diálogo de exemplo

**Especialista:** Queremos saber onde existem obras públicas compatíveis com nossa atuação.
**Dev:** Então “obra prioritária” significa necessariamente obra atrasada?
**Especialista:** Não. A base permite analisar aderência por tipo, região, órgão e situação informada; atraso e prioridade comercial exigiriam dados e regras próprias.
