with exploded_pins as (
    select
        project_snapshot_key,
        ingestion_id,
        project_id,
        pin_position,
        pin_payload
    from {{ ref('stg_obrasgov_project') }} as project
    cross join lateral jsonb_array_elements(project.pins)
        with ordinality as pin_item(pin_payload, pin_position)
)

select
    md5(concat_ws('||', project_snapshot_key, pin_position::text)) as pin_key,
    project_snapshot_key,
    ingestion_id,
    project_id,
    pin_position::integer as pin_position,
    nullif(trim(pin_payload ->> 'pin'), '')::text as pin_name,
    case
        when replace(nullif(trim(pin_payload ->> 'latitude'), ''), ',', '.')
            ~ '^[+-]?[0-9]+([.][0-9]+)?$'
            then replace(pin_payload ->> 'latitude', ',', '.')::numeric
    end as latitude,
    case
        when replace(nullif(trim(pin_payload ->> 'longitude'), ''), ',', '.')
            ~ '^[+-]?[0-9]+([.][0-9]+)?$'
            then replace(pin_payload ->> 'longitude', ',', '.')::numeric
    end as longitude
from exploded_pins
