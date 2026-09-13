from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

default_args = {
    "owner": "retailscale",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

COPY_INTO_SQL = """
COPY INTO bronze.orders
FROM @retailscale_stage/olist/orders/
FILE_FORMAT = (FORMAT_NAME = 'retailscale_csv_format')
ON_ERROR = 'CONTINUE';
"""
# Repeat/extend this pattern per bronze table (orders, customers, order_items,
# products, sellers, payments, reviews, geolocation) — either as one task per
# table, or a single task running multiple COPY INTO statements sequentially.

with DAG(
    dag_id="retailscale_daily_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["retailscale"],
) as dag:

    upload_to_s3 = BashOperator(
        task_id="upload_to_s3",
        bash_command="python /opt/airflow/scripts/upload_to_s3.py",
    )

    snowflake_copy_into = SnowflakeOperator(
        task_id="snowflake_copy_into",
        snowflake_conn_id="snowflake_retail",
        sql=COPY_INTO_SQL,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_retailscale && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_retailscale && dbt test",
    )

    upload_to_s3 >> snowflake_copy_into >> dbt_run >> dbt_test