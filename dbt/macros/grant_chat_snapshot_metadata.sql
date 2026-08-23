{% macro grant_chat_snapshot_metadata() %}
    {% set relation = 'gold.vw_snapshot_metadata_current' %}
    {% do run_query("REVOKE ALL ON " ~ relation ~ " FROM obrasgov_chat") %}
    {% do run_query(
        "GRANT SELECT (source_updated_at, ingested_at, project_count, planned_investment_count, planned_investment_amount, location_count, municipality_count, execution_project_count) ON " ~ relation ~ " TO obrasgov_chat"
    ) %}
{% endmacro %}
