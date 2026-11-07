// Transform API double with parent-space position/rotation/scale, not Unity physics.
public class Transform:Object
{
 public GameObject gameObject;public string name=>gameObject?.name??"";public Transform parent;
 public Vector3 localPosition,localScale=Vector3.one,eulerAngles;public Quaternion localRotation=Quaternion.identity;
 public Vector3 position{get=>parent?parent.TransformPoint(localPosition):localPosition;set=>localPosition=parent?parent.InverseTransformPoint(value):value;}
 public Quaternion rotation{get=>parent?parent.rotation*localRotation:localRotation;set=>localRotation=parent?Quaternion.Inverse(parent.rotation)*value:value;}
 public Vector3 lossyScale=>parent?Vector3.Scale(parent.lossyScale,localScale):localScale;
 public Vector3 right=>rotation*new Vector3(1,0,0);public Vector3 forward=>rotation*new Vector3(0,0,1);
 public Matrix4x4 worldToLocalMatrix=>Matrix4x4.identity;public Matrix4x4 localToWorldMatrix=>Matrix4x4.identity;
 public Vector3 TransformPoint(Vector3 p)=>position+rotation*Vector3.Scale(p,lossyScale);
 public Vector3 InverseTransformPoint(Vector3 p){var q=Quaternion.Inverse(rotation)*(p-position);var s=lossyScale;return new Vector3(q.x/s.x,q.y/s.y,q.z/s.z);}
 public void SetParent(Transform next,bool world=false){var p=position;var q=rotation;parent=next;if(world){position=p;rotation=q;}}
 public void SetPositionAndRotation(Vector3 p,Quaternion q){position=p;rotation=q;}
 public void Rotate(float x,float y,float z){localRotation=localRotation*Quaternion.Euler(x,y,z);}
 public bool IsChildOf(Transform root){for(var p=this;p!=null;p=p.parent)if(System.Object.ReferenceEquals(p,root))return true;return false;}
 public T GetComponentInChildren<T>(bool b=false)where T:class=>gameObject.GetComponent<T>();public T[] GetComponentsInChildren<T>(bool b=false)=>gameObject.GetComponentsInChildren<T>(b);
}
