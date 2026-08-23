DO $$
DECLARE
    view_name text;
BEGIN
    FOREACH view_name IN ARRAY ARRAY[
        'gold.vw_market_overview_current',
        'gold.vw_project_investment_current',
        'gold.vw_project_location_current',
        'gold.vw_status_distribution_current',
        'gold.vw_snapshot_metadata_current',
        'gold.vw_project_detail_current',
        'gold.vw_project_participant_current',
        'gold.vw_project_axis_type_current',
        'gold.vw_project_ppa_current',
        'gold.vw_project_restriction_area_current',
        'gold.vw_project_photo_indicator_current',
        'gold.vw_project_contract_current',
        'gold.vw_project_commitment_current',
        'gold.vw_project_commitment_totals_current',
        'gold.vw_project_execution_current',
        'gold.vw_project_status_history_current',
        'gold.vw_project_feasibility_study_current',
        'gold.vw_project_coverage_current'
    ] LOOP
        IF to_regclass(view_name) IS NOT NULL THEN
            IF view_name = 'gold.vw_snapshot_metadata_current' THEN
                EXECUTE format('REVOKE ALL ON %s FROM obrasgov_chat', view_name);
                EXECUTE format('GRANT SELECT (source_updated_at, ingested_at, project_count, planned_investment_count, planned_investment_amount, location_count, municipality_count, execution_project_count) ON %s TO obrasgov_chat', view_name);
            ELSE
                EXECUTE format('GRANT SELECT ON %s TO obrasgov_chat', view_name);
            END IF;
        END IF;
    END LOOP;
END
$$;
