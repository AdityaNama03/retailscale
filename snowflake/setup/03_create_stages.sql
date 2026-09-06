-- RetailScale: Storage integration + external stage linking Snowflake to S3
-- Run manually in Snowsight. Kept here for reference/reproducibility only.
--
-- NOTE: <ROLE_ARN> below refers to the AWS IAM role `retailscale-snowflake-role`.
-- After creating the integration, run:
--     DESC STORAGE INTEGRATION retailscale_s3_int;
-- and use the returned STORAGE_AWS_IAM_USER_ARN + STORAGE_AWS_EXTERNAL_ID
-- to finish the trust policy on the AWS side before the stage will work.

CREATE STORAGE INTEGRATION IF NOT EXISTS retailscale_s3_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://retailscale-landing/bronze/');

USE DATABASE retailscale_dev;
USE SCHEMA bronze;

CREATE STAGE IF NOT EXISTS retailscale_bronze_stage
  URL = 's3://retailscale-landing/bronze/'
  STORAGE_INTEGRATION = retailscale_s3_int
  COMMENT = 'External stage over the S3 bronze landing zone';

-- Sanity check: should list the uploaded Olist files
LIST @retailscale_bronze_stage;
