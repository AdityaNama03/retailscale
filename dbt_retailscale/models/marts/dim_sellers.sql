{{ config(materialized='table') }}

select 
        seller_id,
        seller_zip_code_prefix,
        coalesce(seller_city, 'Unknown') as seller_city,
        coalesce(seller_state, 'Unknown') as seller_state,

from {{ ref('stg_sellers') }}