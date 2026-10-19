import csv
from pathlib import Path
import unittest
import numpy as np
from model import (solve, G, USAGE, BASE_PLAN, BASIS_INVERSE,
                   baseline_basis_values, baseline_basis_is_feasible,
                   baseline_prediction, alternative_plans)

ROOT = Path(__file__).resolve().parents[1]


class ModelChecks(unittest.TestCase):
    def test_baseline(self):
        s = solve()
        self.assertEqual(s.status, "Optimal")
        np.testing.assert_allclose(s.plan, [33.2, 22.4, 8.], atol=1e-7)
        self.assertAlmostEqual(s.profit, 2929.6)
        np.testing.assert_allclose(s.margins, [0, 0, 23.6, 0, 44], atol=1e-7)
        np.testing.assert_allclose(s.shadow_prices, [11.2, 1.6, 0, -5.8, 0], atol=1e-7)

    def test_local_prediction(self):
        s = solve((250., 180., 200.))
        self.assertAlmostEqual(s.profit, 3041.6)
        self.assertAlmostEqual(s.profit, baseline_prediction(s.capacities))

    def test_resource_saturation(self):
        self.assertAlmostEqual(solve((300., 180., 200.)).profit, 3260.)
        self.assertAlmostEqual(solve((240., 250., 200.)).profit, 3000.)

    def test_joint_counterexample(self):
        caps = (269.5, 124., 200.)
        s = solve(caps)
        self.assertFalse(baseline_basis_is_feasible(caps))
        self.assertAlmostEqual(baseline_basis_values(caps)[1], -5.9)
        self.assertAlmostEqual(baseline_prediction(caps), 3170.4)
        self.assertAlmostEqual(s.profit, 2840.)
        np.testing.assert_allclose(s.plan, [50., 0., 8.], atol=1e-7)

    def test_compensating_joint_change(self):
        caps = (190., 160., 200.)
        self.assertTrue(baseline_basis_is_feasible(caps))
        self.assertAlmostEqual(solve(caps).profit, 2337.6)
        self.assertAlmostEqual(solve(caps).profit, baseline_prediction(caps))

    def test_infeasibility_limits(self):
        for caps in [(39.99, 180., 200.), (240., 23.99, 200.), (240., 180., 31.99)]:
            with self.subTest(caps=caps):
                s = solve(caps)
                self.assertEqual(s.status, "Infeasible")
                self.assertIsNone(s.profit)
                self.assertIsNone(s.plan)
        self.assertEqual(solve(minimum_c=50.).status, "Infeasible")

    def test_profit_adaptation(self):
        s = solve(profit_a=60.)
        self.assertAlmostEqual(s.profit, 3440.)
        self.assertAlmostEqual(s.profit - BASE_PLAN @ [60., 40., 55.], 112.)

    def test_minimum_c_range(self):
        for q in [0., 8., 15., 30.]:
            self.assertAlmostEqual(solve(minimum_c=q).profit, 2976.-5.8*q)
        self.assertAlmostEqual(solve().shadow_prices[3], -5.8)

    def test_basis_inverse(self):
        basis = np.array([[4,3,5,0,0],[2,4,3,0,0],[3,2,4,1,0],
                          [0,0,1,0,0],[-2,1,0,0,1]], float)
        np.testing.assert_allclose(basis @ BASIS_INVERSE, np.eye(5), atol=1e-12)
        np.testing.assert_allclose(baseline_basis_values(), [33.2,22.4,8,23.6,44], atol=1e-7)

    def test_alternative_optima_are_feasible(self):
        rhs = np.array([240.,180.,200.,-8.,0.])
        for p in [30.,470/11,160/3]:
            plans = alternative_plans(p)
            self.assertEqual(len(plans),3)
            optimum = solve(profit_a=p).profit
            for q in plans:
                self.assertTrue(np.all(G @ q <= rhs + 1e-7))
                self.assertTrue(np.all(q >= -1e-7))
                self.assertAlmostEqual(q @ [p,40.,55.],optimum)

    def test_all_notebook_reference_cases(self):
        with open(ROOT/'data'/'notebook_reference_cases.csv') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows),267)
        for row in rows:
            with self.subTest(case=row['Case']):
                caps=tuple(float(row[k]) for k in ['Machine capacity','Staff capacity','Material capacity'])
                s=solve(caps,float(row['Unit profit A']),float(row['Minimum C requirement']))
                self.assertEqual(s.status,'Optimal')
                self.assertLessEqual(abs(s.profit-float(row['Profit'])),1e-6)
                rhs=np.r_[caps,-s.minimum_c,0.]
                self.assertTrue(np.all(G @ s.plan <= rhs+1e-6))
                self.assertTrue(np.all(s.plan>=-1e-6))

    def test_invalid_inputs(self):
        for caps in [(-1.,180.,200.), (240.,180.), (np.nan,180.,200.)]:
            with self.assertRaises(ValueError):solve(caps)
        with self.assertRaises(ValueError):solve(minimum_c=-1.)


if __name__ == '__main__':
    unittest.main()
