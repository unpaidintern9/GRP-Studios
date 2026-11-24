import unittest, math
from horizon_math import *
class Horizon(unittest.TestCase):
    def test_old_geometry_misses_edges(self):
        frame=(-18/52,18/52,-10.125/52,10.125/52,-1)
        c=sphere_center(frame,100,1.85,.77)
        self.assertIsNone(horizon_row(frame,c,100,0))
        self.assertIsNone(horizon_row(frame,c,100,1))
    def test_width_at_lenses_and_shifts(self):
        for focal in (45,52,65,85):
            for y in (-.04,0,.04):
                frame=(-18/focal,18/focal,-10.125/focal+y,10.125/focal+y,-1)
                q=fit_horizon(frame)
                self.assertAlmostEqual(q['rows'][1],.805,places=3)
                self.assertAlmostEqual(q['rows'][0],q['rows'][2],places=6)
                self.assertLessEqual(max(q['rows']),.877)
                self.assertGreater(q['ratio'],1.005-1e-9)
    def test_cues(self):
        p=0
        for f in range(1,169):
            q=closing_cues(f)
            self.assertAlmostEqual(q['earth']+q['stage'],1)
            self.assertGreaterEqual(q['earth'],p)
            self.assertTrue(all(-1e-10<=v<=1+1e-10 for v in q.values()))
            p=q['earth']
        self.assertEqual(closing_cues(113)['earth'],0)
        self.assertEqual(closing_cues(127)['earth'],1)
        self.assertAlmostEqual(closing_cues(141)['sun'],1)
        self.assertEqual(closing_cues(155)['tagline'],1)
    def test_transition_velocities(self):
        for f in (113,127):
            e=1e-3
            self.assertLess(abs(closing_cues(f+e)['earth']-closing_cues(f-e)['earth'])/(2*e),1e-6)
if __name__=='__main__':unittest.main()
