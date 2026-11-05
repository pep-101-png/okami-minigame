using UnityEngine;
namespace Sunward.Remaster
{
    public sealed partial class HeavenlyGarden
    {
        static readonly Vector3 GateCentre=Centre+new Vector3(0,0,-26.5f);
        void BuildReturnGate()
        {
            var position=OnGround(GateCentre);var root=new GameObject("Torii spirit passage · walk through to Windflower");root.transform.SetParent(garden.transform,false);root.transform.position=position;
            var veil=new GameObject("Original moving spirit curtain");veil.transform.SetParent(root.transform,false);veil.transform.localPosition=Vector3.up*2.4f;
            var line=veil.AddComponent<LineRenderer>();line.useWorldSpace=false;line.alignment=LineAlignment.TransformZ;line.positionCount=2;line.SetPosition(0,new Vector3(-1.35f,0,0));line.SetPosition(1,new Vector3(1.35f,0,0));line.startWidth=line.endWidth=4.7f;line.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/PalaceVeil"));line.sharedMaterial.SetColor("_BarrierTint",new Color(.55f,.9f,1,1));veil.AddComponent<OriginalParticleMaterial>();
            OriginalAtmosphere.Create("SpiritGlow",root.transform,new Vector3(0,2,0),18,.23f,2,.2f,1.3f);
            var lamp=root.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=8;lamp.intensity=3;lamp.color=new Color(.55f,.85f,1);
        }
        bool ReturnGate(Vector3 p)
        {
            if(Mathf.Abs(p.x-GateCentre.x)<1.2f && Mathf.Abs(p.z-GateCentre.z)<.65f && Mathf.Abs(p.y-Centre.y)<5)
            {game.ReturnHome();return true;}
            return false;
        }
    }
}
