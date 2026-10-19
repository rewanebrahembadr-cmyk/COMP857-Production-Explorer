from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


class InterfaceChecks(unittest.TestCase):
    def start(self):
        app=AppTest.from_file(str(APP),default_timeout=90).run()
        self.assertEqual(len(app.exception),0)
        return app

    def test_baseline_and_all_pages(self):
        app=self.start()
        self.assertEqual(app.metric[0].value,'£2,929.60')
        for page in ['Resources','Unit profit','Joint changes','Minimum C','Validation and model']:
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception),0,page)
        self.assertEqual(app.metric[0].value,'267')
        self.assertEqual(app.metric[1].value,'267')

    def test_resource_slider_and_infeasible_state(self):
        app=self.start()
        app.sidebar.radio[0].set_value('Resources').run()
        app.slider[0].set_value(250.).run()
        self.assertEqual(app.metric[0].value,'£3,041.60')
        app.slider[0].set_value(0.).run()
        self.assertEqual(len(app.exception),0)
        self.assertGreater(len(app.error),0)
        self.assertEqual(len(app.metric),0)

    def test_joint_counterexample_and_compensation(self):
        app=self.start()
        app.sidebar.radio[0].set_value('Joint changes').run()
        app.selectbox[0].set_value('Counterexample: 269.5 machines, 124 staff').run()
        self.assertEqual(app.metric[0].value,'£2,840.00')
        self.assertGreater(len(app.warning),0)
        app.selectbox[0].set_value('Compensating change: 190 machines, 160 staff').run()
        self.assertEqual(app.metric[0].value,'£2,337.60')
        self.assertGreater(len(app.success),0)

    def test_exact_profit_boundary_and_minimum_c(self):
        app=self.start()
        app.sidebar.radio[0].set_value('Unit profit').run()
        app.selectbox[0].set_value('30').run()
        self.assertEqual(app.metric[0].value,'£2,640.00')
        self.assertEqual(len(app.exception),0)
        app.sidebar.radio[0].set_value('Minimum C').run()
        app.slider[0].set_value(50.).run()
        self.assertGreater(len(app.error),0)
        self.assertEqual(len(app.exception),0)


if __name__ == '__main__':
    unittest.main()
