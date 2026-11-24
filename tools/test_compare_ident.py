import importlib.util, pathlib, unittest
spec=importlib.util.spec_from_file_location('compare_ident',pathlib.Path(__file__).with_name('compare-ident.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CompareTests(unittest.TestCase):
    def test_legacy(self):
        self.assertEqual(m.beat_indices(5),[round(i*9.6) for i in range(12)])
    def test_seven(self):
        f=m.beat_indices(7);self.assertEqual(len(f),12);self.assertEqual(f[6],77);self.assertEqual(f[-1],139);self.assertTrue(all(a<b for a,b in zip(f,f[1:])));self.assertLess(f[-1],167)
    def test_probe(self):
        d={'streams':[{'codec_type':'video','codec_name':'h264','width':1920,'height':1080,'avg_frame_rate':'24/1','sample_aspect_ratio':'1:1'}],'format':{'duration':'7.000'}}
        m.validate_probe(d,7)
        with self.assertRaises(ValueError):m.validate_probe(d,5)
        d['streams'].append({'codec_type':'audio'})
        with self.assertRaises(ValueError):m.validate_probe(d,7)
    def test_duration(self):
        with self.assertRaises(ValueError):m.beat_indices(6)
if __name__=='__main__':unittest.main()
