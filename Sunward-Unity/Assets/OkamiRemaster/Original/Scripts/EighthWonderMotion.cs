using UnityEngine;
namespace Sunward.Remaster
{
    // The genuine WP28_000 wheel curve also belongs on displayed/dropped blades.
    // Layer only its own bone: retain the display or falling sword's orientation.
    public sealed class EighthWonderMotion:MonoBehaviour
    {
        public OriginalVisual visual;float clock;
        void Update(){if(!visual)return;clock+=Time.deltaTime;visual.SampleBoneMotion("Okami/wp28","wp28_000",clock,2);}
    }
}
