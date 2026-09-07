
with source as (

    select * from {{ source('bronze', 'geolocation') }}

),

renamed as (

    select
        geolocation_zip_code_prefix::varchar as geolocation_zip_code_prefix,
        geolocation_lat::float as geolocation_lat,
        geolocation_lng::float as geolocation_lng,
        geolocation_city,
        geolocation_state,
        _loaded_at,
        _source_file
    from source
    where geolocation_zip_code_prefix is not null

)

select * from renamed