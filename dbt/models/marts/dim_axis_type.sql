with scoped_axis_types as (
    select
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

select distinct
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
    )::text as axis_type_key,
    axis_id::integer as axis_id,
    axis_name::text as axis_name,
    type_id::integer as type_id,
    type_name::text as type_name,
    subtype_id::integer as subtype_id,
    subtype_name::text as subtype_name
from scoped_axis_types
