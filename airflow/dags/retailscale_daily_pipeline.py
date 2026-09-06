from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "retailscale",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="retailscale_daily_pipeline",
    default_args=default_args,
    description="S3 upload -> Snowflake bronze load -> dbt run -> dbt test",
    schedule_interval="@daily",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["retailscale"],
) as dag:

    def run_upload_to_s3():
        import subprocess
        result = subprocess.run(
            ["python", "/opt/airflow/scripts/upload_to_s3.py"],
            capture_output=True, text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            raise Exception(f"S3 upload failed: {result.stderr}")

    upload_to_s3 = PythonOperator(
        task_id="upload_to_s3",
        python_callable=run_upload_to_s3,
    )

    # Placeholder for now — real COPY INTO call goes here once wired to Snowflake connector
    snowflake_copy_into = BashOperator(
        task_id="snowflake_copy_into",
        bash_command='echo "TODO: run COPY INTO via Snowflake operator/hook"',
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