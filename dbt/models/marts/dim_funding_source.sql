select distinct
    funding_source_key::text as funding_source_key,
    funding_source_name::text as funding_source_name
from {{ ref('fct_planned_investment') }}
