{{ config(materialized='table') }}

select
    order_id,
    order_purchase_date,
    order_estimated_delivery_date,
    order_delivered_date,
    delivery_delay_days,
    is_late

from {{ ref('int_delivery_performance') }}