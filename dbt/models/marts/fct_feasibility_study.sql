select study.study_key::text, project.project_snapshot_key::text, study.ingestion_id::uuid, study.project_id::text, study.study_type::text, study.study_specification::text,
    project.source_updated_at::timestamptz, project.ingested_at::timestamptz
from {{ ref('stg_obrasgov_feasibility_study') }} as study inner join {{ ref('fct_project_snapshot') }} as project using (ingestion_id, project_id)
