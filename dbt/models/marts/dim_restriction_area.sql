select distinct md5(coalesce(nullif(trim(item ->> 'area_restricao'), ''), '∅'))::text as restriction_area_key,
    nullif(trim(item ->> 'area_restricao'), '')::text as restriction_area
from {{ ref('int_obrasgov_project_context') }} as context inner join {{ ref('fct_project_snapshot') }} as project using (project_snapshot_key)
where collection_name = 'restriction_area'
