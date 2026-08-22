with raw_geometries as (
    select
        ingestion_id,
        page_number,
        page_size,
        record_index,
        payload,
        record_hash,
        fetched_at,
        case
            when nullif(trim(payload ->> 'id_geometria'), '') ~ '^[+-]?[0-9]+$'
                then (payload ->> 'id_geometria')::integer
        end as geometry_id
    from {{ source('bronze', 'obrasgov_geometry_raw') }}
),

ranked_geometries as (
    select
        *,
        row_number() over (
            partition by ingestion_id, coalesce(geometry_id::text, record_hash)
            order by fetched_at desc, page_number desc, record_index desc
        ) as dedupe_rank
    from raw_geometries
)

select
    md5(concat_ws('||', ingestion_id::text, coalesce(geometry_id::text, record_hash))) as location_key,
    ingestion_id::uuid as ingestion_id,
    nullif(trim(payload ->> 'id_projeto_investimento'), '')::text as project_id,
    geometry_id::integer as geometry_id,
    nullif(trim(payload ->> 'sg_uf'), '')::text as uf,
    nullif(trim(payload ->> 'no_municipio'), '')::text as municipality_name,
    case
        when nullif(trim(payload ->> 'cod_ibge'), '') ~ '^[0-9]+$'
            then (payload ->> 'cod_ibge')::bigint
    end as ibge_code,
    nullif(trim(payload ->> 'origem_geometria'), '')::text as geometry_origin,
    record_hash::text as source_record_hash,
    page_number::integer as source_page_number,
    page_size::integer as source_page_size,
    record_index::integer as source_record_index,
    fetched_at::timestamp with time zone as source_fetched_at
from ranked_geometries
where dedupe_rank = 1
