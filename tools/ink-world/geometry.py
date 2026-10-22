"""Original Japanese ink-world geometry, authored as native Unity mesh assets.

Offline authoring only: no external assets, runtime generators or scene mutation.
Run: python tools/ink-world/geometry.py
Parts share material families, fixed seeds and metre units. Render previews with
preview_geometry.py; Blender previews are not verification of Unity rendering.
"""
from pathlib import Path
import sys, math, json, random
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/village'))
import native
from native import Mesh

OUT = ROOT / 'Sunward-Unity/Assets/Sunward/Generated/InkWorld'
WOOD = (.40, .24, .12)
DARK = (.16, .12, .09)
INK = (.09, .12, .095)
GREEN = (.19, .39, .20)
JADE = (.29, .48, .23)
GOLD = (.72, .48, .19)


def irregular_solid(m, center, scale, color, seed, layers=7, rays=24, terrace=False):
    """Closed, scalloped non-spherical foliage pad or undercut stone shelf."""
    rng = random.Random(seed)
    phase = rng.random() * math.tau
    profiles = ([.64, .94, 1., .92, .93, .69, .48]
                if terrace else [.55, .85, 1., .93, .76, .48, .08])
    rings = []
    for j in range(layers):
        t = j / (layers - 1)
        profile = float(np.interp(t,np.linspace(0,1,len(profiles)),profiles))
        ring = []
        for k in range(rays):
            a = k * math.tau / rays
            lobe = 1 + .12 * math.sin(3*a+phase) + .065 * math.sin(7*a-phase)
            radius = profile * lobe
            if terrace:
                radius *= 1 + .035*math.sin(a*11+j*2.8)
            y = t + .04*math.sin(a*5+phase)*math.sin(t*math.pi)
            p = (center[0] + math.cos(a)*radius*scale[0] + .08*t*scale[0],
                 center[1] + y*scale[1],
                 center[2] + math.sin(a)*radius*scale[2])
            tone = .81 + .22*t + .04*math.sin(a*3+phase)
            ring.append(m.vertex(p,np.array(color)*tone,(k/rays,t)))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for k in range(rays):
            kk=(k+1)%rays
            m.tri.extend([(a[k],b[k],a[kk]),(a[kk],b[k],b[kk])])
    for ids, rev in [(rings[0],False),(rings[-1],True)]:
        mid=m.vertex(np.mean(np.array(m.v)[ids],axis=0),color,(.5,.5))
        for k in range(rays):
            a,b=ids[k],ids[(k+1)%rays]
            m.tri.append((mid,b,a) if rev else (mid,a,b))


def branch(m, points, widths, rng, color=WOOD):
    m.tube(points,widths,color,n=12,groove=.15)
    # Raised torn ridges follow the living branch, including its bends.
    for scar in range(2):
        angle=scar*math.pi+rng.random()*.15
        path=[]
        for j,(p,w) in enumerate(zip(points,widths)):
            path.append(np.array(p)+np.array([math.cos(angle+j*.15)*w*.96,
                                             0,math.sin(angle+j*.15)*w*.96]))
        m.tube(path,[max(.004,w*.055) for w in widths],np.array(color)*.65,n=4)


def knot(m, center, rx, ry, color=WOOD):
    p=np.array(center)
    for level in range(3):
        fac=1-level*.22
        points=[p+np.array([math.sin(a)*rx*fac,math.cos(a)*ry*fac,
                           .008*math.sin(a*3)]) for a in np.linspace(0,math.tau,25)]
        m.tube(points,[.009 if level else .017]*25,
               np.array(color)*(.52+level*.10),n=5)


def root_fan(m,rng,base=.42,color=WOOD):
    for j in range(7):
        a=j*math.tau/7+rng.uniform(-.15,.15)
        length=rng.uniform(.9,1.4)
        branch(m,[(math.cos(a)*length,.018,math.sin(a)*length),
                  (math.cos(a)*.65,.10,math.sin(a)*.65),
                  (.10,.32,.02),(0,.68,0)],
               [.028,.12,base*.80,base*.60],rng,color=color)


