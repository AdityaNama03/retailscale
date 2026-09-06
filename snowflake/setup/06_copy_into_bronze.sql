-- RetailScale: COPY INTO statements for remaining bronze tables
-- orders and customers already done.

USE DATABASE retailscale_dev;
USE SCHEMA bronze;

-- products
COPY INTO products
FROM (
    SELECT
        $1, $2, $3, $4, $5, $6, $7, $8, $9,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/products/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- sellers
COPY INTO sellers
FROM (
    SELECT
        $1, $2, $3, $4,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/sellers/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- order_items
COPY INTO order_items
FROM (
    SELECT
        $1, $2, $3, $4, $5, $6, $7,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/order_items/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- payments
COPY INTO payments
FROM (
    SELECT
        $1, $2, $3, $4, $5,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/payments/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- reviews
COPY INTO reviews
FROM (
    SELECT
        $1, $2, $3, $4, $5, $6, $7,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/reviews/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- geolocation
COPY INTO geolocation
FROM (
    SELECT
        $1, $2, $3, $4, $5,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/geolocation/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- category_translation
COPY INTO category_translation
FROM (
    SELECT
        $1, $2,
        CURRENT_TIMESTAMP(),
        METADATA$FILENAME
    FROM @retailscale_bronze_stage/category_translation/
)
FILE_FORMAT = (FORMAT_NAME = 'csv_format')
ON_ERROR = 'CONTINUE';

-- Sanity check row counts across all tables
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM orders
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'category_translation', COUNT(*) FROM category_translation;
