CREATE TABLE meals (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    servings TEXT,
    recipe_url TEXT,
    created_at TIMESTAMP
);