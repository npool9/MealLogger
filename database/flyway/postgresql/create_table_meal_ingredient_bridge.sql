CREATE TABLE meal_ingredient_bridge (
    meal_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity DECIMAL NOT NULL,
    unit TEXT,
    PRIMARY KEY (meal_id, ingredient_id),
    FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE RESTRICT,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT
);