def pine(seed):
    rng=random.Random(seed+101);wood=Mesh();leaves=Mesh()
    lean=1 if seed%2==0 else -1
    trunk=[(0,0,0),(.13,.65,-.03),(-.02,1.35,.10),(.31*lean,2.05,.06),
           (.61*lean,2.8,.16),(.57*lean,3.60,.08),(.82*lean,4.35,.11),
           (1.08*lean,5.05,.23),(1.32*lean,5.55,.20)]
    widths=[.43,.35,.29,.235,.19,.15,.11,.07,.025]
    branch(wood,trunk,widths,rng);root_fan(wood,rng)
    knot(wood,(.18,1.09,.28),.10,.18)
    knot(wood,(.39*lean,2.22,.23),.08,.13)
    # Asymmetrical, shelf-like growth, conspicuously unlike a radial lollipop.
    ends=[]
    for j in range(11):
        a=j*2.399963+seed*.72
        y=1.85+j*.29;span=(2.10-j*.085)*rng.uniform(.83,1.14)
        start=np.array([.2+lean*.12*y,y,.07])
        elbow=start+np.array([math.cos(a)*span*.55,-.12,math.sin(a)*span*.55])
        tip=start+np.array([math.cos(a)*span,.26,math.sin(a)*span])
        branch(wood,[start,elbow,tip],[.13-j*.007,.065-j*.003,.013],rng)
        for offset in [-.42,.25]:
            end=tip+np.array([math.cos(a+offset)*.47,.15,math.sin(a+offset)*.47])
            branch(wood,[elbow,tip,end],[.038,.025,.006],rng)
            ends.append((end,a))
    ends.append((np.array(trunk[-1])+np.array([0,-.05,0]),.3))
    for j,(end,a) in enumerate(ends):
        size=(rng.uniform(.55,.88),rng.uniform(.22,.33),rng.uniform(.42,.72))
        c=end-np.array([0,.02,0])
        irregular_solid(leaves,c,size,JADE if j%3==0 else GREEN,seed*90+j,rays=16,layers=5)
        # Dark layered undersides and articulated needle fringes read at distance.
        irregular_solid(leaves,c-np.array([0,.06,0]),
                        (size[0]*.91,.07,size[2]*.91),INK,seed*90+j+700,rays=12,layers=3)
        for k in range(7):
            angle=k*math.tau/7+rng.random()*.25
            p=c+np.array([math.cos(angle)*size[0]*.76,.12,
                          math.sin(angle)*size[2]*.76])
            for spread in [-.18,.18]:
                leaves.leaf(p,.18,.024,angle+spread,
                            (.43,.55,.24) if k%3==0 else (.26,.43,.20),tip=.07)
    return wood,leaves


def blossom(m,p,rng,size=.11):
    colors=[(.96,.76,.68),(.91,.55,.57),(.98,.86,.75),(.85,.41,.49)]
    for j in range(5):
        a=j*math.tau/5+rng.random()*.05
        direction=np.array([math.cos(a),0,math.sin(a)])
        side=np.array([-math.sin(a),0,math.cos(a)])
        center=np.array(p)+direction*size*.38
        pts=[]
        for k in range(7):
            t=k*math.tau/6
            pts.append(center+direction*(math.cos(t)*size*.56)+
                       side*(math.sin(t)*size*.36)+np.array([0,.012+math.cos(t)*.015,0]))
        col=colors[j%len(colors)]
        mid=m.vertex(center+np.array([0,-.005,0]),col,(.5,.5))
        ids=[m.vertex(v,col,(.5+.5*math.cos(k*math.tau/6),.5+.5*math.sin(k*math.tau/6))) for k,v in enumerate(pts)]
        for k in range(6):m.tri.append((mid,ids[k+1],ids[k]))
    m.loft([(p[0],p[1]+.005,p[2],size*.15,size*.15),
            (p[0],p[1]+.026,p[2],size*.09,size*.09)],(.72,.43,.12),n=4)


