using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

namespace Sunward.Remaster
{
    public sealed class NativePoseBank
    {
        public sealed class Clip
        {
            public string Name; public int Samples; public float Duration; public bool Loop;
            public Vector3[] Position, Scale; public Quaternion[] Rotation;
        }
        public readonly int BoneCount;
        readonly Dictionary<string, Clip> clips = new Dictionary<string, Clip>();
        public NativePoseBank(string resource)
        {
            var asset = Resources.Load<TextAsset>(resource);
            if (!asset) throw new InvalidDataException("Missing original motion bank: " + resource);
            using (var reader = new BinaryReader(new MemoryStream(asset.bytes)))
            {
                if (Encoding.ASCII.GetString(reader.ReadBytes(4)) != "OPB1" || reader.ReadInt32() != 1)
                    throw new InvalidDataException("Unsupported native pose bank");
                BoneCount = reader.ReadInt32(); int count = reader.ReadInt32();
                if (BoneCount < 2 || BoneCount > 128 || count < 1 || count > 512) throw new InvalidDataException("Invalid native pose bank size");
                for (int i = 0; i < count; i++)
                {
                    int length = reader.ReadInt32();
                    if (length < 1 || length > 64) throw new InvalidDataException("Invalid clip name");
                    var c = new Clip { Name = Encoding.ASCII.GetString(reader.ReadBytes(length)), Samples = reader.ReadInt32(), Duration = reader.ReadSingle(), Loop = reader.ReadInt32() != 0 };
                    if (c.Samples < 2 || c.Samples > 12000 || c.Duration <= 0 || c.Duration > 200) throw new InvalidDataException("Invalid native clip duration");
                    int n = checked(c.Samples * BoneCount);
                    c.Position = new Vector3[n]; c.Scale = new Vector3[n]; c.Rotation = new Quaternion[n];
                    for (int j = 0; j < n; j++)
                    {
                        c.Position[j] = Vector(reader); c.Rotation[j] = new Quaternion(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle()); c.Scale[j] = Vector(reader);
                    }
                    clips.Add(c.Name, c);
                }
                if (reader.BaseStream.Position != reader.BaseStream.Length) throw new InvalidDataException("Unexpected native bank trailing bytes");
            }
        }
        static Vector3 Vector(BinaryReader reader) => new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
        public Clip Find(string name) => clips.TryGetValue(name, out var clip) ? clip : null;
        public void Sample(Clip clip, float time, Transform[] bones, Vector3[] fromPosition, Quaternion[] fromRotation, Vector3[] fromScale, float blend, bool loop, bool mirror = false)
        {
            float phase = loop ? Mathf.Repeat(time, clip.Duration) / clip.Duration : Mathf.Clamp01(time / clip.Duration);
            float frame = phase * (clip.Samples - 1); int a = Mathf.FloorToInt(frame), b = Mathf.Min(a + 1, clip.Samples - 1); float u = frame - a;
            for (int i = 0; i < BoneCount; i++)
            {
                int ka = a * BoneCount + i, kb = b * BoneCount + i;
                var position = Vector3.Lerp(clip.Position[ka], clip.Position[kb], u);
                var rotation = Quaternion.Slerp(clip.Rotation[ka], clip.Rotation[kb], u);
                if (mirror) { position.x = -position.x; rotation = new Quaternion(rotation.x, -rotation.y, -rotation.z, rotation.w); }
                bones[i].localPosition = Vector3.Lerp(fromPosition[i], position, blend);
                bones[i].localRotation = Quaternion.Slerp(fromRotation[i], rotation, blend);
                bones[i].localScale = Vector3.Lerp(fromScale[i], Vector3.Lerp(clip.Scale[ka], clip.Scale[kb], u), blend);
            }
        }
    }
}
