{{ config(materialized='table') }}

with order_items as (

    select * from {{ ref('stg_order_items') }}

),

orders_dates as (

    select
        order_id,
        order_purchase_date

    from {{ ref('int_orders_enriched') }}

),

joined as (

    select
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,
        oi.price,
        oi.freight_value,
        date(oi.shipping_limit_date) as shipping_limit_date,
        od.order_purchase_date

    from order_items oi
    left join orders_dates od on oi.order_id = od.order_id

)

select * from joined