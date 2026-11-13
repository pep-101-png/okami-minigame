using UnityEngine;
namespace Sunward.Remaster
{
    // Swept traversal, independent of Unity trigger delivery or a single thin plane.
    [DefaultExecutionOrder(90)]
    public sealed class CelestialTrialGate:MonoBehaviour
    {
        public GameFlow game;public int kind;public ParticleSystem mist;
        Vector3 previous;bool havePrevious;int revision;float cooldown;
        public static bool Crosses(Vector3 a,Vector3 b)
        {if(Mathf.Abs(b.x)<2 && b.y>-.8f && b.y<6 && Mathf.Abs(b.z)<1.3f)return true;if(a.z*b.z>0 || Mathf.Abs(b.z-a.z)<.0001f)return false;var p=Vector3.Lerp(a,b,Mathf.Clamp01(-a.z/(b.z-a.z)));return Mathf.Abs(p.x)<2 && p.y>-.8f && p.y<6;}
        void Update()
        {
            if(!game || !game.Player || !game.Celestial)return;
            if(kind==1 && HeavenlyGarden.Inside(game.Player.transform.position) && !HeavenlyGarden.PalaceInside(game.Player.transform.position) && !CelestialTrials.InArena(game.Player.transform.position) && HeavenlyGarden.Height(transform.position,out var floor))transform.position=new Vector3(transform.position.x,floor+.03f,transform.position.z);
            cooldown=Mathf.Max(0,cooldown-Time.unscaledDeltaTime);var p=transform.InverseTransformPoint(game.Player.transform.position);
            bool entered=Crosses(havePrevious && revision==game.Player.TeleportRevision?previous:p,p);previous=p;revision=game.Player.TeleportRevision;havePrevious=true;
            bool completed=game.Profile.shiranuiUnlock>=kind;bool ready=!completed && game.Celestial.Ready(kind);
            if(mist){var main=mist.main;main.startColor=ready?new Color(1,.88f,.55f,.8f):new Color(.6f,.7f,1,.25f);}
            if(game.Blocked || game.InTrial || game.Health<=0 || game.Player.Locked || Mathf.Abs(p.x)>4 || Mathf.Abs(p.z)>4 || p.y<-.8f || p.y>6)return;
            if(completed){game.WorldPrompt("The old guardian's seal has fallen silent");return;}
            game.WorldPrompt(ready?"Walk through the awakened passage":"E · Examine the quiet seal");
            if(ready && entered && cooldown<=0){cooldown=2;game.Celestial.Enter(kind);}
            else if(game.Player.input.Interact.WasPressedThisFrame() && cooldown<=0){cooldown=.5f;game.ShowDialogue(CelestialHints.Gate(game.Profile,kind));}
        }
    }
}
