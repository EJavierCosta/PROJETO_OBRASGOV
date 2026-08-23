select md5(concat_ws('||', context.project_snapshot_key, context.item_position::text))::text as project_photo_indicator_key,
    context.project_snapshot_key::text, context.ingestion_id::uuid, context.project_id::text,
    nullif(trim(context.item ->> 'ind_foto'), '')::text as ind_foto
from {{ ref('int_obrasgov_project_context') }} as context inner join {{ ref('fct_project_snapshot') }} as project using (project_snapshot_key)
where context.collection_name = 'photo_indicator'
