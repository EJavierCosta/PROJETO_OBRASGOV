select distinct {{ obrasgov_organization_key('supplier_cnpj', 'supplier_name') }}::text as supplier_key,
    supplier_name::text as supplier_name, supplier_cnpj::text as supplier_cnpj
from {{ ref('stg_obrasgov_contract') }} as contract
inner join {{ ref('fct_project_snapshot') }} as project using (ingestion_id, project_id)
where supplier_name is not null or supplier_cnpj is not null
