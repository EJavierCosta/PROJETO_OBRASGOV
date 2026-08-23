{{ config(materialized='view', grants={'select': ['obrasgov_frontend', 'obrasgov_chat']}) }}
select project.project_id::text, dim_restriction_area.restriction_area::text, project.source_updated_at::timestamptz, project.ingested_at::timestamptz, project.ingestion_id::uuid
from {{ ref('bridge_project_restriction_area') }} bridge inner join {{ ref('dim_restriction_area') }} using (restriction_area_key) inner join {{ ref('fct_project_snapshot') }} project using (project_snapshot_key) inner join {{ ref('int_obrasgov_current_ingestion') }} current on project.ingestion_id=current.ingestion_id