def cherry(seed):
    rng=random.Random(seed+207);wood=Mesh();flowers=Mesh()
    trunk=[(0,0,0),(-.06,.6,.03),(.17,1.2,-.03),(.37,1.8,.08),(.28,2.3,.10)]
    branch(wood,trunk,[.40,.34,.28,.23,.15],rng,color=(.35,.22,.17))
    root_fan(wood,rng,.37);knot(wood,(.24,1.02,.23),.10,.17)
    for j in range(9):
        a=j*2.399963+seed*.8;span=rng.uniform(1.3,2.3);start=np.array(trunk[-2])
        elbow=start+np.array([math.cos(a)*span*.40,.34+j*.08,math.sin(a)*span*.40])
        end=start+np.array([math.cos(a)*span,.67+j*.12,math.sin(a)*span])
        branch(wood,[start,elbow,end],[.17-j*.009,.085,.018],rng,color=(.35,.22,.17))
        for k in range(3):
            aa=a+(k-1)*.7
            tip=end+np.array([math.cos(aa)*.55,.21,math.sin(aa)*.55])
            branch(wood,[elbow,end,tip],[.055,.028,.005],rng,color=(.35,.22,.17))
            color=[(.79,.39,.46),(.92,.61,.62),(.96,.73,.67)][(j+k)%3]
            c=tip+np.array([0,-.06,0]);sx=rng.uniform(.40,.58);sz=rng.uniform(.35,.53)
            irregular_solid(flowers,c,(sx,.29,sz),color,seed*90+j*3+k,rays=14,layers=5)
            for t in range(6):
                aa=t*2.39996;rad=.38+(.20 if t%2 else .02)
                p=c+np.array([math.cos(aa)*sx*rad*1.4,
                              .25+math.sin(t*1.9)*.08,
                              math.sin(aa)*sz*rad*1.4])
                blossom(flowers,p,rng,size=.12)
    return wood,flowers


