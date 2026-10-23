namespace Sunward
{
    // Pure movement policy: also exercised without a Unity editor.
    public static class SwimmingRules
    {
        public const float WaterLevel = -.34f;
        public const float FloatRoot = WaterLevel - .72f;
        public const float JumpImpulse = 7.2f;
        public const float DoubleJumpImpulse = 7.4f;

        public static bool ShouldSwim(bool wasSwimming, float depth, float rootY, float vertical, bool onDeck)
        {
            if (onDeck || (!wasSwimming && vertical > 1.2f))
                return false;
            return depth > (wasSwimming ? .28f : .48f) && rootY < WaterLevel + (wasSwimming ? .38f : .08f);
        }

        public static float BuoyancyVelocity(float rootY, float vertical, float deltaTime)
        {
            float desired = System.Math.Max(-2.8f, System.Math.Min(2.8f, (FloatRoot - rootY) * 5.5f));
            float change = System.Math.Max(0, deltaTime) * 18;
            return vertical < desired ? System.Math.Min(vertical + change, desired) : System.Math.Max(vertical - change, desired);
        }

        public static bool CanJump(float coyote, bool swimming, bool doubleUsed)
        {
            return coyote > 0 || swimming || !doubleUsed;
        }
    }
}
