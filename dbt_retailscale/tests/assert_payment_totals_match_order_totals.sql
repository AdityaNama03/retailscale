with payments_agg as (
    select 
        order_id, 
        sum(payment_value) as total_price 
    from {{ ref('fct_payments') }}
    group by order_id
)

select 
    p.order_id, 
    p.total_price, 
    o.total_payment_value,
    abs(p.total_price - o.total_payment_value) as difference
from payments_agg p
join {{ ref('fct_orders') }} o on p.order_id = o.order_id
where abs(p.total_price - o.total_payment_value) > 0.01