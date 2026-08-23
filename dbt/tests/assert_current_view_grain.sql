select
    'vw_market_overview_current'::text as view_name,
    project_id,
    ingestion_id::text as ingestion_id,
    count(*)::bigint as row_count
from {{ ref('vw_market_overview_current') }}
group by project_id, ingestion_id
having count(*) > 1

union all

select
    'vw_project_investment_current'::text as view_name,
    concat_ws('||', project_id, coalesce(funding_source_name, '∅')) as project_id,
    ingestion_id::text as ingestion_id,
    count(*)::bigint as row_count
from {{ ref('vw_project_investment_current') }}
group by project_id, funding_source_name, ingestion_id
having count(*) > 1

union all

select
    'vw_project_location_current'::text as view_name,
    concat_ws(
        '||',
        project_id,
        coalesce(geometry_id::text, '∅'),
        coalesce(municipality_name, '∅'),
        coalesce(ibge_code::text, '∅'),
        coalesce(uf, '∅'),
        coalesce(pin_name, '∅'),
        coalesce(latitude::text, '∅'),
        coalesce(longitude::text, '∅')
    ) as project_id,
    ingestion_id::text as ingestion_id,
    count(*)::bigint as row_count
from {{ ref('vw_project_location_current') }}
group by project_id, geometry_id, municipality_name, ibge_code, uf, pin_name, latitude, longitude, ingestion_id
having count(*) > 1
