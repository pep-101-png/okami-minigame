using System;
using System.Collections;
using System.IO;
using System.Reflection;
using System.Text.Json;
using UnityEngine;
using Sunward.Remaster;
public static class TextBoundsTests
{
    public static void Run(string assets)
    {
        var type=typeof(InkText);var glyph=type.GetNestedType("Glyph",BindingFlags.NonPublic);var dictionary=Activator.CreateInstance(typeof(System.Collections.Generic.Dictionary<,>).MakeGenericType(typeof(char),glyph)) as IDictionary;
        var doc=JsonDocument.Parse(File.ReadAllText(Path.Combine(assets,"OkamiRemaster/Original/Resources/Okami/UI/MessageGlyphs.json")));
        foreach(var row in doc.RootElement.GetProperty("glyphs").EnumerateArray())
        {var g=Activator.CreateInstance(glyph,true);foreach(var prop in row.EnumerateObject())glyph.GetField(prop.Name).SetValue(g,prop.Value.GetInt32());dictionary.Add((char)row.GetProperty("code").GetInt32(),g);}
        var atlas=type.GetNestedType("Atlas",BindingFlags.NonPublic);var data=Activator.CreateInstance(atlas,true);atlas.GetField("width").SetValue(data,2400);atlas.GetField("height").SetValue(data,2400);
        type.GetField("glyphs",BindingFlags.Static|BindingFlags.NonPublic).SetValue(null,dictionary);type.GetField("atlas",BindingFlags.Static|BindingFlags.NonPublic).SetValue(null,data);type.GetField("texture",BindingFlags.Static|BindingFlags.NonPublic).SetValue(null,new Texture2D());
        int checks=0;
        foreach(string text in new[]{"VITALITY +12 max health per rank.","WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW", "A moment of stillness.\nRETURN HOME KEEP PROGRESS"})foreach(float width in new[]{96f,262f,590f})
        {
            float h=InkText.MeasureHeight(text,width,29);GUI.InkRects.Clear();int groups=GUI.InkGroups;InkText.Draw(text,new Rect(80,40,width,h),29,Color.white);
            if(GUI.InkGroups!=groups+1)throw new Exception("Native text is not clipped to its allocated region");checks++;
            foreach(var r in GUI.InkRects){if(r.x<-.001f || r.y<-.001f || r.x+r.width>width+.001f || r.y+r.height>h+.001f)throw new Exception("Native lettering exceeds measured width or height");checks++;}
        }
        GUI.InkRects.Clear();InkText.Draw("WWWWWWWWWWWWWWWWWW",new Rect(20,20,96,32),29,Color.white,false);foreach(var r in GUI.InkRects){if(r.x+r.width>96.001f)throw new Exception("Unwrapped caption leaves its bounds");checks++;}
        // Exercise complete in-project dialogue at actual body sizes. Every
        // non-whitespace glyph must be painted, not merely clipped away safely.
        var corpus=new System.Collections.Generic.List<string>{new string('W',500),"first\n\nsecond\n\nthird\n\nfourth\n\nfifth"};
        foreach(var file in Directory.GetFiles(assets,"*.cs",SearchOption.AllDirectories))
            foreach(System.Text.RegularExpressions.Match match in System.Text.RegularExpressions.Regex.Matches(File.ReadAllText(file),@"ShowDialogue\(""((?:[^""\\]|\\.)*)"""))
                corpus.Add(System.Text.RegularExpressions.Regex.Unescape(match.Groups[1].Value));
        foreach(string story in (string[])typeof(VillageTeaVisit).GetField("stories",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null))corpus.Add(story);
        var world=JsonDocument.Parse(File.ReadAllText(Path.Combine(assets,"Sunward/Data/Valley.json"))).RootElement.GetProperty("world");
        foreach(var npc in world.GetProperty("npcs").EnumerateArray())
        {var lines=new System.Collections.Generic.List<string>();foreach(var line in npc.GetProperty("lines").EnumerateArray())lines.Add(line.GetString());corpus.Add(npc.GetProperty("name").GetString()+"\n\n"+string.Join("\n\n",lines));}
        int legacyTruncations=0;var previews=new System.Collections.Generic.List<object>();
        foreach(var size in new[]{new[]{800,600},new[]{1280,720},new[]{1366,768},new[]{1920,1080},new[]{3840,2160}})
        {
            int oldWidth=Screen.width,oldHeight=Screen.height;Screen.width=size[0];Screen.height=size[1];
            var flags=BindingFlags.Static|BindingFlags.NonPublic;var bubbleRect=(Rect)typeof(VillagePresentation).GetMethod("DialogueBounds",flags).Invoke(null,null);var bodyRect=(Rect)typeof(VillagePresentation).GetMethod("DialogueBody",flags).Invoke(null,new object[]{bubbleRect});float width=bodyRect.width,height=bodyRect.height,em=(float)typeof(VillagePresentation).GetProperty("DialogueEm",flags).GetValue(null);
            Screen.width=oldWidth;Screen.height=oldHeight;
            foreach(string text in corpus)
            {
                for(int start=0;start<text.Length;start+=160){string old=text.Substring(start,Math.Min(160,text.Length-start));if(InkText.MeasureHeight(old,width,em)>height)legacyTruncations++;}
                var pages=InkText.Paginate(text,width,height,em);if(string.Concat(pages)!=text)throw new Exception("Pagination dropped dialogue characters");checks++;
                foreach(string part in pages)
                {
                    GUI.InkRects.Clear();InkText.Draw(part,new Rect(0,0,width,height),em,Color.white);int expected=0;foreach(char c in part)if(c!=' ' && c!='\n' && c!='\r')expected++;
                    if(GUI.InkRects.Count!=expected)throw new Exception("A dialogue page silently hides its final lines: "+part);checks++;
                    var complete=GUI.InkRects.ToArray();
                    if(text.StartsWith("Amaterasu, Shiranui sleeps") && (size[0]==800 || size[0]==1366))previews.Add(new{screenWidth=size[0],screenHeight=size[1],width,height,em,bodyX=bodyRect.x,bodyY=bodyRect.y,text=part,rects=Array.ConvertAll(complete,r=>new{r.x,r.y,r.width,r.height})});
                    GUI.InkRects.Clear();InkText.Draw(part,new Rect(0,0,width,height),em,Color.white,true,Math.Min(40,part.Length));
                    for(int i=0;i<GUI.InkRects.Count;i++)if(GUI.InkRects[i].x!=complete[i].x || GUI.InkRects[i].y!=complete[i].y)throw new Exception("Typewriter moves already-visible words");checks++;
                }
            }
        }
        string previewPath=Environment.GetEnvironmentVariable("SUNWARD_DIALOGUE_PREVIEW");if(!string.IsNullOrEmpty(previewPath))File.WriteAllText(previewPath,JsonSerializer.Serialize(previews));
        if(legacyTruncations==0)throw new Exception("Dialogue corpus did not reproduce the old fixed-page cutoff");
        Console.WriteLine("Old fixed 160-character pages overflow in "+legacyTruncations+" corpus/resolution cases; repaired pages retain all glyphs.");
        DialogueInteractionTests.Run(corpus.Find(x=>x.Length>300 && x.Contains(" "))??corpus[0]);
        Console.WriteLine("PASS "+checks+" actual native glyph-metric layout/clipping contracts; engine doubles, not Unity screenshots");
    }
}
