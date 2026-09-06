with source as (

    select * from {{ ref('int_orders_enriched') }}

),

fact_orders as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_at as purchase_date,
        order_approved_at as approved_date,
        order_delivered_customer_at as delivery_date,
        total_payment_value,
        payment_count,

        case
            when order_delivered_customer_at is null then null
            when order_delivered_customer_at > order_estimated_delivery_at then true
            else false
        end as is_late_delivery

    from source

)

select * from fact_orders