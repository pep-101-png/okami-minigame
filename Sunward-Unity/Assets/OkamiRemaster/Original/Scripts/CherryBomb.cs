using UnityEngine;
namespace Sunward.Remaster
{
    // Original ET07 appearance and core sprites; fuse/damage are Sunward mechanics.
    public sealed class CherryBomb : MonoBehaviour
    {
        public GameFlow game;
        float fuse=2.3f;bool exploded;
        public static void Spawn(GameFlow game,Vector3 point)
        {
            var go=new GameObject("Cherry Bomb · original ET07");point.y=game.valley.Height(point)+.02f;go.transform.position=point;
            VillageFestival.Place(go.transform,"Okami/et07",Vector3.zero,new Vector3(1,1.45f,1),Vector3.zero);
            var bomb=go.AddComponent<CherryBomb>();bomb.game=game;
            var sparks=OriginalAtmosphere.Create("Spark",go.transform,Vector3.up*1.3f,7,.14f,.4f,.25f,.05f);
        }
        void Update()
        {
            if(!game || game.Blocked || exploded)return;
            fuse-=Time.deltaTime;if(fuse>0)return;exploded=true;
            var p=transform.position;CelestialBrush.Burst("Cloud",p+Vector3.up*.5f,35,1.7f);CelestialBrush.Burst("Flame",p+Vector3.up*.5f,20,.75f);CelestialBrush.Burst("Spark",p+Vector3.up*.7f,32,.5f);
            foreach(var enemy in game.Enemies)if(enemy && !enemy.Dead && Vector3.Distance(enemy.transform.position,p)<5.5f)enemy.Damage(55*game.Combat.FormMultiplier,(enemy.transform.position-p).normalized,.3f);
            // No glacial weapon sound substituted for an unidentified bomb event.
            Destroy(gameObject);
        }
    }
}
