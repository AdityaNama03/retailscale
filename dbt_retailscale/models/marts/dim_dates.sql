{{ config(materialized='table') }}

with date_spine as (

    select dateadd(day, seq4(), '2016-09-04'::date) as date_day
    from table(generator(rowcount => 774))

)

select
    date_day,
    year(date_day)          as year,
    quarter(date_day)       as quarter,
    month(date_day)         as month,
    monthname(date_day)     as month_name,
    day(date_day)           as day_of_month,
    dayofweek(date_day)     as day_of_week,
    dayname(date_day)       as day_name,
    case when dayofweek(date_day) in (0, 6) then true else false end as is_weekend

from date_spine