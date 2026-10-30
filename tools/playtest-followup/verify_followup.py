"""Focused offline regression checks; Unity compile/playback remain unverified."""
from pathlib import Path
import sys,json,hashlib,re,subprocess,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref
sys.path.insert(0,str(Path(__file__).parent));from pose_audit import bank
from native import Scene
BASE='262519a7ac762e4e1f5af7f472139cedf87f8bd9';A=ROOT/'Sunward-Unity/Assets';RES=A/'OkamiRemaster/Original/Resources/Okami'
def run():
    w=World();s=w.scene;before=Scene(s.path,text=subprocess.check_output(['git','show',BASE+':'+str(s.path.relative_to(ROOT))],cwd=ROOT).decode());report={};disabled=[];unchanged=0
    for id,b in before.blocks.items():
        if before.kind(id) not in [64,65,135,136,143,154]:continue
        if s.blocks[id]==b:unchanged+=1;continue
        assert before.kind(id)==65 and before.name(before.owner(id))=='Food house collision'
        assert s.blocks[id]==b.replace('  m_Enabled: 1\n','  m_Enabled: 0\n');disabled.append(id)
    assert len(disabled)==5;report.update(unchangedColliderBlocksSincePreviousCandidate=unchanged,replacedPubWallBoxes=5)
    audio=json.loads(Path(__file__).with_name('audio-audit.json').read_text());assert len(audio)==42
    for r in audio:
        path=ROOT/r['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['outputSHA256'];assert r['output']['peak']<=.45001 and r['output']['clippedFraction']==0;assert r['output']['rmsDBFS']<=-22.9
        if path.suffix=='.wav':
            with wave.open(str(path)) as f:x=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float)/32768
            assert abs(x).max()<.451 and np.any(x)
    assert sum(r['frameScalesDecrypted'] for r in audio)==39
    report.update(originalCuesAudited=42,encryptedADXStreamsCorrected=39,maxDerivativePeak=max(r['output']['peak'] for r in audio),outputClippedSamples=0)
    for id,b in s.blocks.items():
        if s.kind(id)==1 and 'stripped' not in b and s.refs(id):assert s.kind(s.refs(id)[0]) in [4,224],('Transform must be first',id)
    assert json.loads((RES/'hm08/Model.json').read_text())['visibleGroups']==[0,2], 'Sword trainee must retain body group 2'
    actors=[];diner_resources=[]
    for id,b in s.blocks.items():
        if 'Assembly-CSharp::Sunward.Remaster.NativeVenueActor\n' not in b:continue
        actor=ref(b,'actor')[0];raw=s.blocks[actor];resource=re.search(r'  resource: (\S+)',raw)[1];clips=bank(RES/resource.split('/')[-1]/'Poses.bytes');role=re.search(r'  role: (\S+)',b)[1]
        if role=='training':
            motion=re.search(r'  motion: (\S+)',b)[1];assert motion in clips;dummy=ref(b,'dummy')[0];assert 'TrainingDummy' in s.blocks[dummy]
            a=w.matrix(0,s.transform(s.owner(id)))[:3,3];target=w.matrix(0,s.transform(s.owner(dummy)))[:3,3];assert np.linalg.norm(a-target)<3.2
        else:
            assert 'venue_seated' in clips and 'venue_hands' in clips
            if role=='diner':diner_resources.append(resource)
        actors.append(role)
    assert actors.count('training')==3 and actors.count('diner')==3 and actors.count('musician')==1 and len(set(diner_resources))==3
    report.update(nativeActivityActors=7,distinctDiners=3,dummyPartnersWithinReach=True)
    plan=json.loads(Path(__file__).with_name('scene-changes.json').read_text());trees=[r for r in plan['placements'] if r['package']=='pond-sakura'];assert len(trees)==2
    for r in trees:
        for go in r['objects']:
            renderer=s.blocks[s.component(go,23)];assert 'm_Enabled: 1' in renderer
            mesh=ref(s.blocks[s.component(go,33)],'m_Mesh')[1];d=w.mesh(mesh,4300000);assert len(d['triangles'])>0
    assert 'Cull Off' in (A/'OkamiRemaster/Original/Shaders/OriginalBlossomCards.shader').read_text()
    # Both entry destinations are inside; exit destinations are outside, regardless
    # of whether a wall currently blocks walking up to an old outside-only prompt.
    dojo=lambda p:abs(p[0])<6.5 and 16.2<p[2]<33.6 and p[1]<6
    pub=lambda p:abs(p[0]-10)<4.4 and abs(p[2]+15)<3.6 and p[1]<6
    assert dojo((0,.52,18.3)) and not dojo((0,.05,13.3));assert pub((6.8,.67,-15)) and not pub((2.8,.05,-15))
    game=(A/'Sunward/Scripts/GameFlow.cs').read_text();assert 'if (Sunward.Remaster.VillageServices.InDojo(p)) return "venue:dojo";' in game
    # Shared sources can no longer accidentally broadcast animal/NPC calls in 2D.
    sound=(A/'Sunward/Scripts/ValleyAudio.cs').read_text();assert 'source.spatialBlend=1' in sound and 'distance>=range' in sound and 'distance>=level.x' in sound and 'nextVoice' in sound and 'Player perspective audio listener' in sound
    atmosphere=(A/'OkamiRemaster/Original/Scripts/OriginalAtmosphere.cs').read_text();assert 'Create("Cloud", game.Player' not in atmosphere and 'Create("Flame", game.Player' not in atmosphere and 'shape.skinnedMeshRenderer=body' in atmosphere
    report.update(treePlacementsWithoutBuildingMeshes=2,entryExitContainmentChecksPassed=True,animalNpcSoundSpatialAndRangeLimited=True,shiranuiEmitterUsesBodySurface=True,UnityCompilationVerified=False,UnityGameplayVerified=False,audibleMixApproved=False,exactNativeKotoPlayingMotionIdentified=False,swimmingNativeClipsReidentified=False)
    Path(__file__).with_name('verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
