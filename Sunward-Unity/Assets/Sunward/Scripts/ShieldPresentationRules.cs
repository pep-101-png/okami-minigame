namespace Sunward
{
    // Shared by all visibility entry points; never equip a village weapon view.
    public static class ShieldPresentationRules
    {
        public const float MountHeight = 1.70f;
        public const float TiltDegrees = 90;
        public const float ChestMotionLimit = .055f;
        public static bool Visible(bool inTrial, bool resting, bool locked, bool result)
        {
            return inTrial && !resting && !locked && !result;
        }
    }
}
