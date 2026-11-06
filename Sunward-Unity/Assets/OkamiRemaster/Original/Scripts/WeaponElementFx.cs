using UnityEngine;
namespace Sunward.Remaster
{
    public static class WeaponElementFx
    {
        public static bool Lightning(string weapon)=>weapon=="wp29" || weapon==OriginalWeaponEvolution.ThunderId;
        public static Color Colour(string weapon)
        {
            switch(weapon){case "wp29":case "wp29e":return new Color(1,.77f,.12f);case "wp2e":return new Color(.38f,.78f,1);case "wp24":return new Color(1,.28f,.05f);case "wp2c":case "wp22":return new Color(.36f,.85f,.42f);case "wp2d":case "wp23":return new Color(.75f,.4f,1);case "wp2b":return new Color(1,.32f,.2f);case "wp28":return new Color(.85f,.55f,.18f);case "wp20":return new Color(1,.42f,.12f);case "wp21":return new Color(1,.65f,.2f);case "wp25":return new Color(.82f,.9f,1);case "wp26":return new Color(.35f,.85f,.7f);case "wp27":return new Color(.4f,.75f,1);case "wp2a":return new Color(1,.8f,.25f);default:return new Color(1,.9f,.65f);}
        }
        public static void Tint(GameObject root,Color colour)
        {
            var shader=Resources.Load<Material>("Okami/Effects/ElementTint").shader;
            foreach(var r in root.GetComponentsInChildren<SkinnedMeshRenderer>())
            {var mat=new Material(r.sharedMaterial);mat.shader=shader;mat.SetColor("_Tint",colour);r.sharedMaterial=mat;r.gameObject.AddComponent<OriginalParticleMaterial>();}
        }
        public static void Bark(GameFlow game,string weapon,Vector3 point)
        {
            var ring=game.Fx.Ring(point,new Color(.5f,.7f,1),5.5f);if(ring)Tint(ring.gameObject,Colour(weapon));
            if(Lightning(weapon))Thunder(game,point+Vector3.up*.3f,false);
            else
            {
                string art=weapon=="wp24"?"Flame":weapon=="wp2e"?"SpiritGlow":"Spirit";
                var p=OriginalAtmosphere.Create(art,null,point+Vector3.up*.5f,0,.2f,.7f,.4f,1.8f);
                if(p){var main=p.main;main.startColor=Colour(weapon);p.Emit(18);Object.Destroy(p.gameObject,1.5f);}
            }
        }
        public static void Thunder(GameFlow game,Vector3 point,bool charged,bool sound=true)
        {
            if(charged && game.Player && game.Player.valley)point.y=game.Player.valley.Height(point)+.04f;
            var root=new GameObject(charged?"Original Thunder Edge · charged thunderstrike":"Original Thunder Edge · lightning contact");root.transform.position=point;
            ThunderPainting.Burst(root.transform,Vector3.zero,charged);
            var lamp=root.AddComponent<Light>();lamp.type=LightType.Point;lamp.color=Colour("wp29");lamp.range=charged?22:7;lamp.intensity=charged?18:6;
            var life=root.AddComponent<ThunderFlash>();life.life=charged?.9f:.4f;
            if(sound)game.Audio.Cue(charged?"thunder-burst":"thunder-strike");
        }
    }
}
