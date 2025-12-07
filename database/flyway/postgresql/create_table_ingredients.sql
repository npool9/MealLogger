CREATE TABLE ingredients (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,

    -- Base macros
    calories_per_unit   NUMERIC NOT NULL,
    protein_per_unit    NUMERIC NOT NULL,
    carbs_per_unit      NUMERIC NOT NULL,
    fat_per_unit        NUMERIC NOT NULL,

    -- Extended macros
    fiber_per_unit          NUMERIC,
    sugar_per_unit          NUMERIC,
    saturated_fat_per_unit  NUMERIC,
    trans_fat_per_unit      NUMERIC,
    cholesterol_mg_per_unit NUMERIC,

    -- Minerals
    sodium_mg_per_unit      NUMERIC,
    potassium_mg_per_unit   NUMERIC,
    calcium_mg_per_unit     NUMERIC,
    iron_mg_per_unit        NUMERIC,

    -- Vitamins
    vitamin_a_ug_per_unit   NUMERIC,
    vitamin_c_mg_per_unit   NUMERIC,
    vitamin_d_ug_per_unit   NUMERIC,

    default_unit        TEXT NOT NULL
);
