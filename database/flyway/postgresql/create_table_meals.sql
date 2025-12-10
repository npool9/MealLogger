CREATE TABLE meals (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    servings TEXT,
    serving_size BIGINT,
    serving_unit CHARACTER VARYING,
    recipe_url TEXT,
    created_at TIMESTAMP
);