import math
import unittest

from app.services.development_plan import build_development_plan


class DevelopmentPlanTests(unittest.TestCase):
    def test_large_sql_gap_is_high_priority_and_sorted_first(self) -> None:
        plan = build_development_plan(74.0, [
            {"skill_key": "sql", "skill": "SQL", "current_rating": 2, "required_rating": 5},
            {"skill_key": "excel", "skill": "Excel", "current_rating": 3, "required_rating": 4},
        ])

        self.assertEqual(plan.items[0].skill_key, "sql")
        self.assertEqual(plan.items[0].priority, "high")
        self.assertEqual(plan.items[0].gap, 3)
        self.assertIn("joins", " ".join(plan.items[0].learning_sequence))

    def test_increasing_proficiency_reduces_gap_and_changes_priority_order(self) -> None:
        low_sql = build_development_plan(70.0, [
            {"skill_key": "sql", "skill": "SQL", "current_rating": 2, "required_rating": 5},
            {"skill_key": "excel", "skill": "Excel", "current_rating": 2, "required_rating": 4},
        ])
        high_sql = build_development_plan(70.0, [
            {"skill_key": "sql", "skill": "SQL", "current_rating": 4, "required_rating": 5},
            {"skill_key": "excel", "skill": "Excel", "current_rating": 2, "required_rating": 4},
        ])

        sql_low_item = next(item for item in low_sql.items if item.skill_key == "sql")
        sql_high_item = next(item for item in high_sql.items if item.skill_key == "sql")
        self.assertEqual(sql_low_item.gap, 3)
        self.assertEqual(sql_high_item.gap, 1)
        self.assertGreater(sql_low_item.priority_score, sql_high_item.priority_score)
        self.assertEqual(low_sql.items[0].skill_key, "sql")
        self.assertEqual(high_sql.items[0].skill_key, "excel")

    def test_career_requirement_sets_produce_different_plans(self) -> None:
        product_analyst = build_development_plan(70.0, [
            {"skill_key": "product_thinking", "skill": "Product Thinking", "current_rating": 2, "required_rating": 4},
            {"skill_key": "sql", "skill": "SQL", "current_rating": 3, "required_rating": 4},
        ])
        data_analyst = build_development_plan(70.0, [
            {"skill_key": "statistics", "skill": "Statistics", "current_rating": 2, "required_rating": 5},
            {"skill_key": "python", "skill": "Python", "current_rating": 2, "required_rating": 4},
        ])

        self.assertNotEqual([item.skill_key for item in product_analyst.items], [item.skill_key for item in data_analyst.items])
        self.assertEqual(product_analyst.items[0].skill_key, "product_thinking")
        self.assertEqual(data_analyst.items[0].skill_key, "statistics")

    def test_strong_profile_has_no_false_gaps_and_unsupported_skill_is_safe(self) -> None:
        strong = build_development_plan(88.0, [
            {"skill_key": "sql", "skill": "SQL", "current_rating": 5, "required_rating": 4},
        ])
        unsupported = build_development_plan(65.0, [
            {"skill_key": "new_skill", "skill": "New Skill", "current_rating": 1, "required_rating": 3},
        ])

        self.assertFalse(strong.items)
        self.assertIn("maintain", strong.phases[0].title.lower())
        self.assertEqual(unsupported.items[0].skill, "New Skill")
        self.assertTrue(unsupported.items[0].suggested_action)

    def test_plan_values_are_finite_and_priority_formula_is_bounded(self) -> None:
        plan = build_development_plan(74.0, [
            {"skill_key": "sql", "skill": "SQL", "current_rating": 1, "required_rating": 5},
        ])

        self.assertTrue(math.isfinite(plan.career_fit_score))
        self.assertTrue(all(1 <= item.priority_score <= 20 for item in plan.items))
        self.assertTrue(all(math.isfinite(float(item.gap)) for item in plan.items))


if __name__ == "__main__":
    unittest.main()
