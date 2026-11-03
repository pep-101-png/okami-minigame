using System;
using System.IO;
using UnityEngine;

namespace Sunward
{
    public sealed class SaveStore
    {
        public ProfileData Data { get; private set; }
        public string Status { get; private set; }
        public string Path { get; }

        public SaveStore()
        {
            string automationData = System.Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_DATA");
            bool isolated = System.Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_READONLY") == "1";
            if (isolated && string.IsNullOrWhiteSpace(automationData))
                throw new System.InvalidOperationException("Automation requires an isolated save directory.");
            if (isolated) Directory.CreateDirectory(automationData);
            Path = System.IO.Path.Combine(isolated ? automationData : Application.persistentDataPath, "Sunward-Unity-v1.json");
            Reload();
        }

        static ProfileData Parse(string text)
        {
            try
            {
                var p = JsonUtility.FromJson<ProfileData>(text);
                return ProgressionRules.Validate(p) ? p : null;
            }
            catch
            {
                return null;
            }
        }

        public bool Reload()
        {
            ProfileData best = null;
            foreach (string f in new[]
            {
                Path,
                Path + ".backup"
            }

            )
                try
                {
                    if (File.Exists(f))
                    {
                        var p = Parse(File.ReadAllText(f));
                        if (p != null && (best == null || p.revision > best.revision))
                            best = p;
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning("Save read: " + e.Message);
                }

            if (best != null)
            {
                Data = best;
                Status = "Memory restored";
                return true;
            }

            Data = Data ?? new ProfileData();
            Status = "New memory · no valid save found";
            return false;
        }

        public bool Save()
        {
            try
            {
                if (!ProgressionRules.Validate(Data))
                    throw new InvalidDataException("Invalid profile");
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(Path));
                Data.revision++;
                string text = JsonUtility.ToJson(Data, true), temp = Path + ".tmp";
                File.WriteAllText(temp, text);
                var verify = Parse(File.ReadAllText(temp));
                if (verify == null || verify.revision != Data.revision)
                    throw new IOException("Verification failed");
                if (File.Exists(Path) && Parse(File.ReadAllText(Path)) != null)
                    File.Copy(Path, Path + ".backup", true);
                File.Copy(temp, Path, true);
                File.Delete(temp);
                Status = "Memory inscribed · saved";
                return true;
            }
            catch (Exception e)
            {
                Status = "Save failed · " + e.Message;
                Debug.LogWarning(Status);
                return false;
            }
        }

        public bool Import(string text)
        {
            try
            {
                var p = Parse(text);
                if (p == null)
                    return false;
                var old = Data;
                p.revision = Math.Max(p.revision, old.revision);
                Data = p;
                if (Save())
                    return true;
                Data = old;
                return false;
            }
            catch
            {
                return false;
            }
        }
    }
}
