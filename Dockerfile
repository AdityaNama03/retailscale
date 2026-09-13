FROM apache/airflow:2.9.3

RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt" \
    apache-airflow-providers-snowflake

RUN pip install --no-cache-dir dbt-snowflake