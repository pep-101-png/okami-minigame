namespace Sunward
{
    // Shared with portable tests. Never remove a deform/control bone's scale.
    public static class WolfScaleRules
    {
        public static bool IsContainerScale(string path, string property)
        {
            if (property != "m_LocalScale.x" && property != "m_LocalScale.y" && property != "m_LocalScale.z")
                return false;
            if (string.IsNullOrEmpty(path))
                return true;
            int slash = path.LastIndexOf('/');
            return path.Substring(slash + 1) == "WOLF_RIG";
        }
    }
}
