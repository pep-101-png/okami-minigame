using System;

namespace Sunward
{
    // Shared by wolf sleep authoring and residents. Triangle invariants are
    // exercised in portable tests; this never stretches either bone to reach.
    public static class LimbArc
    {
        public static void Solve(float upper, float lower, float distance, out float along, out float lift, out float reach)
        {
            if (!float.IsFinite(upper) || !float.IsFinite(lower) || !float.IsFinite(distance) || upper <= 0 || lower <= 0 || distance < 0)
                throw new ArgumentOutOfRangeException(nameof(distance), "Limb lengths and target must be finite, lengths positive.");
            float epsilon = MathF.Min(.0001f, MathF.Min(upper, lower) * .01f);
            reach = Math.Clamp(distance, MathF.Abs(upper - lower) + epsilon, upper + lower - epsilon);
            along = (upper * upper - lower * lower + reach * reach) / (2 * reach);
            lift = MathF.Sqrt(MathF.Max(0, upper * upper - along * along));
        }
    }
}
