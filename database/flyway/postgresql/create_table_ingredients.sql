CREATE TABLE ingredients (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,

    -- Base macros
    calories_per_gram   NUMERIC NOT NULL,
    protein_per_gram    NUMERIC NOT NULL,
    carbs_per_gram      NUMERIC NOT NULL,
    fat_per_gram        NUMERIC NOT NULL,

    -- Extended macros
    fiber_per_gram          NUMERIC,
    sugar_per_gram          NUMERIC,
    saturated_fat_per_gram  NUMERIC,
    trans_fat_per_gram      NUMERIC,
    cholesterol_per_gram    NUMERIC,

    -- Minerals
    sodium_per_gram         NUMERIC,
    potassium_per_gram      NUMERIC,
    calcium_per_gram        NUMERIC,
    iron_per_gram           NUMERIC,

    -- Vitamins
    vitamin_a_per_gram      NUMERIC,
    vitamin_c_per_gram      NUMERIC,
    vitamin_d_per_gram      NUMERIC
);
