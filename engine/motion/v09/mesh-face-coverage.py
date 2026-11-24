import bpy,json,pathlib,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/tmp/grp-v09');raw=(root/'official-mask.bin').read_bytes()
W,H=1536,934;center=(744.,453.5);unit=6/932
names=('silver-monogram','gold-r','silver-wordmark','gold-descriptor')
def sample():
    s=bpy.context.scene;s.frame_set(120);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    out={}
    for idx,name in enumerate(names,1):
        ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);m=ev.to_mesh()
        try:
            m.calc_loop_triangles();vertices=[ev.matrix_world@v.co for v in m.vertices]
            faces=[tuple(t.vertices) for t in m.loop_triangles]
            bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
            pts=[(i%W,i//W) for i,c in enumerate(raw) if c==idx]
            xmin=max(2,min(x for x,y in pts)-5);xmax=min(W-3,max(x for x,y in pts)+5)
            ymin=max(2,min(y for x,y in pts)-5);ymax=min(H-3,max(y for x,y in pts)+5)
            missed=unexpected=positive=negative=0;misses=[];extras=[]
            for y in range(ymin,ymax+1,3):
                for x in range(xmin,xmax+1,3):
                    v=[raw[(y+dy)*W+x+dx]==idx for dy in (-2,0,2) for dx in (-2,0,2)]
                    if any(v) and not all(v):continue
                    expected=all(v)
                    o=Vector(((x+.5-center[0])*unit,(center[1]-y-.5)*unit,4))
                    loc,norm,face,dist=bvh.ray_cast(o,Vector((0,0,-1)),8)
                    found=loc is not None
                    if expected:
                        positive+=1
                        if not found:missed+=1;misses.append((x,y))
                    else:
                        negative+=1
                        if found:unexpected+=1;extras.append((x,y))
            out[name]={'interiorSamples':positive,'exteriorSamples':negative,'missingFaceSamples':missed,'unexpectedFaceSamples':unexpected,'interiorCoverage':round(1-missed/max(1,positive),6),'exteriorCorrectness':round(1-unexpected/max(1,negative),6),'firstMisses':misses[:10],'firstExtras':extras[:10],'triangles':len(faces)}
        finally:ev.to_mesh_clear()
    return out
report={}
for name,path in [('v09b',root/'preview/gold-light-v09b.blend'),('v09d_rejected',root/'rejected-v09d/gold-light-v09d.blend'),('v09e',root/'final/gold-light-v09e.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(path));report[name]=sample()
(root/'mesh-face-coverage.json').write_text(json.dumps(report,indent=2));print('MESH_FACE_COVERAGE',json.dumps(report),flush=True)
