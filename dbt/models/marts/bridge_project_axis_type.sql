with scoped_axis_types as (
    select
        axis_type.project_axis_type_key,
        axis_type.project_snapshot_key,
        project.ingestion_id,
        axis_type.axis_id,
        axis_type.axis_name,
        axis_type.type_id,
        axis_type.type_name,
        axis_type.subtype_id,
        axis_type.subtype_name
    from {{ ref('int_obrasgov_project_axis_type') }} as axis_type
    inner join {{ ref('fct_project_snapshot') }} as project
        on axis_type.project_snapshot_key = project.project_snapshot_key
)

select
    project_axis_type_key::text as project_axis_type_bridge_key,
    project_snapshot_key::text as project_snapshot_key,
    ingestion_id::uuid as ingestion_id,
    md5(
        concat_ws(
            '||',
            coalesce(axis_id::text, '∅'),
            coalesce(axis_name, '∅'),
            coalesce(type_id::text, '∅'),
            coalesce(type_name, '∅'),
            coalesce(subtype_id::text, '∅'),
            coalesce(subtype_name, '∅')
        )
    )::text as axis_type_key
from scoped_axis_types
