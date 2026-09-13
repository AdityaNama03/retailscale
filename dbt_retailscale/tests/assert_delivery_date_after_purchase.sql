select
    order_id,
    order_purchase_date,
    order_delivered_date
from {{ ref('fct_delivery_performance') }}
where order_delivered_date < order_purchase_date