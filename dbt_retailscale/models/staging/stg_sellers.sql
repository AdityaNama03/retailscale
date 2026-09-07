with source as (

    select * from {{ source('bronze', 'sellers') }}

),

renamed as (

    select
        seller_id,
        seller_zip_code_prefix::varchar as seller_zip_code_prefix,
        seller_city,
        seller_state,
        _loaded_at,
        _source_file
    from source
    where seller_id is not null

)

select * from renamed