def ink_tree():
    """Exposed angular black-umber branches with sparse pointed olive sprays."""
    rng=random.Random(431);wood=Mesh();leaves=Mesh();bark=(.19,.15,.105)
    trunk=[(0,0,0),(-.12,.65,.02),(.11,1.35,.07),(.04,2.00,-.03),
           (-.28,2.70,.04),(-.42,3.35,.12),(-.21,3.97,.06),(-.49,4.60,.14)]
    branch(wood,trunk,[.39,.33,.27,.23,.19,.13,.08,.014],rng,color=bark)
    root_fan(wood,rng,.36,color=bark)
    knot(wood,(.13,1.13,.25),.10,.16,color=bark)
    for j in range(12):
        a=j*2.39996+.3;start=np.array(trunk[2+j//3]);span=2.15-j*.075
        elbow=start+np.array([math.cos(a)*span*.48,.16,math.sin(a)*span*.48])
        end=start+np.array([math.cos(a)*span,.73+(j%3)*.12,math.sin(a)*span])
        branch(wood,[start,elbow,end],[.125-j*.006,.055,.008],rng,color=bark)
        for k in range(3):
            aa=a+(k-1)*.66
            tip=end+np.array([math.cos(aa)*.56,.27,math.sin(aa)*.56])
            wood.tube([elbow,end,tip],[.027,.015,.004],bark,n=7)
            # Clearly separated leaves and air gaps retain the ink silhouette.
            for t in range(8):
                u=t/8;p=end+(tip-end)*u
                direction=aa+(-.9 if t%2 else .9)
                leaves.leaf(p,.25+rng.random()*.09,.065,direction,
                            [( .38,.45,.20),(.50,.53,.24),(.28,.38,.20)][t%3],tip=.08)
    return wood,leaves


def cliff(seed):
    """A standalone, six-metre layered escarpment; open fissures are geometry."""
    rng=random.Random(seed+301);stone=Mesh();moss=Mesh()
    basecolors=[(.65,.49,.30),(.38,.43,.42),(.57,.43,.28)]
    color=basecolors[seed%3]
    for j in range(4):
        x=(j-1.5)*1.45+rng.uniform(-.2,.2);z=rng.uniform(-.23,.26)
        height=rng.uniform(5.6,7.4) if seed==2 else rng.uniform(2.5,4.1)
        for k in range(5):
            y=k*height/5;rad=1.20-k*.10+rng.uniform(-.1,.1)
            center=(x+math.sin(k*1.6+seed)*.11,y,z+math.cos(k+seed)*.10)
            irregular_solid(stone,center,(rad,height/5+.06,.75-k*.04),
                            np.array(color)*(1+.035*k),seed*80+j*5+k,
                            rays=12,terrace=True)
            if k in [2,4]:
                for t in range(3):
                    a=t*2.4+j
                    p=(center[0]+math.cos(a)*rad*.75,y+height/5+.02,
                       center[2]+math.sin(a)*(.62-k*.03))
                    irregular_solid(moss,p,(.28,.045,.19),(.30,.42,.19),seed*80+j*15+k*3+t,rays=12)
    return stone,moss


def ridge_crest():
    """A sun-disc and carved curling wave silhouette, placed on a roof ridge."""
    ceramic=Mesh();gold=Mesh()
    ceramic.box((0,.06,0),(.70,.12,.30),(.22,.31,.31),bevel=.04)
    for side in [-1,1]:
        path=[(side*.05,.12,0),(side*.34,.15,0),(side*.51,.33,0),
              (side*.49,.57,0),(side*.35,.63,0),(side*.23,.53,0)]
        ceramic.tube(path,[.105,.13,.105,.085,.055,.018],(.20,.30,.30),n=12,groove=.06)
        gold.tube([(p[0],p[1],-.095) for p in path],[.012]*6,GOLD,n=6)
    # Disc axis is Z, achieved by mapping the usual upright loft.
    disc=Mesh();disc.loft([(0,-.045,0,.16,.16),(0,.045,0,.16,.16)],GOLD,n=24)
    disc.v=[(p[0],p[2]+.38,p[1]) for p in disc.v]
    # axis exchange reverses handedness, reverse triangle winding.
    disc.tri=[(a,c,b) for a,b,c in disc.tri];gold.merge(disc)
    for a in np.linspace(0,math.tau,9)[:-1]:
        gold.tube([(math.sin(a)*.205,.38+math.cos(a)*.205,-.004),
                   (math.sin(a)*.265,.38+math.cos(a)*.265,-.004)],
                  [.012,.005],GOLD,n=6)
    return ceramic,gold


def gable():
    timber=Mesh();plaster=Mesh();gold=Mesh()
    # Unit-width karahafu-like entrance feature; front is +Z.
    for z in [-.035,.035]:
        path=[]
        for x in np.linspace(-1.05,1.05,31):
            y=.12+.51*math.exp(-(x/.62)**2)+.08*(abs(x)/1.05)**4
            path.append((x,y,z))
        timber.tube(path,[.052]*len(path),WOOD,n=10,groove=.055)
    timber.box((0,.09,0),(2.16,.11,.16),WOOD,bevel=.015)
    # Recessed fan panelling follows the curved gable rather than filling a box.
    for x0 in np.arange(-.94,.94,.115):
        x1=x0+.11
        y0=.10+.51*math.exp(-(x0/.62)**2)
        y1=.10+.51*math.exp(-(x1/.62)**2)
        plaster.face([(x0,.15,.012),(x1,.15,.012),(x1,y1,.012),(x0,y0,.012)],(.78,.70,.48))
        timber.tube([(x0,.16,.028),(x0,y0,.028)],[.012,.010],DARK,n=5)
    for side in [-1,1]:
        path=[(side*.88,.05,0),(side*.76,-.08,0),(side*.55,-.14,0),
              (side*.47,-.24,0),(side*.58,-.28,0)]
        timber.tube(path,[.055,.060,.043,.027,.012],WOOD,n=8)
    # A small front sun crest.
    for a in np.linspace(0,math.tau,21)[:-1]:
        gold.tube([(math.cos(a)*.11,.35+math.sin(a)*.11,.06),
                   (math.cos(a+.16)*.11,.35+math.sin(a+.16)*.11,.06)],
                  [.012,.012],GOLD,n=5)
    return timber,plaster,gold


def bracket():
    """A carved cloud bracket, unit dimensions, mount below existing eaves."""
    m=Mesh();m.box((0,0,0),(.17,.22,.19),WOOD,bevel=.025)
    for side in [-1,1]:
        path=[(0,-.04,0),(side*.11,.05,0),(side*.30,.07,0),
              (side*.39,.15,0),(side*.35,.22,0),(side*.25,.22,0)]
        m.tube(path,[.075,.075,.065,.045,.027,.008],WOOD,n=9,groove=.06)
    m.box((0,.23,0),(.78,.08,.21),WOOD,bevel=.02)
    return m


def stone_lantern():
    stone=Mesh();gold=Mesh()
    gray=(.42,.47,.40)
    stone.loft([(0,0,0,.40,.40),(0,.12,0,.44,.44),(0,.20,0,.31,.31),
                (0,.28,0,.23,.23),(0,.75,0,.12,.12),(0,.86,0,.24,.24),
                (0,.95,0,.27,.27)],gray,n=8,flute=.06)
    for a in [0,math.pi/2,math.pi,math.pi*1.5]:
        x,z=math.cos(a)*.22,math.sin(a)*.22
        stone.tube([(x,.96,z),(x,1.36,z)],[.045,.045],gray,n=8)
    # Open chamber deliberately has gaps; no fake black cards.
    gold.loft([(0,1.03,0,.11,.11),(0,1.26,0,.09,.09)],(.83,.56,.20),n=12,flute=.05)
    roofrings=[(0,1.38,0,.48,.48),(0,1.44,0,.47,.47),
               (0,1.50,0,.30,.30),(0,1.65,0,.11,.11)]
    stone.loft(roofrings,gray,n=8)
    stone.loft([(0,1.63,0,.11,.11),(0,1.73,0,.13,.13),
                (0,1.83,0,.02,.02)],gray,n=12)
    return stone,gold


def shrine_offering():
    wood=Mesh();paper=Mesh();rope=Mesh()
    # Bent branch prayer stand, shimenawa rope and folded white shide.
    for side in [-1,1]:
        wood.tube([(side*.71,0,0),(side*.69,.90,.04),
                   (side*.78,1.70,0),(side*.84,2.08,-.03)],
                  [.075,.065,.055,.025],WOOD,n=12,groove=.09)
    points=[(x,1.86-.18*math.cos(x/.8*math.pi/2),0) for x in np.linspace(-.8,.8,25)]
    rope.tube(points,[.048]*25,(.67,.53,.28),n=12,groove=.10)
    for x in [-.51,-.17,.17,.51]:
        start=1.86-.18*math.cos(x/.8*math.pi/2)
        for j in range(4):
            a=x+(.05 if j%2 else -.05)
            paper.face([(a,start-j*.09,.03),(a+.11,start-j*.09,.03),
                        (a+.07,start-(j+1)*.09,.045),
                        (a-.04,start-(j+1)*.09,.045)],(.91,.87,.71))
    return wood,paper,rope


def save(name, mesh, family, manifest, purpose):
    p=OUT/(name+'.asset');mesh.write(p);g=native.guid(p)
    v=np.array(mesh.v);lo=v.min(0);hi=v.max(0)
    manifest.append({'name':name,'guid':g,'materialFamily':family,'purpose':purpose,
                     'vertices':len(mesh.v),'triangles':len(mesh.tri),
                     'min':lo.tolist(),'max':hi.tolist(),
                     'size':(hi-lo).tolist()})


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    folder=Path(str(OUT)+'.meta')
    if not folder.exists():
        import hashlib
        g=hashlib.md5(str(OUT.relative_to(ROOT)).encode()).hexdigest()
        folder.write_text('fileFormatVersion: 2\nguid: '+g+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
    manifest=[]
    for i in range(3):
        for part,m,family in zip(['trunk','foliage'],pine(i),['wood','foliage']):
            save(f'Pine-{i}-{part}',m,family,manifest,'Sculptural asymmetrical Japanese pine; base at origin')
    for i in range(2):
        for part,m,family in zip(['trunk','blossom'],cherry(i),['wood','foliage']):
            save(f'Cherry-{i}-{part}',m,family,manifest,'Twisted wide cherry silhouette; base at origin')
    for part,m,family in zip(['trunk','olive'],ink_tree(),['wood','foliage']):
        save('Ink-tree-'+part,m,family,manifest,'Angular umber branches, sparse pointed olive foliage; reference-inspired silhouette')
    for i in range(3):
        for part,m,family in zip(['stone','moss'],cliff(i),['stone','foliage']):
            save(f'Cliff-{i}-{part}',m,family,manifest,'Layered six-metre escarpment; use around existing boundary collision')
    for part,m,family in zip(['ceramic','sun'],ridge_crest(),['roof','gold']):
        save('Ridge-crest-'+part,m,family,manifest,'Roof ridge center at origin, +Y up, front +Z')
    for part,m,family in zip(['timber','paper','gold'],gable(),['wood','plaster','gold']):
        save('Gable-'+part,m,family,manifest,'Entrance karahafu fascia; base center origin, front +Z; nominal width 2.16m')
    save('Carved-bracket',bracket(),'wood',manifest,'Below eave; matching top mounting edge at Y=.27m')
    for part,m,family in zip(['stone','light'],stone_lantern(),['stone','gold']):
        save('Stone-lantern-'+part,m,family,manifest,'Open-chamber garden lantern sculpture; 1.83m height')
    for part,m,family in zip(['timber','paper','rope'],shrine_offering(),['wood','plaster','rope']):
        save('Prayer-stand-'+part,m,family,manifest,'Small shimenawa prayer stand, +Z front; no collider or interaction')
    report={'units':'metres','generator':'tools/ink-world/geometry.py',
            'unityRendered':False,'assets':manifest,
            'totalLibraryTriangles':sum(v['triangles'] for v in manifest)}
    (ROOT/'tools/ink-world/geometry-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'meshAssets':len(manifest),
                      'totalLibraryTriangles':report['totalLibraryTriangles']},indent=2))


if __name__=='__main__':
    main()
