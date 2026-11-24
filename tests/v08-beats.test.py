import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine/motion"))
from gold_light_v08_beats import *
class Timing(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(TOTAL/FPS,7)
        self.assertEqual(retime(120),168)
        self.assertEqual(retime(1),1)
        self.assertTrue(all(retime(i+1)>retime(i) for i in range(1,120)))
    def test_reveal(self):
        self.assertEqual(dict(WORDMARK)[77],0)
        self.assertEqual(dict(WORDMARK)[88],1)
        self.assertEqual(dict(TAGLINE)[139],0)
        self.assertEqual(dict(TAGLINE)[150],1)
        self.assertEqual(retime(78),109)
    def test_shot_interval(self):
        self.assertGreater(retime(39)-retime(30),6)
        self.assertEqual(retime(110),157)
if __name__=="__main__":unittest.main()
