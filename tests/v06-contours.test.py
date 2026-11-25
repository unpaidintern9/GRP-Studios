import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine/motion"))
from gold_light_v06_contours import fit_group,mask,sampled
class Contours(unittest.TestCase):
    def test_dense_collinear_knots_are_removed(self):
        a=[(x,10) for x in range(10,90)]+[(90,y) for y in range(10,90)]+[(x,90) for x in range(90,10,-1)]+[(10,y) for y in range(90,10,-1)]
        curves,r=fit_group([a],100,100,True)
        self.assertLess(r["fittedKnots"],r["sourceKnots"])
        self.assertGreaterEqual(r["sampledSilhouetteIoU"],.992)
    def test_hole_is_retained(self):
        a=[(10,10),(90,10),(90,90),(10,90)];b=[(40,40),(60,40),(60,60),(40,60)]
        c,r=fit_group([a,b],100,100,False)
        self.assertEqual(r["loopCount"],2);self.assertEqual(mask([sampled(x) for x in c],100,100)[50]>>50&1,0)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):fit_group([],100,100,True)
if __name__=="__main__":unittest.main()
