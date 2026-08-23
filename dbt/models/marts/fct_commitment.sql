select commitment.commitment_key::text, project.project_snapshot_key::text, commitment.ingestion_id::uuid, commitment.project_id::text,
    commitment.commitment_number::text, commitment.emission_date::date, commitment.issuing_ug::text, commitment.source_system::text, commitment.source_base::text,
    commitment.expense_nature::text, commitment.creditor_name::text, commitment.commitment_description::text,
    commitment.valor_empenho::numeric, commitment.aliquidar::numeric, commitment.liquidado::numeric, commitment.pago::numeric, commitment.rpinscrito::numeric, commitment.rpaliquidar::numeric, commitment.rpaliquidado::numeric, commitment.rppago::numeric,
    project.source_updated_at::timestamptz, project.ingested_at::timestamptz
from {{ ref('stg_obrasgov_commitment') }} as commitment inner join {{ ref('fct_project_snapshot') }} as project using (ingestion_id, project_id)
