using UnityEngine;
namespace Sunward.Remaster
{
    public sealed partial class HeavenlyGarden
    {
        public static readonly Vector3 PalaceCentre=new Vector3(230,80,140);
        public static bool PalaceInside(Vector3 p)=>Mathf.Abs(p.x-PalaceCentre.x)<25 && Mathf.Abs(p.z-PalaceCentre.z)<25 && p.y>76 && p.y<98;
        GameObject palace;float palaceDoorCooldown;
        static Vector3 PalaceGuard(Vector3 p)
        {var d=new Vector2(p.x-PalaceCentre.x,p.z-PalaceCentre.z);if(d.magnitude>20)d=d.normalized*20;return new Vector3(PalaceCentre.x+d.x,p.y,PalaceCentre.z+d.y);}
        void BuildPalace()
        {
            palace=new GameObject("Heavens palace · quiet white cloud sanctuary");palace.transform.SetParent(garden.transform,false);palace.transform.position=PalaceCentre;
            var floor=VillageFestival.Place(palace.transform,"Okami/celestial-grounded",Vector3.zero,new Vector3(65,.025f,65),Vector3.zero);
            foreach(var r in floor.GetComponentsInChildren<SkinnedMeshRenderer>())
            {var material=new Material(Resources.Load<Material>("Okami/Effects/PalaceCloud"));material.mainTexture=Resources.Load<Texture2D>("Okami/Effects/Cloud");r.sharedMaterial=material;r.gameObject.layer=6;r.gameObject.AddComponent<MeshCollider>().sharedMesh=r.sharedMesh;}
            for(int i=0;i<8;i++)
            {float a=i*Mathf.PI/4;var cloud=VillageFestival.Place(palace.transform,"Okami/heaven-cloud",new Vector3(Mathf.Sin(a)*20,-.25f,Mathf.Cos(a)*20),new Vector3(16,2.6f,12),new Vector3(0,i*45,0));if(cloud)foreach(var r in cloud.GetComponentsInChildren<SkinnedMeshRenderer>()){var mat=new Material(r.sharedMaterial);mat.shader=Resources.Load<Material>("Okami/Effects/HeavenCloud").shader;r.sharedMaterial=mat;}}
            var exitGate=VillageFestival.Place(palace.transform,"Okami/heaven-gate",new Vector3(0,0,-14.5f),new Vector3(4,4,1.2f),Vector3.zero);if(exitGate)SolidProp(exitGate);
            var sleeper=new GameObject("Shiranui · original sleeping wolf");sleeper.SetActive(false);sleeper.transform.SetParent(palace.transform,false);sleeper.transform.localPosition=Vector3.up*.04f;var actor=sleeper.AddComponent<OriginalActor>();actor.game=game;actor.resource="Okami/palace-shiranui";actor.idle=actor.walk=actor.run=actor.windup=actor.strike=actor.recover=actor.death="pl00_004";actor.modelScale=1.2f;sleeper.transform.localRotation=Quaternion.Euler(0,35,0);sleeper.SetActive(true);
            var lamp=sleeper.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=12;lamp.intensity=3;lamp.color=new Color(.9f,.94f,1);
            var veil=new GameObject("Mystical seal · continuous soft original spirit paint");veil.transform.SetParent(palace.transform,false);veil.AddComponent<PalaceSeal>();
            for(int i=0;i<16;i++){float a=i*Mathf.PI/8;var segment=new GameObject("Palace spirit seal · solid boundary");segment.transform.SetParent(palace.transform,false);segment.transform.localPosition=new Vector3(Mathf.Sin(a)*3.7f,3.5f,Mathf.Cos(a)*3.7f);segment.transform.localRotation=Quaternion.Euler(0,i*22.5f,0);var wall=segment.AddComponent<BoxCollider>();wall.size=new Vector3(1.6f,7,.28f);}
            OriginalAtmosphere.Create("SpiritGlow",palace.transform,new Vector3(0,1,0),5,.14f,4,.03f,3.5f);
        }
        bool PalaceInteractions()
        {
            palaceDoorCooldown=Mathf.Max(0,palaceDoorCooldown-Time.unscaledDeltaTime);var p=game.Player.transform.position;bool inside=PalaceInside(p);Shader.SetGlobalFloat("_HeavenPalace",inside?1:0);
            if(game.Player.Locked || game.Blocked)return inside;
            if(inside)
            {
                if(p.z<PalaceCentre.z-13.5f && Mathf.Abs(p.x-PalaceCentre.x)<2 && palaceDoorCooldown<=0){var at=Centre+new Vector3(0,5,24.8f);Height(at,out var y);at.y=y+.03f;game.Player.Teleport(at);game.Player.transform.rotation=Quaternion.Euler(0,180,0);palaceDoorCooldown=1.5f;Shader.SetGlobalFloat("_HeavenPalace",0);var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();return true;}
                game.WorldPrompt(Vector2.Distance(new Vector2(p.x,p.z),new Vector2(PalaceCentre.x,PalaceCentre.z))<6?"E · Examine Shiranui's seal":"Shiranui sleeps ahead · walk through the entrance gate to leave");
                if(game.Player.input.Interact.WasPressedThisFrame() && palaceDoorCooldown<=0 && Vector2.Distance(new Vector2(p.x,p.z),new Vector2(PalaceCentre.x,PalaceCentre.z))<6){palaceDoorCooldown=.6f;game.ShowDialogue("Shiranui sleeps within this mystical seal. To free him, reach level 15 and earn 30 total upgrade ranks, then defeat the palace guardian. That guardian is a future encounter, so the seal cannot yet be broken. P remains available as a transformation test shortcut.");}
                return true;
            }
            if(palaceDoorCooldown<=0 && Mathf.Abs(p.x-Centre.x)<1.25f && p.z>25 && p.z<27.5f && p.y>Centre.y+4)
            {game.Services.CancelRest();game.Combat.Cancel();game.Player.Teleport(PalaceCentre+new Vector3(0,.04f,-11.5f));game.Player.transform.rotation=Quaternion.Euler(0,0,0);palaceDoorCooldown=1.5f;Shader.SetGlobalFloat("_HeavenPalace",1);var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();return true;}
            return false;
        }
    }
}
