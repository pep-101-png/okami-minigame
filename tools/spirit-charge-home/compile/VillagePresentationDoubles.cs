namespace UnityEngine
{
    public class GUIStyle{public static GUIStyle none=new GUIStyle();}
    public enum ScaleMode{ScaleAndCrop,ScaleToFit,StretchToFill}
    public static partial class GUI
    {
        public static void DrawTextureWithTexCoords(Rect r,Texture2D t,Rect uv){}
        public static void DrawTexture(Rect r,Texture2D t,ScaleMode mode){}
        public static bool Button(Rect r,string text,GUIStyle style)=>false;
    }
}

namespace UnityEngine.InputSystem.Controls{public class ButtonControl:UnityEngine.InputSystem.Key{}}
