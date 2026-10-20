namespace Sunward
{
    public static class SurfaceArtRules
    {
        public static string Family(PaintData data)
        {
            if (data.kind == "wood" || data.kind == "stone" || data.kind == "roof")
                return data.kind;
            if (data.kind == "landscape" || data.kind == "grass")
                return "meadow";
            if (data.kind == "shoji" || data.kind == "wash" && data.texture == 5)
                return "plaster";
            return null;
        }
    }
}
