// Shared ScrollUI members are declared here only for compiling the new partial
// against the actual game assembly. The shipped ScrollUI supplies these members.
using UnityEngine;namespace Sunward{public sealed partial class ScrollUI:MonoBehaviour{public GameFlow game;GUIStyle body,title,small,button;Texture2D hintInk;void Label(string text,GUIStyle style){}bool Button(string text,GUIStyle style)=>false;void DrawPaper(Rect r){}}}
