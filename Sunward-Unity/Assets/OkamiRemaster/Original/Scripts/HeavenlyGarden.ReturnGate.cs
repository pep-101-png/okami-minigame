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
            var line=veil.AddComponent<LineRenderer>();line.useWorldSpace=false;line.alignment=LineAlignment.TransformZ;line.positionCount=2;line.SetPosition(0,new Vector3(-2.3f,0,0));line.SetPosition(1,new Vector3(2.3f,0,0));line.startWidth=line.endWidth=4.7f;line.sharedMaterial=new Material(Resources.Load<Material>("Okami/Effects/PalaceVeil"));line.sharedMaterial.SetColor("_BarrierTint",new Color(.55f,.9f,1,1));veil.AddComponent<OriginalParticleMaterial>();
            OriginalAtmosphere.Create("SpiritGlow",root.transform,new Vector3(0,2,0),18,.23f,2,.2f,1.3f);
            var lamp=root.AddComponent<Light>();lamp.type=LightType.Point;lamp.range=8;lamp.intensity=3;lamp.color=new Color(.55f,.85f,1);
        }
        public static bool InReturnPassage(Vector3 p)
        {
            // Match the visible opening, including the approach side of the gate.
            // Ground probes can see the upper garden tier above the wolf. The
            // passage belongs to the gate's XZ footprint, not that probe height.
            return Inside(p) && !PalaceInside(p) && Mathf.Abs(p.x-GateCentre.x)<2.3f && Mathf.Abs(p.z-GateCentre.z)<1.9f;
        }
        void SolidGate(GameObject prop)
        {
            // Decorative gate meshes can include a broad sheet across the opening.
            // Only the two visible posts and overhead lintel block the player.
            foreach(float side in new[]{-1f,1f}){var post=prop.AddComponent<BoxCollider>();post.center=new Vector3(side*3.5f,3,0);post.size=new Vector3(1.1f,6,1.2f);}
            var lintel=prop.AddComponent<BoxCollider>();lintel.center=new Vector3(0,6.3f,0);lintel.size=new Vector3(9,1.2f,1.4f);
        }
        bool ReturnGate(Vector3 p)
        {
            if(!InReturnPassage(p))return false;
            game.ReturnHome();var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();return true;
        }
    }
}
