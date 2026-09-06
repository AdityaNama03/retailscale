-- RetailScale: File format for CSV loads
-- Run manually in Snowsight. Kept here for reference/reproducibility only.

USE DATABASE retailscale_dev;
USE SCHEMA bronze;

CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL')
  EMPTY_FIELD_AS_NULL = TRUE
  COMMENT = 'Standard CSV format for Olist bronze loads';
