select distinct md5(concat_ws('||', coalesce(item ->> 'tipo', '∅'), coalesce(item ->> 'descricao', '∅')))::text as ppa_key,
    nullif(trim(item ->> 'tipo'), '')::text as ppa_type, nullif(trim(item ->> 'descricao'), '')::text as ppa_description
from {{ ref('int_obrasgov_project_context') }} as context inner join {{ ref('fct_project_snapshot') }} as project using (project_snapshot_key)
where collection_name = 'ppa'
