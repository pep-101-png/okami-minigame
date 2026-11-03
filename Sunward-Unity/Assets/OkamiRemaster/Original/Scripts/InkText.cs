using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    // Original Latin atlas; measurement and painting share the same glyph metrics.
    public static class InkText
    {
        [System.Serializable]sealed class Atlas{public int width,height;public Glyph[] glyphs;}
        [System.Serializable]sealed class Glyph{public int code,x,y,width,height,top,advance;}
        static Texture2D texture;static Atlas atlas;static Dictionary<char,Glyph> glyphs;
        static void Load()
        {
            if(glyphs!=null)return;glyphs=new Dictionary<char,Glyph>();texture=Resources.Load<Texture2D>("Okami/UI/MessageGlyphs");var data=Resources.Load<TextAsset>("Okami/UI/MessageGlyphs");if(!data || !texture)return;atlas=JsonUtility.FromJson<Atlas>(data.text);foreach(var g in atlas.glyphs)glyphs[(char)g.code]=g;
        }
        static Glyph Find(char c){if(glyphs.TryGetValue(c,out var g))return g;return glyphs.TryGetValue('?',out g)?g:null;}
        static float Advance(char c,float em){var g=Find(c);return (c==' '?65:g!=null?g.advance:88)*em/160f;}
        static float WordWidth(string text,int start,float em){float w=0;for(int i=start;i<text.Length && text[i]!=' ' && text[i]!='\n';i++)w+=Advance(text[i],em);return w;}
        public static float MeasureHeight(string text,float width,float em)
        {
            Load();if(string.IsNullOrEmpty(text))return em;float x=0,y=0;
            for(int i=0;i<text.Length;i++)
            {
                char c=text[i];if(c=='\r')continue;if(c=='\n'){x=0;y+=em*.98f;continue;}
                if(c!=' ' && (i==0 || text[i-1]==' ' || text[i-1]=='\n')){float word=WordWidth(text,i,em);if(word<width && x>0 && x+word>width){x=0;y+=em*.98f;}}
                float advance=Advance(c,em);if(x>0 && x+advance>width){x=0;y+=em*.98f;}x+=advance;
            }
            return y+em;
        }
        public static void Draw(string text,Rect area,float em,Color colour,bool wrap=true)
        {
            Load();if(!texture || string.IsNullOrEmpty(text) || area.width<=0 || area.height<=0)return;
            var old=GUI.color;GUI.color=colour;float x=0,y=0;GUI.BeginGroup(area);
            for(int i=0;i<text.Length;i++)
            {
                char c=text[i];if(c=='\r')continue;if(c=='\n'){x=0;y+=em*.98f;continue;}
                if(wrap && c!=' ' && (i==0 || text[i-1]==' ' || text[i-1]=='\n')){float word=WordWidth(text,i,em);if(word<area.width && x>0 && x+word>area.width){x=0;y+=em*.98f;}}
                var g=Find(c);if(g==null)continue;float advance=Advance(c,em);
                if(x+advance>area.width && x>0){if(!wrap)break;x=0;y+=em*.98f;}
                if(y+em>area.height)break;
                if(c!=' ')GUI.DrawTextureWithTexCoords(new Rect(x,y+g.top*em/160f,g.width*em/160f,g.height*em/160f),texture,new Rect(g.x/(float)atlas.width,1-(g.y+g.height)/(float)atlas.height,g.width/(float)atlas.width,g.height/(float)atlas.height));
                x+=advance;
            }
            GUI.EndGroup();GUI.color=old;
        }
    }
}
