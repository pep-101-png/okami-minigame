namespace UnityEngine
{
 public struct Bounds{public Bounds(Vector3 a,Vector3 b){}}
 public enum ParticleSystemShapeType{SkinnedMeshRenderer}public enum ParticleSystemMeshShapeType{Triangle}
 public class Material:Object{public Material(Material source){}public Texture2D mainTexture;}
 public class AnimationCurve{public static AnimationCurve Linear(float a,float b,float c,float d)=>new AnimationCurve();}
 public class LineRenderer:Renderer{public GameObject gameObject=new GameObject();public bool useWorldSpace;public int positionCount;public float startWidth,endWidth;public Color startColor,endColor;public void SetPosition(int i,Vector3 p){}}
 public class TrailRenderer:LineRenderer{public Transform transform=>gameObject.transform;public float time,minVertexDistance,widthMultiplier;public AnimationCurve widthCurve;public bool emitting;public void Clear(){}}
}
namespace Sunward
{
 public class EnemyDefinition:UnityEngine.Object{public string id;public float hp,damage,speed,scale,windup;public UnityEngine.GameObject visual;}
 public static class ProgressionRules{public static int Level(ProfileData p)=>1;}
 public class VisualFx{public UnityEngine.LineRenderer Ring(UnityEngine.Vector3 p,UnityEngine.Color c,float radius,float duration=1)=>new UnityEngine.LineRenderer();}
 public class ResidentLocomotion:UnityEngine.Object{public bool enabled;}
 public class VillageResident:UnityEngine.Object{public GameFlow game;}
}
