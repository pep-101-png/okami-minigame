using UnityEngine;
namespace Sunward.Remaster
{
    // Sleep toggles a saved time of day. All visible lamps/supports are original
    // Okami models; illumination and transitions remain Sunward runtime systems.
    public sealed class VillageFestival : MonoBehaviour
    {
        public GameFlow game;
        public static bool NextNight(bool current)=>!current;
        float blend;
        Light sun;
        float sunIntensity;
        Color sunColor,fog,ambient;
        Quaternion sunRotation;
        GameObject festival;
        readonly System.Collections.Generic.List<Light> lamps=new System.Collections.Generic.List<Light>();
        readonly Vector4[] pools=new Vector4[24];
        public bool Night=>game && game.Profile.night;
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();sun=RenderSettings.sun;
            if(sun){sunIntensity=sun.intensity;sunColor=sun.color;sunRotation=sun.transform.rotation;}
            fog=RenderSettings.fogColor;ambient=RenderSettings.ambientLight;blend=Night?1:0;
            festival=new GameObject("Original village festival lanterns");festival.transform.SetParent(transform,false);
            for(int row=0;row<6;row++)
            {
                float z=-11+row*4.2f;
                var stringRoot=new GameObject("Original colourful lantern string "+row);stringRoot.transform.SetParent(festival.transform,false);stringRoot.transform.position=new Vector3(0,game.valley.Height(new Vector3(0,0,z)),z);
                for(int side=0;side<2;side++)Place(stringRoot.transform,"Okami/vt00",new Vector3(side==0?-3.8f:3.8f,0,0),new Vector3(.16f,4.8f,.16f),Vector3.zero);
                // Native ET03 cord runs along local Z; rotate it across the road.
                Place(stringRoot.transform,"Okami/et03",new Vector3(0,4.6f,0),new Vector3(.025f,.025f,7.6f),new Vector3(0,90,0));
                for(int i=0;i<5;i++)
                {
                    float x=-2.6f+i*1.3f,top=4.612f;
                    Place(stringRoot.transform,"Okami/et03",new Vector3(x,top-.115f,0),new Vector3(.016f,.016f,.23f),new Vector3(-90,0,0));
                    string resource=(row+i)%4==0?"Okami/vt33":(row+i)%4==1?"Okami/vt34":(row+i)%4==2?"Okami/vt32":"Okami/et07";
                    float height=.56f;Place(stringRoot.transform,resource,new Vector3(x,top-.23f-height,0),new Vector3(.42f,height,.42f),Vector3.zero);
                }
                var glow=new GameObject("Warm light beneath lantern string");glow.transform.SetParent(stringRoot.transform,false);glow.transform.localPosition=new Vector3(0,3.7f,0);var light=glow.AddComponent<Light>();light.type=LightType.Point;light.range=8;light.color=new Color(1,.66f,.33f);light.intensity=0;light.shadows=LightShadows.None;lamps.Add(light);pools[row]=new Vector4(0,stringRoot.transform.position.y+2,z,8);
            }
            pools[12]=new Vector4(-5.1f,1.6f,18.8f,6);pools[13]=new Vector4(5.1f,1.6f,18.8f,6);pools[14]=new Vector4(10,2,-15,7);pools[15]=new Vector4(-34,2,-16,6);
            pools[16]=new Vector4(-4,2,29,7);pools[17]=new Vector4(4,2,29,7);
            Shader.SetGlobalVectorArray("_SunwardFestivalLights",pools);Apply();
        }
        public static void Place(Transform parent,string resource,Vector3 position,Vector3 size,Vector3 rotation)
        {
            var data=Resources.Load<TextAsset>(resource+"/Model");if(!data)return;
            var model=JsonUtility.FromJson<BoundsModel>(data.text);Vector3 lo=Vector3.one*float.PositiveInfinity,hi=Vector3.one*float.NegativeInfinity;
            foreach(var part in model.parts)
            {
            if(model.visibleGroups!=null && model.visibleGroups.Length>0 && System.Array.IndexOf(model.visibleGroups,int.Parse(part.name.Split('-')[1]))<0)continue;
            for(int i=0;i<part.positions.Length;i+=3){var p=new Vector3(part.positions[i],part.positions[i+1],part.positions[i+2]);lo=Vector3.Min(lo,p);hi=Vector3.Max(hi,p);}
            }
            var extent=hi-lo;Vector3 scale=new Vector3(size.x/Mathf.Max(.001f,extent.x),size.y/Mathf.Max(.001f,extent.y),size.z/Mathf.Max(.001f,extent.z));
            var root=new GameObject("Original cedar festival support");root.transform.SetParent(parent,false);root.transform.localPosition=position;root.transform.localRotation=Quaternion.Euler(rotation);
            root.AddComponent<OriginalVisual>().Load(resource,-Vector3.Scale(new Vector3((lo.x+hi.x)*.5f,lo.y,(lo.z+hi.z)*.5f),scale),scale);
        }
        [System.Serializable]sealed class BoundsModel{public BoundsPart[] parts;public int[] visibleGroups;}
        [System.Serializable]sealed class BoundsPart{public string name;public float[] positions;}
        public void SleepToNextTime()
        {
            game.Profile.night=NextNight(game.Profile.night);game.Save.Save();
            game.Notify(Night?"Night falls · festival lanterns light the village":"Morning returns · the village wakes");
        }
        void Update(){if(!game)return;blend=Mathf.MoveTowards(blend,Night?1:0,Time.unscaledDeltaTime/.9f);Apply();}
        void Apply()
        {
            Shader.SetGlobalFloat("_SunwardNight",blend);
            if(sun){sun.intensity=Mathf.Lerp(sunIntensity,.12f,blend);sun.color=Color.Lerp(sunColor,new Color(.45f,.58f,1),blend);sun.transform.rotation=Quaternion.Slerp(sunRotation,Quaternion.Euler(32,-30,0),blend);}
            RenderSettings.fogColor=Color.Lerp(fog,new Color(.035f,.055f,.11f),blend);RenderSettings.ambientLight=Color.Lerp(ambient,new Color(.10f,.14f,.24f),blend);
            if(festival)festival.SetActive(true);foreach(var lamp in lamps)if(lamp)lamp.intensity=18*blend;
        }
        void OnDestroy()
        {
            Shader.SetGlobalFloat("_SunwardNight",0);Shader.SetGlobalVectorArray("_SunwardFestivalLights",new Vector4[24]);
            if(sun){sun.intensity=sunIntensity;sun.color=sunColor;sun.transform.rotation=sunRotation;}
            RenderSettings.fogColor=fog;RenderSettings.ambientLight=ambient;
        }
    }
}
