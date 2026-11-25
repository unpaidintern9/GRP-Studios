import math, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine/motion'))
from gold_light_v07_beats import face_shot, shot_plan, WORDMARK_KEYS, SHIFT_KEYS

class BeatTests(unittest.TestCase):
    def test_projection(self):
        for scale in (.5, 1, 3):
            h=3*scale
            for coverage in (2.4, 1.28, .86):
                _,p,t,l,_=face_shot(20,(1,2,.2),h,coverage,52,(.15,.09),-14)
                self.assertAlmostEqual(h*l/(20.25*math.dist(p,t)),coverage)
                self.assertGreater(p[2],t[2])
    def test_order_and_reveal(self):
        shots=shot_plan((-3,3,-1,2),(-1,2,-1,2),-3,-2,(-2.5,0))
        self.assertEqual([q[0] for q in shots],[1,11,20,30,39,49,59,69,78,98,110,120])
        self.assertGreater(shots[3][1][2],shots[2][1][2])
        self.assertTrue(all(v==0 for f,v in WORDMARK_KEYS if f<=49))
        self.assertEqual(dict(WORDMARK_KEYS)[50],0)
        self.assertEqual(dict(WORDMARK_KEYS)[59],1)
        self.assertEqual(dict(SHIFT_KEYS)[50],1)
        self.assertEqual(dict(SHIFT_KEYS)[59],0)
    def test_invalid(self):
        with self.assertRaises(ValueError):face_shot(1,(0,0,0),0,1,50,(0,0),0)
        with self.assertRaises(ValueError):face_shot(1,(0,0,0),1,1,50,(10,0),0)

if __name__=='__main__':unittest.main()
