{{ config(materialized='table') }}

select
    product_id,
    coalesce(product_category_name, 'Unknown') as product_category_name,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm

from {{ ref('stg_products') }}