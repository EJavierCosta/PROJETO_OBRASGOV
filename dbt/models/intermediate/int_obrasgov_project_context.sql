with collections as (
    select project_snapshot_key, ingestion_id, project_id, 'ppa'::text as collection_name, coalesce(case when jsonb_typeof(ppas) = 'array' then ppas end, '[]'::jsonb) as items from {{ ref('stg_obrasgov_project') }}
    union all select project_snapshot_key, ingestion_id, project_id, 'restriction_area', coalesce(case when jsonb_typeof(areas_restricao) = 'array' then areas_restricao end, '[]'::jsonb) from {{ ref('stg_obrasgov_project') }}
    union all select project_snapshot_key, ingestion_id, project_id, 'photo_indicator', coalesce(case when jsonb_typeof(fotos) = 'array' then fotos end, '[]'::jsonb) from {{ ref('stg_obrasgov_project') }}
)
select project_snapshot_key::text, ingestion_id::uuid, project_id::text, collection_name::text, item::jsonb,
    row_number() over (partition by project_snapshot_key, collection_name order by ordinal)::integer as item_position
from collections cross join lateral jsonb_array_elements(items) with ordinality as exploded(item, ordinal)
