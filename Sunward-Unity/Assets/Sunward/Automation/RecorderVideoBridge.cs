#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;
namespace Sunward.Editor.Automation
{
    // Optional capability-checked adapter. No Recorder package or assembly dependency is added.
    // PNG frames are ALWAYS kept until the outer runner verifies an MP4 with ffprobe.
    public sealed class RecorderVideoBridge : IDisposable
    {
        object controller;
        UnityEngine.Object settings, movie;
        public string status = "not_installed", detail = "", candidate = "";
        static Type Find(string name) => AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType(name, false)).FirstOrDefault(t => t != null);
        static bool Set(object target, string name, object value)
        {
            var type = target.GetType(); var property = type.GetProperty(name); var field = type.GetField(name);
            Type memberType = property != null && property.CanWrite ? property.PropertyType : field?.FieldType;
            if (memberType == null) return false;
            object converted = memberType.IsEnum ? Enum.Parse(memberType, value.ToString()) : Convert.ChangeType(value, memberType);
            if (property != null && property.CanWrite) property.SetValue(target, converted); else field.SetValue(target, converted);
            return true;
        }
        static void SetObject(object target, string name, object value)
        {
            var p = target.GetType().GetProperty(name);
            if (p != null && p.CanWrite) { p.SetValue(target,value); return; }
            var f = target.GetType().GetField(name);
            if (f == null) throw new NotSupportedException("Recorder member unavailable: " + name);
            f.SetValue(target,value);
        }
        public void Start(RenderTexture texture, int fps, string outputBase, bool prefer)
        {
            if (!prefer) { status = "disabled_by_configuration"; return; }
            var controllerType = Find("UnityEditor.Recorder.RecorderController");
            if (controllerType == null) return;
            try {
                var settingsType = Find("UnityEditor.Recorder.RecorderControllerSettings");
                var movieType = Find("UnityEditor.Recorder.MovieRecorderSettings");
                var inputType = Find("UnityEditor.Recorder.Input.RenderTextureInputSettings");
                if (settingsType == null || movieType == null || inputType == null) throw new NotSupportedException("Recorder RenderTexture/movie API not compatible.");
                Directory.CreateDirectory(Path.GetDirectoryName(outputBase));
                settings = ScriptableObject.CreateInstance(settingsType); movie = ScriptableObject.CreateInstance(movieType);
                var input = Activator.CreateInstance(inputType);
                SetObject(input,"RenderTexture",texture);
                Set(input,"OutputWidth",texture.width); Set(input,"OutputHeight",texture.height);
                SetObject(movie,"ImageInputSettings",input);
                if (!Set(movie,"Enabled",true) || !Set(movie,"OutputFile",outputBase) || !Set(settings,"FrameRate",fps)) throw new NotSupportedException("Recorder settings unavailable.");
                Set(movie,"OutputFormat","MP4"); Set(movie,"CaptureAlpha",false); Set(movie,"CaptureAudio",false); Set(movie,"VideoBitRateMode","Low");
                Set(settings,"CapFrameRate",true); Set(settings,"FrameRatePlayback","Constant");
                settingsType.GetMethod("AddRecorderSettings").Invoke(settings,new[] { movie });
                settingsType.GetMethod("SetRecordModeToManual").Invoke(settings,null);
                controller = Activator.CreateInstance(controllerType,settings);
                var prepared = controllerType.GetMethod("PrepareRecording").Invoke(controller,null);
                if (prepared is bool p && !p) throw new Exception("Recorder preparation rejected this environment.");
                var started = controllerType.GetMethod("StartRecording").Invoke(controller,null);
                if (started is bool s && !s) throw new Exception("Recorder could not start.");
                candidate = outputBase + ".mp4"; status = "recording_candidate_unverified";
            } catch (Exception e) { status = "incompatible_or_unavailable"; detail = e.GetBaseException().Message; Dispose(); }
        }
        public void Dispose()
        {
            try { controller?.GetType().GetMethod("StopRecording")?.Invoke(controller,null); }
            catch (Exception e) { detail += " Stop: " + e.GetBaseException().Message; status = "stop_failed"; }
            controller = null;
            if (settings) UnityEngine.Object.DestroyImmediate(settings);
            if (movie) UnityEngine.Object.DestroyImmediate(movie);
        }
    }
}

#endif
