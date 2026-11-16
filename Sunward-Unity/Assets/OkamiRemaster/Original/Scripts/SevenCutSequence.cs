using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class SevenCutSequence:MonoBehaviour
    {
        GameFlow game;EnemyBrain target;int cut;float clock;string weapon;
        public static void Begin(GameFlow g,EnemyBrain e){var obj=new GameObject("Seven Strike · successive native wind cuts");var sequence=obj.AddComponent<SevenCutSequence>();sequence.game=g;sequence.target=e;sequence.weapon=g.Profile.equipped;}
        void Update()
        {
            if(!game || !game.InTrial || !target || target.Dead || game.Profile.equipped!=weapon){Destroy(gameObject);return;}if(game.Blocked)return;clock+=Time.deltaTime;if(clock<cut*.075f)return;
            var p=target.transform.position+Vector3.up*(.45f+cut*.1f);float side=cut%2==0?1:-1;
            BrushStrokeFlash.Slash(p+new Vector3(-side*.75f,-.3f,0),p+new Vector3(side*.75f,.3f,0));CelestialBrush.Burst("Wind",p,1,1.2f);
            target.Damage(3*game.Combat.FormMultiplier*AwakenedWeaponArts.SpecialPower(game),game.Player.transform.forward,.05f);VillageAdventures.Record(game,"seven");cut++;if(cut>=7)Destroy(gameObject);
        }
    }
}
