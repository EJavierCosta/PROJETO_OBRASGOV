select md5(concat_ws('||', context.project_snapshot_key, context.item_position::text))::text as project_restriction_area_key,
    context.project_snapshot_key::text, context.ingestion_id::uuid, context.project_id::text,
    md5(coalesce(nullif(trim(context.item ->> 'area_restricao'), ''), '∅'))::text as restriction_area_key
from {{ ref('int_obrasgov_project_context') }} as context inner join {{ ref('fct_project_snapshot') }} as project using (project_snapshot_key)
where context.collection_name = 'restriction_area'
