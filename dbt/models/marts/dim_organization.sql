with organizations as (
    select organization_key::text, organization_name::text, organization_cnpj::text
    from {{ ref('fct_project_snapshot') }}

    union all

    select organization_key::text, organization_name::text, organization_cnpj::text
    from {{ ref('int_obrasgov_project_participant') }}
)
select organization_key, max(organization_name)::text as organization_name,
    max(organization_cnpj)::text as organization_cnpj
from organizations
group by organization_key
