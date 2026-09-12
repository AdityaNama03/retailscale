{{ config(materialized='table') }}

with products as (

    select * from {{ ref('stg_products') }}

),

translation as (

    select * from {{ ref('product_category_name_translation') }}

),

joined as (

    select
        p.product_id,
        coalesce(t.product_category_name_english, p.product_category_name, 'Unknown') as product_category_name,
        p.product_name_lenght,
        p.product_description_lenght,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm

    from products p
    left join translation t on p.product_category_name = t.product_category_name

)

select * from joined