select
    order_id,
    order_status,
    total_payment_value
from {{ ref('fct_orders') }}
where total_payment_value <= 0
  and order_status != 'canceled'