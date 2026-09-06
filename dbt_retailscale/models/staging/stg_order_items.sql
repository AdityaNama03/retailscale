with source as (

    select * from {{ source('bronze', 'order_items') }}

),

renamed as (

    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date::timestamp_ntz as shipping_limit_date,
        price::number(10,2) as price,
        freight_value::number(10,2) as freight_value,
        _loaded_at,
        _source_file
    from source
    where order_id is not null

)

select * from renamed