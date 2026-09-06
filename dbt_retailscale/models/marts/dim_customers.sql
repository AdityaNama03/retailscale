with snapshot as (

    select * from {{ ref('snap_customers') }}

),

final as (

    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,

        dbt_valid_from as valid_from,
        dbt_valid_to as valid_to,
        case when dbt_valid_to is null then true else false end as is_current

    from snapshot

)

select * from final