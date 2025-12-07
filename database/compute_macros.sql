-- Replace $1 with the meal id (or use a prepared statement parameter)
SELECT
  m.id,
  m.name,
  m.servings,

  -- totals (whole recipe)
  SUM( COALESCE(i.calories_per_unit,0)  * mi.quantity )                     AS total_calories,
  SUM( COALESCE(i.protein_per_unit,0)   * mi.quantity )                     AS total_protein,
  SUM( COALESCE(i.carbs_per_unit,0)     * mi.quantity )                     AS total_carbs,
  SUM( COALESCE(i.fat_per_unit,0)       * mi.quantity )                     AS total_fat,

  SUM( COALESCE(i.fiber_per_unit,0)     * mi.quantity )                     AS total_fiber,
  SUM( COALESCE(i.sugar_per_unit,0)     * mi.quantity )                     AS total_sugar,
  SUM( COALESCE(i.saturated_fat_per_unit,0) * mi.quantity )                AS total_saturated_fat,
  SUM( COALESCE(i.trans_fat_per_unit,0) * mi.quantity )                     AS total_trans_fat,
  SUM( COALESCE(i.cholesterol_mg_per_unit,0) * mi.quantity )               AS total_cholesterol_mg,

  SUM( COALESCE(i.sodium_mg_per_unit,0)  * mi.quantity )                    AS total_sodium_mg,
  SUM( COALESCE(i.potassium_mg_per_unit,0) * mi.quantity )                  AS total_potassium_mg,
  SUM( COALESCE(i.calcium_mg_per_unit,0) * mi.quantity )                    AS total_calcium_mg,
  SUM( COALESCE(i.iron_mg_per_unit,0)    * mi.quantity )                    AS total_iron_mg,

  SUM( COALESCE(i.vitamin_a_ug_per_unit,0) * mi.quantity )                  AS total_vitamin_a_ug,
  SUM( COALESCE(i.vitamin_c_mg_per_unit,0) * mi.quantity )                  AS total_vitamin_c_mg,
  SUM( COALESCE(i.vitamin_d_ug_per_unit,0) * mi.quantity )                  AS total_vitamin_d_ug,

  -- per-serving (guard against zero servings)
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.calories_per_unit,0) * mi.quantity ) / m.servings END AS calories_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.protein_per_unit,0) * mi.quantity ) / m.servings END  AS protein_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.carbs_per_unit,0) * mi.quantity ) / m.servings END    AS carbs_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.fat_per_unit,0) * mi.quantity ) / m.servings END      AS fat_per_serving,

  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.fiber_per_unit,0) * mi.quantity ) / m.servings END    AS fiber_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.sugar_per_unit,0) * mi.quantity ) / m.servings END    AS sugar_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.saturated_fat_per_unit,0) * mi.quantity ) / m.servings END
                                                                               AS saturated_fat_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.trans_fat_per_unit,0) * mi.quantity ) / m.servings END
                                                                               AS trans_fat_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.cholesterol_mg_per_unit,0) * mi.quantity ) / m.servings END
                                                                               AS cholesterol_mg_per_serving,

  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.sodium_mg_per_unit,0) * mi.quantity ) / m.servings END AS sodium_mg_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.potassium_mg_per_unit,0) * mi.quantity ) / m.servings END AS potassium_mg_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.calcium_mg_per_unit,0) * mi.quantity ) / m.servings END  AS calcium_mg_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.iron_mg_per_unit,0) * mi.quantity ) / m.servings END     AS iron_mg_per_serving,

  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.vitamin_a_ug_per_unit,0) * mi.quantity ) / m.servings END AS vitamin_a_ug_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.vitamin_c_mg_per_unit,0) * mi.quantity ) / m.servings END AS vitamin_c_mg_per_serving,
  CASE WHEN COALESCE(m.servings,0) = 0 THEN NULL
       ELSE SUM( COALESCE(i.vitamin_d_ug_per_unit,0) * mi.quantity ) / m.servings END AS vitamin_d_ug_per_serving

FROM meals m
JOIN meal_ingredients mi ON m.id = mi.meal_id
JOIN ingredients i ON mi.ingredient_id = i.id
WHERE m.id = $1
GROUP BY m.id, m.name, m.servings;
