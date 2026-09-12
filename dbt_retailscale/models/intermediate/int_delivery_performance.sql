{{ config(materialized='table') }}

with orders as (

    select
        order_id,
        order_purchase_date,
        order_delivered_date,
        date(order_estimated_delivery_at) as order_estimated_delivery_date

    from {{ ref('int_orders_enriched') }}

),

calculated as (

    select
        order_id,
        order_purchase_date,
        order_delivered_date,
        order_estimated_delivery_date,
        datediff(day, order_estimated_delivery_date, order_delivered_date) as delivery_delay_days,
        case
            when order_delivered_date is null then null
            when datediff(day, order_estimated_delivery_date, order_delivered_date) > 0 then true
            else false
        end as is_late

    from orders

)

select * from calculated