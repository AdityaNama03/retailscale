-- RetailScale: Medallion schemas
-- Run manually in Snowsight. Kept here for reference/reproducibility only.

USE DATABASE retailscale_dev;

CREATE SCHEMA IF NOT EXISTS bronze COMMENT = 'Raw, untransformed data as loaded from S3';
CREATE SCHEMA IF NOT EXISTS silver COMMENT = 'Cleaned, typed, deduplicated data';
CREATE SCHEMA IF NOT EXISTS gold   COMMENT = 'Business-ready marts (dims/facts)';
