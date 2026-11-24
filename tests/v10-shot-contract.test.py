import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine/motion/v10"))
from shot_contract import *
class Contract(unittest.TestCase):
    def test_anchors(self):
        self.assertEqual(ANCHORS,tuple(s[0] for s in SHOTS[:-1]))
        self.assertEqual(TOTAL/FPS,7)
    def test_safe_region(self):
        self.assertEqual(widescreen(0,0),(.21875,0))
        self.assertEqual(widescreen(1,1),(.78125,1))
        self.assertFalse(bounds_ok((.1,.8,.1,.9),"mark"))
        self.assertTrue(bounds_ok((.24,.76,.1,.9),"mark"))
    def test_closing(self):
        self.assertEqual(dict(EARTH)[113],0)
        self.assertEqual(dict(EARTH)[127],1)
        self.assertEqual(dict(SUN)[141],1)
        self.assertEqual(dict(TAG)[155],1)
        self.assertEqual(dict(WORDMARK)[71],0)
        self.assertEqual(dict(WORDMARK)[85],1)
        self.assertTrue(all(s[1:]==SHOTS[6][1:] for s in SHOTS[6:]))
if __name__=="__main__":unittest.main()
