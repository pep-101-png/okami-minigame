using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    public static class BrushPatterns
    {
        public static bool CherryBomb(IReadOnlyList<Vector2> points)
        {
            if(points==null || points.Count<14)return false;
            Vector2 lo=points[0],hi=lo;float length=0;
            for(int i=1;i<points.Count-2;i++)
            {
                length+=Vector2.Distance(points[i-1],points[i]);lo=Vector2.Min(lo,points[i]);hi=Vector2.Max(hi,points[i]);
                if(i<8)continue;float span=(hi-lo).magnitude;
                if(span<60 || length<span*1.8f || Vector2.Distance(points[0],points[i])>span*.22f)continue;
                float tail=Vector2.Distance(points[i],points[points.Count-1]),travel=0;
                if(tail<span*.22f)continue;
                for(int j=i+1;j<points.Count;j++)travel+=Vector2.Distance(points[j-1],points[j]);
                if(travel/tail<1.4f)return true;
            }
            return false;
        }
    }
}
