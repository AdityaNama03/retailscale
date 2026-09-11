with orders as (

    select *, date(order_purchase_at) as order_purchase_date, date(order_delivered_customer_at) as order_delivered_date
 from {{ ref('stg_orders') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

payments_agg as (

    select
        order_id,
        sum(payment_value) as total_payment_value,
        count(*) as payment_count,
        max(payment_installments) as max_installments

    from {{ ref('stg_payments') }}
    group by order_id

),

joined as (

    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_purchase_at,
        o.order_approved_at,
        o.order_delivered_carrier_at,
        o.order_delivered_customer_at,
        o.order_estimated_delivery_at,
        o.order_purchase_date,
        o.order_delivered_date,

        c.customer_unique_id,
        c.customer_city,
        c.customer_state,

        p.total_payment_value,
        p.payment_count,
        p.max_installments

    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join payments_agg p on o.order_id = p.order_id

)

select * from joined