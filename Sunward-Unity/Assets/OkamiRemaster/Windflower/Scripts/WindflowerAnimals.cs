using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using UnityEngine;
using UnityEngine.Rendering;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(-50)]
    public sealed class WindflowerAnimals : MonoBehaviour
    {
        public GameFlow game;
        public bool Paused;
        public string LastError { get; private set; }
        public int AnimalCount { get { return actors.Count; } }
        [Serializable] sealed class Layout { public Placement[] actors; public Vector3 farmArrival, farmOverview; }
        [Serializable] sealed class Placement { public string asset, name; public Vector3 position; public Vector2[] path; public float yaw, seed; }
        sealed class Clip { public string source; public float duration, speed, lift; public int count; public Vector3[] position, scale; public Quaternion[] rotation; public float[] ground; }
        sealed class Part { public Mesh mesh; public Material material; }
        sealed class AnimalAsset { public string name; public int[] parents; public Vector3[] bind; public Vector3 offset; public Part[] parts; public Clip idle, walk; public float height; }
        sealed class Actor
        {
            public AnimalAsset asset; public Placement placement; public Transform root, model; public Transform[] bones;
            public float time, walkTime, wait, blend, speed, speedVelocity; public int nextPoint; public Vector3 heading;
        }
        readonly Dictionary<string, AnimalAsset> assets = new Dictionary<string, AnimalAsset>();
        readonly List<Actor> actors = new List<Actor>();
        readonly List<Mesh> ownedMeshes = new List<Mesh>();
        readonly List<Material> ownedMaterials = new List<Material>();
        static Vector3 Vector(BinaryReader r) { return new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle()); }
        static string Text(BinaryReader r)
        {
            int count = r.ReadInt32(); if (count < 0 || count > 4096) throw new InvalidDataException("Invalid farm string.");
            byte[] b = r.ReadBytes(count); if (b.Length != count) throw new EndOfStreamException();
            return System.Text.Encoding.UTF8.GetString(b);
        }
        static int Count(BinaryReader r, int maximum) { int value = r.ReadInt32(); if (value < 1 || value > maximum) throw new InvalidDataException("Invalid farm count."); return value; }
        static Quaternion Rotation(BinaryReader r)
        {
            Quaternion q = new Quaternion(r.ReadSingle(), r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
            float n = Mathf.Sqrt(q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w);
            if (float.IsNaN(n) || n < .5f || n > 1.5f) throw new InvalidDataException("Invalid animal rotation.");
            return new Quaternion(q.x/n,q.y/n,q.z/n,q.w/n);
        }
        void Start()
        {
            if (game == null || game.valley == null || game.Player == null)
            {
                LastError = "Windflower animal life requires the existing game/player/valley references.";
                Debug.LogError(LastError, this); enabled = false; return;
            }
            Initialize();
        }
        void Initialize()
        {
            try
            {
                TextAsset data = Resources.Load<TextAsset>("Farm/Animals");
                TextAsset layoutData = Resources.Load<TextAsset>("WindflowerNative/Animals");
                Material template = Resources.Load<Material>("Farm/AnimalPaint");
                if (data == null || layoutData == null || template == null) throw new InvalidDataException("Farm resources are missing. Copy all files from the update Assets folder.");
                Dictionary<string,Material> materials = new Dictionary<string,Material>();
                using (MemoryStream input = new MemoryStream(data.bytes, false))
                using (GZipStream gzip = new GZipStream(input, CompressionMode.Decompress))
                using (BinaryReader reader = new BinaryReader(gzip))
                {
                    if (reader.ReadInt32() != 0x314D5246 || reader.ReadInt32() != 2) throw new InvalidDataException("Unsupported farm animation data.");
                    int assetCount = Count(reader, 32);
                    for (int k = 0; k < assetCount; ++k)
                    {
                        AnimalAsset a = new AnimalAsset(); a.name = Text(reader); int nb = Count(reader, 128); a.offset = Vector(reader);
                        a.parents = new int[nb]; a.bind = new Vector3[nb]; Matrix4x4[] bindposes = new Matrix4x4[nb]; Vector3[] globalBind = new Vector3[nb];
                        for (int i = 0; i < nb; ++i)
                        {
                            int parent = reader.ReadInt32(); if (parent < -1 || parent >= i) throw new InvalidDataException("Invalid animal bone parent.");
                            a.parents[i] = parent; a.bind[i] = Vector(reader); globalBind[i] = a.bind[i] + (parent < 0 ? Vector3.zero : globalBind[parent]); bindposes[i] = Matrix4x4.Translate(-globalBind[i]);
                        }
                        int partCount = Count(reader, 32); a.parts = new Part[partCount];
                        for (int j = 0; j < partCount; ++j)
                        {
                            string textureId = Text(reader); int nv = Count(reader, 30000), ni = Count(reader, 100000);
                            if (ni % 3 != 0) throw new InvalidDataException("Invalid animal triangle count.");
                            Vector3[] vertices = new Vector3[nv]; Vector2[] uv = new Vector2[nv]; Color32[] colors = new Color32[nv]; BoneWeight[] weights = new BoneWeight[nv];
                            for (int i = 0; i < nv; ++i) vertices[i] = Vector(reader);
                            for (int i = 0; i < nv; ++i) uv[i] = new Vector2(reader.ReadSingle(),reader.ReadSingle());
                            for (int i = 0; i < nv; ++i) colors[i] = new Color32(reader.ReadByte(),reader.ReadByte(),reader.ReadByte(),reader.ReadByte());
                            for (int i = 0; i < nv; ++i)
                            {
                                int b0=reader.ReadByte(),b1=reader.ReadByte(),b2=reader.ReadByte();
                                if (b0>=nb || b1>=nb || b2>=nb) throw new InvalidDataException("Invalid skin bone.");
                                weights[i].boneIndex0=b0;weights[i].boneIndex1=b1;weights[i].boneIndex2=b2;
                            }
                            for (int i = 0; i < nv; ++i)
                            {
                                int w0=reader.ReadByte(),w1=reader.ReadByte(),w2=reader.ReadByte(); if(w0+w1+w2!=255) throw new InvalidDataException("Invalid skin weights.");
                                weights[i].weight0=w0/255f;weights[i].weight1=w1/255f;weights[i].weight2=w2/255f;
                            }
                            int[] triangles = new int[ni]; for(int i=0;i<ni;++i) { triangles[i]=reader.ReadInt32();if(triangles[i]<0||triangles[i]>=nv)throw new InvalidDataException("Invalid animal triangle index."); }
                            Mesh mesh = new Mesh(); mesh.name=a.name+" original part "+j;mesh.indexFormat=IndexFormat.UInt32;mesh.vertices=vertices;mesh.uv=uv;mesh.colors32=colors;mesh.boneWeights=weights;mesh.bindposes=bindposes;mesh.triangles=triangles;mesh.RecalculateNormals();mesh.RecalculateBounds();ownedMeshes.Add(mesh);
                            a.height=Mathf.Max(a.height,mesh.bounds.size.y);
                            Material material;
                            if(!materials.TryGetValue(textureId,out material))
                            {
                                Texture2D texture=Resources.Load<Texture2D>("FarmTextures/"+textureId);if(texture==null)throw new InvalidDataException("Missing original animal texture "+textureId);
                                material=new Material(template);material.name="Original animal paint "+textureId;material.mainTexture=texture;materials.Add(textureId,material);ownedMaterials.Add(material);
                            }
                            a.parts[j]=new Part{mesh=mesh,material=material};
                        }
                        int clipCount=Count(reader,8);
                        for(int j=0;j<clipCount;++j)
                        {
                            string role=Text(reader);Clip clip=new Clip();clip.source=Text(reader);clip.duration=reader.ReadSingle();clip.speed=reader.ReadSingle();clip.lift=reader.ReadSingle();clip.count=Count(reader,400);
                            if(clip.duration<=0||clip.duration>20||clip.speed<0||clip.speed>5)throw new InvalidDataException("Invalid farm clip timing.");
                            clip.position=new Vector3[clip.count*nb];clip.rotation=new Quaternion[clip.count*nb];clip.scale=new Vector3[clip.count*nb];clip.ground=new float[clip.count];
                            for(int f=0;f<clip.count;++f){clip.ground[f]=reader.ReadSingle();for(int i=0;i<nb;++i){int index=f*nb+i;clip.position[index]=Vector(reader);clip.rotation[index]=Rotation(reader);clip.scale[index]=Vector(reader);}}
                            if(role=="idle")a.idle=clip;else if(role=="walk")a.walk=clip;
                        }
                        if(a.idle==null||a.walk==null)throw new InvalidDataException("Missing native farm clips.");assets.Add(a.name,a);
                    }
                    if(reader.BaseStream.ReadByte()!=-1)throw new InvalidDataException("Unexpected trailing animal data.");
                }
                Layout layout=JsonUtility.FromJson<Layout>(layoutData.text);if(layout==null||layout.actors==null)throw new InvalidDataException("Invalid farm layout.");
                foreach(Placement placement in layout.actors) Spawn(placement);
                Debug.Log("Windflower ambient animal life ready: "+actors.Count+" animals using original recovered skeletons, textures and motion curves.");
            }
            catch(Exception error){LastError=error.Message;Debug.LogException(error);}
        }
        void Spawn(Placement p)
        {
            AnimalAsset asset;if(!assets.TryGetValue(p.asset,out asset))throw new InvalidDataException("Unknown farm animal "+p.asset);
            Actor a=new Actor{asset=asset,placement=p,time=p.seed*2.3f,walkTime=p.seed,wait=2+p.seed%3};
            GameObject root=new GameObject(p.name);root.transform.SetParent(transform,false);root.transform.localPosition=p.position;root.transform.localRotation=Quaternion.Euler(0,p.yaw,0);a.root=root.transform;
            GameObject model=new GameObject("Original rig and painted skin");model.transform.SetParent(root.transform,false);model.transform.localPosition=asset.offset+Vector3.up*asset.idle.lift;a.model=model.transform;
            a.bones=new Transform[asset.parents.Length];
            for(int i=0;i<a.bones.Length;++i){GameObject b=new GameObject("Original bone "+i);b.transform.SetParent(asset.parents[i]<0?a.model:a.bones[asset.parents[i]],false);b.transform.localPosition=asset.bind[i];a.bones[i]=b.transform;}
            foreach(Part part in asset.parts)
            {
                GameObject body=new GameObject(part.mesh.name);body.transform.SetParent(model.transform,false);SkinnedMeshRenderer renderer=body.AddComponent<SkinnedMeshRenderer>();renderer.sharedMesh=part.mesh;renderer.sharedMaterial=part.material;renderer.bones=a.bones;renderer.rootBone=a.bones[0];renderer.quality=SkinQuality.Bone4;
                Bounds bounds=part.mesh.bounds;bounds.Expand(3);renderer.localBounds=bounds;renderer.updateWhenOffscreen=false;
            }
            // Ambient actors do not add solid obstacles to existing NPC/player routes.
            Vector3 ground = root.transform.position; ground.y = game.valley.Height(ground); root.transform.position = ground;
            actors.Add(a);ApplyPose(a);
        }
        static void Sample(Clip clip,float time,int bone,int nb,out Vector3 position,out Quaternion rotation,out Vector3 scale)
        {
            // Last->first interpolation also protects clips whose endpoints differ slightly.
            float frame=Mathf.Repeat(time,clip.duration)/clip.duration*(clip.count-1);int i=Mathf.FloorToInt(frame);int j=Mathf.Min(i+1,clip.count-1);float t=frame-i;
            scale=Vector3.Lerp(clip.scale[i*nb+bone],clip.scale[j*nb+bone],t);
            position=Vector3.Lerp(clip.position[i*nb+bone],clip.position[j*nb+bone],t);rotation=Quaternion.Slerp(clip.rotation[i*nb+bone],clip.rotation[j*nb+bone],t);

        }
        static float Ground(Clip clip,float time)
        {
            float frame=Mathf.Repeat(time,clip.duration)/clip.duration*(clip.count-1);int i=Mathf.FloorToInt(frame),j=Mathf.Min(i+1,clip.count-1);float value=Mathf.Lerp(clip.ground[i],clip.ground[j],frame-i);
            return value;
        }
        void ApplyPose(Actor a)
        {
            int n=a.bones.Length;
            for(int i=0;i<n;++i)
            {
                Vector3 idle,walk,si,sw;Quaternion qi,qw;Sample(a.asset.idle,a.time,i,n,out idle,out qi,out si);Sample(a.asset.walk,a.walkTime,i,n,out walk,out qw,out sw);
                a.bones[i].localScale=Vector3.Lerp(si,sw,a.blend);a.bones[i].localPosition=Vector3.Lerp(idle,walk,a.blend);a.bones[i].localRotation=Quaternion.Slerp(qi,qw,a.blend);
            }
            a.model.localPosition=a.asset.offset+Vector3.up*Mathf.Lerp(Ground(a.asset.idle,a.time),Ground(a.asset.walk,a.walkTime),a.blend);
        }
        void Update()
        {
            if(Paused || LastError!=null || game==null || game.Blocked || game.valley.Data==null) return;float dt=Mathf.Min(Time.deltaTime,.075f);
            foreach(Actor a in actors)
            {
                a.time+=dt;float desired=0;Vector2[] path=a.placement.path;Vector3 direction=Vector3.zero;
                bool held=false;
                bool visitorNear=(game.Player.transform.position-a.root.position).sqrMagnitude<1.25f*1.25f;
                if(path!=null&&path.Length>1&&!held&&!visitorNear)
                {
                    if(a.wait>0)a.wait-=dt;
                    else
                    {
                        Vector2 target=path[a.nextPoint];Vector3 delta=new Vector3(target.x-a.root.localPosition.x,0,target.y-a.root.localPosition.z);
                        if(delta.sqrMagnitude<.035f){a.nextPoint=(a.nextPoint+1)%path.Length;a.wait=1.8f+Mathf.Repeat(a.placement.seed+a.nextPoint*.73f,2.0f);}
                        else
                        {
                            Quaternion heading=Quaternion.LookRotation(-delta.normalized,Vector3.up);float angle=Quaternion.Angle(a.root.localRotation,heading);
                            a.root.localRotation=Quaternion.RotateTowards(a.root.localRotation,heading,80*dt);direction=delta.normalized;
                            float turn=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(15,75,angle));float arrival=Mathf.Clamp01(delta.magnitude/.40f);
                            desired=a.asset.walk.speed*turn*arrival;
                        }
                    }
                }
                a.speed=Mathf.SmoothDamp(a.speed,desired,ref a.speedVelocity,.24f,4,dt);
                if(direction.sqrMagnitude>.01f)a.heading=direction;
                if(a.heading.sqrMagnitude>.01f&&a.speed>.005f)
                {
                    Vector3 before=a.root.position;
                    Vector3 next=game.valley.GuardRiver(before,before+a.heading*a.speed*dt);
                    float radius=Mathf.Clamp(a.asset.height*.20f,.12f,.30f);
                    Vector3 delta=next-before;
                    bool obstacle=delta.sqrMagnitude>.000001f && Physics.SphereCast(before+Vector3.up*(radius+.15f),radius,delta.normalized,out _,delta.magnitude+.03f,1<<6,QueryTriggerInteraction.Ignore);
                    if(obstacle) { a.speed=0;a.wait=1.5f;if(path!=null&&path.Length>1)a.nextPoint=(a.nextPoint+1)%path.Length; }
                    else a.root.position=next;
                }
                else if(desired==0)a.speed=Mathf.MoveTowards(a.speed,0,dt*1.8f);
                float weight=Mathf.Clamp01(a.speed/Mathf.Max(.01f,a.asset.walk.speed));a.blend=Mathf.MoveTowards(a.blend,weight,dt*3);
                Vector3 ground=a.root.position;ground.y=game.valley.Height(ground);a.root.position=ground;
                a.walkTime+=dt*weight;ApplyPose(a);
            }
        }
        void OnDestroy()
        {
            foreach(Mesh mesh in ownedMeshes)if(mesh!=null){if(Application.isPlaying)Destroy(mesh);else DestroyImmediate(mesh);}
            foreach(Material material in ownedMaterials)if(material!=null){if(Application.isPlaying)Destroy(material);else DestroyImmediate(material);}
            ownedMeshes.Clear();ownedMaterials.Clear();actors.Clear();assets.Clear();
        }
    }
}
