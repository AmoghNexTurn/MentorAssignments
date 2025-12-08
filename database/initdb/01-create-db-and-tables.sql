CREATE TABLE big_data (
    id          bigserial PRIMARY KEY,
    user_id     int,
    category    int,
    payload     text
);

INSERT INTO big_data (user_id, category, payload)
SELECT
    (random() * 1000000)::int,                -- many distinct users
    (random() * 100)::int,                    -- 0–100 categories
    md5(random()::text)                       -- random text
FROM generate_series(1, 200000);            -- 2M rows

CREATE TABLE big_data_2 AS TABLE big_data;

CREATE INDEX idx_big_data_user_id
ON big_data (user_id);

CREATE INDEX idx_big_data_category
ON big_data (category);
