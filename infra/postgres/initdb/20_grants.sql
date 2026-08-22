GRANT USAGE ON SCHEMA bronze, silver, gold TO obrasgov_ingestion, obrasgov_dbt, obrasgov_frontend;
GRANT CREATE ON SCHEMA bronze TO obrasgov_ingestion;
GRANT CREATE, USAGE ON SCHEMA silver, gold TO obrasgov_dbt;

GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_run TO obrasgov_ingestion;
GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_resource TO obrasgov_ingestion;
GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_page TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_project_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_geometry_raw TO obrasgov_ingestion;
GRANT SELECT, INSERT ON bronze.obrasgov_source_update_raw TO obrasgov_ingestion;

GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO obrasgov_dbt;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze TO obrasgov_dbt;
GRANT USAGE ON SCHEMA gold TO obrasgov_frontend;
