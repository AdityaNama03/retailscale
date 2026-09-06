-- RetailScale: Warehouse and Database setup
-- Run manually in Snowsight. Kept here for reference/reproducibility only.

CREATE WAREHOUSE IF NOT EXISTS retailscale_wh
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for RetailScale project';

CREATE DATABASE IF NOT EXISTS retailscale_dev
  COMMENT = 'RetailScale development database';
