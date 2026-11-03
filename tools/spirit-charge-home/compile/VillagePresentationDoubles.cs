namespace UnityEngine
{
    public class GUIStyle{public static GUIStyle none=new GUIStyle();}
    public enum ScaleMode{ScaleAndCrop,ScaleToFit,StretchToFill}
    public static partial class GUI
    {
        public static System.Collections.Generic.List<Rect> InkRects=new System.Collections.Generic.List<Rect>();public static int InkGroups;public static void BeginGroup(Rect r){InkGroups++;}public static void EndGroup(){}
        public static void DrawTextureWithTexCoords(Rect r,Texture2D t,Rect uv){InkRects.Add(r);}
        public static void DrawTexture(Rect r,Texture2D t,ScaleMode mode){}
        public static bool Button(Rect r,string text,GUIStyle style)=>false;
    }
}

namespace UnityEngine.InputSystem.Controls{public class ButtonControl:UnityEngine.InputSystem.Key{}}
