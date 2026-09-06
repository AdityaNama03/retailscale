with source as (
    select * from {{ source('bronze', 'customers') }}

),
renamed as (

    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        _loaded_at,
        _source_file

    from source
    where customer_id is not null

)

select * from renamed