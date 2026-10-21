namespace Sunward
{
    // Pure rules shared with the portable/Windows PowerShell 5.1 checks.
    public static class LocomotionTuning
    {
        public const float WalkSpeed = 1.1f, JogSpeed = 3.6f, SprintSpeed = 7.2f;
        public static string Gait(float speed, float turn, string current)
        {
            current = current ?? "";
            float idle = current == "Idle_Natural" ? .16f : .08f;
            float walk = current.StartsWith("Walk_") ? 1.65f : 1.45f;
            float sprint = current.StartsWith("Sprint_") ? 5.0f : 5.5f;
            string family = speed < walk ? "Walk" : speed < sprint ? "Jog" : "Sprint";
            if (speed < idle) return "Idle_Natural";
            if (speed > .2f && System.Math.Abs(turn) > 1.15f)
                return family + "_Turn_" + (turn < 0 ? "L" : "R");
            return family == "Sprint" ? "Sprint_Fluid" : family + "_Natural";
        }
        public static float ReferenceSpeed(string state)
        {
            return state.StartsWith("Walk_") ? .5667f : state.StartsWith("Jog_") ? 2.448f : 4.9725f;
        }
    }
}
