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
        Console.WriteLine("PASS "+checks+" actual native glyph-metric layout/clipping contracts; engine doubles, not Unity screenshots");
    }
}
