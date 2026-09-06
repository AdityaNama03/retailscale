with source as (

    select * from {{ source('bronze', 'payments') }}

),

renamed as (

    select
        order_id,
        payment_sequential::integer as payment_sequential,
        payment_type,
        payment_installments::integer as payment_installments,
        payment_value::number(10,2) as payment_value,
        _loaded_at,
        _source_file

    from source
    where order_id is not null

)

select * from renamed