"""Reproducible authoring pass for the existing Windflower game.

Uses the last integrated artwork scene as its base, then applies only the
requested village, movement presentation, environment and combat additions.
Never called at runtime or by Windows syncing.
"""
from pathlib import Path
import importlib.util,json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE='7046ef08b6c394d05a1536f6c4dac28b766214df'
sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene
SCENE=ROOT/'Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'

def run():
    original=subprocess.check_output(['git','show',BASE+':'+str(SCENE.relative_to(ROOT))],cwd=ROOT).decode()
    scene=Scene(SCENE,original)
    reports={}
    for name in ['environment','places','characters','combat']:
        path=Path(__file__).with_name(name+'.py')
        spec=importlib.util.spec_from_file_location('living_'+name,path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reports[name]=module.apply(scene)
        print(name,json.dumps(reports[name]),flush=True)
    repair_path=ROOT/'tools/player-review/repair.py'
    spec=importlib.util.spec_from_file_location('player_review_fixes',repair_path)
    repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair)
    reports['playerReview']=repair.apply(scene)
    print('playerReview',json.dumps(reports['playerReview']),flush=True)
    scene.save()
    reports['sceneSha256']=hashlib.sha256(SCENE.read_bytes()).hexdigest()
    Path(__file__).with_name('authoring-report.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports

if __name__=='__main__':run()
