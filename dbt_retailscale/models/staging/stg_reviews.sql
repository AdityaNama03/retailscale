-- stg_reviews.sql

with source as (

    select * from {{ source('bronze', 'reviews') }}

),

renamed as (

    select
        review_id,
        order_id,
        review_score::integer as review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date::timestamp as review_creation_date,
        review_answer_timestamp::timestamp as review_answer_timestamp,
        _loaded_at,
        _source_file
    from source
    where review_id is not null

)

select * from renamed