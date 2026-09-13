select
    oi.order_id,
    oi.order_item_id
from {{ ref('fct_order_items') }} oi
left join {{ ref('fct_orders') }} o on oi.order_id = o.order_id
where o.order_id is null