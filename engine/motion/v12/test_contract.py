import unittest
import transition_contract as t
import sculpt_profile as p
class Contract(unittest.TestCase):
    def test_transition(self):
        self.assertGreater(t.validate()["transitionSeconds"],1.5)
    def test_leading_limb(self):
        self.assertGreater(t.pixel(116,0)["visible_earth"],t.pixel(116,.195)["visible_earth"])
    def test_no_uncovered_horizon(self):
        self.assertLess(max(t.pixel(f,y)["uncovered"] for f in range(1,169) for y in (0,.05,.10,.15,.195)),.12)
    def test_crown(self):
        self.assertEqual(p.validate()["outwardSilhouetteGrowth"],0)
        self.assertGreater(p.CROWN_WIDTH,4*.027)
    def test_narrow_strokes(self):
        self.assertLess(p.surface_z(.025),p.surface_z(.10))
        self.assertGreater(p.surface_z(.025),p.HALF_SIDE)
    def test_end_frame(self):
        self.assertEqual(t.cues(168)["tagline"],1)
        self.assertEqual(t.pixel(168,.195)["stage_keep"],0)
        self.assertEqual(t.pixel(168,.195)["visible_earth"],1)
if __name__=="__main__":unittest.main()
