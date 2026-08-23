GRANT USAGE ON SCHEMA bronze, silver TO obrasgov_ingestion, obrasgov_dbt;
REVOKE ALL ON SCHEMA bronze, silver FROM obrasgov_frontend;
GRANT USAGE ON SCHEMA gold TO obrasgov_frontend;
GRANT CREATE ON SCHEMA bronze TO obrasgov_ingestion;
GRANT CREATE, USAGE ON SCHEMA silver, gold TO obrasgov_dbt;

GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_run TO obrasgov_ingestion;
GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_resource TO obrasgov_ingestion;
GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_page TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_project_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_geometry_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_contract_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_commitment_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_physical_execution_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_status_history_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_feasibility_study_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_source_update_raw TO obrasgov_ingestion;

GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO obrasgov_dbt;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze TO obrasgov_dbt;
GRANT USAGE ON SCHEMA gold TO obrasgov_frontend;

REVOKE ALL ON SCHEMA bronze, silver FROM obrasgov_chat;
REVOKE CREATE ON SCHEMA gold FROM obrasgov_chat;
GRANT USAGE ON SCHEMA gold TO obrasgov_chat;
REVOKE ALL ON ALL TABLES IN SCHEMA gold FROM obrasgov_chat;

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
                EXECUTE format('GRANT SELECT (source_updated_at, ingested_at, project_count, planned_investment_count, planned_investment_amount, location_count, municipality_count, execution_project_count) ON %s TO obrasgov_chat', view_name);
            ELSE
                EXECUTE format('GRANT SELECT ON %s TO obrasgov_chat', view_name);
            END IF;
        END IF;
    END LOOP;
    EXECUTE format(
        'REVOKE CREATE, TEMPORARY ON DATABASE %I FROM obrasgov_chat',
        current_database()
    );
END
$$;
