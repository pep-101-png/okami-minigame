namespace Sunward
{
    // Shared by all visibility entry points; never equip a village weapon view.
    public static class ShieldPresentationRules
    {
        public const float MountHeight = 1.46f;
        public const float TiltDegrees = 55;
        public const float ChestMotionLimit = .14f;
        public static bool Visible(bool inTrial, bool resting, bool locked, bool result)
        {
            return inTrial && !resting && !locked && !result;
        }
    }
}
