select contract.contract_key::text, project.project_snapshot_key::text, contract.ingestion_id::uuid, contract.project_id::text,
    contract.contract_source_id::text, contract.contract_number::text,
    {{ obrasgov_organization_key('contract.supplier_cnpj', 'contract.supplier_name') }}::text as supplier_key,
    contract.supplier_name::text, contract.supplier_cnpj::text, contract.contract_status::text, contract.validity_start_date::date, contract.validity_end_date::date,
    contract.contract_object::text, contract.process_number::text, contract.modality::text, contract.organization_name::text, contract.category::text, contract.procurement_number::text, contract.transparency_link::text,
    contract.valor_global_contrato::numeric, contract.valor_acumulado_contrato::numeric, contract.valor_utilizado_pi_contrato::numeric, contract.valor_incluido_contrato::numeric,
    project.source_updated_at::timestamptz, project.ingested_at::timestamptz
from {{ ref('stg_obrasgov_contract') }} as contract inner join {{ ref('fct_project_snapshot') }} as project using (ingestion_id, project_id)
