using UnityEngine;
namespace Sunward.Remaster
{
    public sealed partial class HeavenlyGarden
    {
        void BuildReturnGate(Transform gate)
        {
            var root=new GameObject("Torii spirit passage · walk through to Windflower");root.transform.SetParent(gate,false);
            var portal=root.AddComponent<HeavenReturnPortal>();portal.game=game;
            var trigger=root.AddComponent<BoxCollider>();trigger.isTrigger=true;trigger.center=new Vector3(0,3.1f,0);trigger.size=new Vector3(4.6f,8.8f,2.8f);
            var body=root.AddComponent<Rigidbody>();body.isKinematic=true;body.useGravity=false;
            var veil=new GameObject("Original moving spirit curtain");veil.transform.SetParent(root.transform,false);veil.transform.localPosition=Vector3.up*2.4f;
            var line=veil.AddComponent<LineRenderer>();line.useWorldSpace=false;line.alignment=LineAlignment.TransformZ;line.positionCount=2;line.SetPosition(0,new Vector3(-2.3f,0,0));line.SetPosition(1,new Vector3(2.3f,0,0));line.startWidth=line.endWidth=4.7f;line.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/PalaceVeil"));line.sharedMaterial.SetColor("_BarrierTint",new Color(.55f,.9f,1,1));veil.AddComponent<OriginalParticleMaterial>();
            OriginalAtmosphere.Create("SpiritGlow",root.transform,new Vector3(0,2,0),18,.23f,2,.2f,1.3f);
            var lamp=root.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=8;lamp.intensity=3;lamp.color=new Color(.55f,.85f,1);
        }
        void SolidGate(GameObject prop)
        {
            // Decorative gate meshes can include a broad sheet across the opening.
            // Only the two visible posts and overhead lintel block the player.
            foreach(float side in new[]{-1f,1f}){var post=prop.AddComponent<BoxCollider>();post.center=new Vector3(side*3.5f,3,0);post.size=new Vector3(1.1f,6,1.2f);}
            var lintel=prop.AddComponent<BoxCollider>();lintel.center=new Vector3(0,6.3f,0);lintel.size=new Vector3(9,1.2f,1.4f);
        }
    }
}
