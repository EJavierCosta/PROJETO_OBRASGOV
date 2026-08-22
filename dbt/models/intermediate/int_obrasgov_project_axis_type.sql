with exploded_axis_types as (
    select
        project_snapshot_key,
        ingestion_id,
        project_id,
        axis_position,
        axis_type_payload
    from {{ ref('stg_obrasgov_project') }} as project
    cross join lateral jsonb_array_elements(project.axis_types)
        with ordinality as axis_type_item(axis_type_payload, axis_position)
)

select
    md5(concat_ws('||', project_snapshot_key, axis_position::text)) as project_axis_type_key,
    project_snapshot_key,
    ingestion_id,
    project_id,
    axis_position::integer as axis_position,
    nullif(trim(axis_type_payload ->> 'eixo'), '')::text as axis_name,
    case
        when nullif(trim(axis_type_payload ->> 'id_eixo'), '') ~ '^[+-]?[0-9]+$'
            then (axis_type_payload ->> 'id_eixo')::integer
    end as axis_id,
    nullif(trim(axis_type_payload ->> 'tipo'), '')::text as type_name,
    case
        when nullif(trim(axis_type_payload ->> 'id_tipo'), '') ~ '^[+-]?[0-9]+$'
            then (axis_type_payload ->> 'id_tipo')::integer
    end as type_id,
    nullif(trim(axis_type_payload ->> 'subtipo'), '')::text as subtype_name,
    case
        when nullif(trim(axis_type_payload ->> 'id_subtipo'), '') ~ '^[+-]?[0-9]+$'
            then (axis_type_payload ->> 'id_subtipo')::integer
    end as subtype_id
from exploded_axis_types
