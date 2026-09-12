{{ config(materialized='table') }}

with payments as (

    select * from {{ ref('stg_payments') }}

),

orders_dates as (

    select
        order_id,
        order_purchase_date

    from {{ ref('int_orders_enriched') }}

),

joined as (

    select
        p.order_id,
        p.payment_sequential,
        p.payment_type,
        p.payment_installments,
        p.payment_value,
        od.order_purchase_date

    from payments p
    left join orders_dates od on p.order_id = od.order_id

)

select * from joined