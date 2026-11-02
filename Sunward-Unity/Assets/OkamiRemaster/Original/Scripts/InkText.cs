using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    // Draw the actual original Latin message atlas. No replacement font artwork.
    public static class InkText
    {
        [System.Serializable]sealed class Atlas{public int width,height;public Glyph[] glyphs;}
        [System.Serializable]sealed class Glyph{public int code,x,y,width,height,top,advance;}
        static Texture2D texture;static Atlas atlas;static Dictionary<char,Glyph> glyphs;
        static void Load()
        {
            if(glyphs!=null)return;glyphs=new Dictionary<char,Glyph>();texture=Resources.Load<Texture2D>("Okami/UI/MessageGlyphs");var data=Resources.Load<TextAsset>("Okami/UI/MessageGlyphs");if(!data || !texture)return;atlas=JsonUtility.FromJson<Atlas>(data.text);foreach(var g in atlas.glyphs)glyphs[(char)g.code]=g;
        }
        public static void Draw(string text,Rect area,float em,Color colour,bool wrap=true)
        {
            Load();if(!texture || string.IsNullOrEmpty(text))return;
            var old=GUI.color;GUI.color=colour;float x=0,y=0,line=em*.94f;
            for(int i=0;i<text.Length;i++)
            {
                char c=text[i];
                if(wrap && c!=' ' && c!='\n' && (i==0 || text[i-1]==' ' || text[i-1]=='\n'))
                {
                    float word=0;
                    for(int j=i;j<text.Length && text[j]!=' ' && text[j]!='\n';j++){Glyph letter;if(!glyphs.TryGetValue(text[j],out letter))letter=glyphs['?'];word+=letter.advance*em/160f;}
                    if(word<area.width && x+word>area.width && x>0){x=0;y+=line;}
                }
                if(c=='\r')continue;if(c=='\n'){x=0;y+=line;continue;}
                Glyph g;if(!glyphs.TryGetValue(c,out g))g=glyphs['?'];
                float advance=(c==' '?65:g.advance)*em/160f;
                if(wrap && x+advance>area.width && x>0){x=0;y+=line;}
                if(y+em>area.height)break;
                if(c!=' ')GUI.DrawTextureWithTexCoords(new Rect(area.x+x,area.y+y+g.top*em/160f,g.width*em/160f,g.height*em/160f),texture,new Rect(g.x/(float)atlas.width,1-(g.y+g.height)/(float)atlas.height,g.width/(float)atlas.width,g.height/(float)atlas.height));
                x+=advance;
            }
            GUI.color=old;
        }
    }
}
