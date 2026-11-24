import math, unittest
from gold_light_v10_timing import *

class Timing(unittest.TestCase):
    def test_format(self):
        self.assertEqual((FPS,TOTAL,TOTAL/FPS),(24,168,7))
        self.assertEqual(frame_time(1),0)
        self.assertEqual(frame_time(168),167/24)
        for f in (0,169,1.5):
            with self.assertRaises(ValueError):frame_time(f)
    def test_no_overshoot(self):
        for i in range(1,7):
            knots=[(r[0],r[i]) for r in CAMERA]
            for a,b in zip(knots,knots[1:]):
                for j in range(51):
                    v=pchip(knots,a[0]+(b[0]-a[0])*j/50)
                    self.assertGreaterEqual(v,min(a[1],b[1])-1e-9)
                    self.assertLessEqual(v,max(a[1],b[1])+1e-9)
    def test_camera_continuity(self):
        e=1e-5
        for i in range(1,7):
            knots=[(r[0],r[i]) for r in CAMERA]
            for t,_ in knots[1:-1]:
                left=(pchip(knots,t)-pchip(knots,t-e))/e
                right=(pchip(knots,t+e)-pchip(knots,t))/e
                self.assertLess(abs(left-right),.04)
        self.assertEqual(camera_channels(4.02),camera_channels(6.95))
    def test_reveal(self):
        self.assertEqual(cues(2.35)['wordmark'],0)
        self.assertEqual(cues(2.98)['wordmark'],1)
        self.assertEqual(cues(4.06)['earth'],0)
        self.assertEqual(cues(4.88)['earth'],1)
        self.assertEqual(cues(5.38)['tagline'],0)
        self.assertEqual(cues(5.85)['tagline'],1)
    def test_complement_and_continuity(self):
        prev=0
        for f in range(1,TOTAL+1):
            c=cues(frame_time(f))
            self.assertTrue(all(0<=v<=1 for v in c.values()))
            self.assertAlmostEqual(c['stage']+c['earth'],1)
            self.assertGreaterEqual(c['earth'],prev)
            self.assertLess(c['earth']-prev,.10)
            prev=c['earth']
    def test_horizon_geometry(self):
        p=horizon_center(100,95)
        self.assertLess(p[1],0)
        self.assertAlmostEqual(horizon_row(.5),.79,places=6)
        # Broad horizon touches both screen edges; never a tiny globe.
        self.assertIsNotNone(horizon_row(0))
        self.assertAlmostEqual(horizon_row(0),horizon_row(1),places=7)
        self.assertGreater(horizon_row(0),.79)
        self.assertLess(horizon_row(0),1.0)
    def test_preview_density(self):
        f=preview_frames()
        self.assertEqual(f[0],1);self.assertEqual(f[-1],168)
        self.assertGreaterEqual(len([n for n in f if 4*24<n<5*24+2]),5)
        self.assertEqual(len(f),len(set(f)))
    def test_beat_order(self):
        for a,b in zip(REFERENCE_BEATS,REFERENCE_BEATS[1:]):
            self.assertLess(a[0],b[0]);self.assertLess(a[1],b[1])
        self.assertEqual(REFERENCE_BEATS[4][1],1.95)
        self.assertEqual(shot_manifest()['creativeApproval'],False)

if __name__=='__main__':unittest.main()
