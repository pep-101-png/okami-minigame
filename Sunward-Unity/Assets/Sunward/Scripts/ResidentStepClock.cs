namespace Sunward
{
    public sealed class ResidentSoundBudget
    {
        float next;
        public bool Allow(float now)
        {
            if (now < next) return false;
            next = now + .20f;
            return true;
        }
        public void Reset() { next = 0; }
    }

    // Sound is driven by real travelled distance, never by IK contact repairs.
    public sealed class ResidentStepClock
    {
        float distance, cooldown;
        public bool Advance(float moved, float dt, bool walking)
        {
            cooldown = System.Math.Max(0, cooldown - dt);
            if (!walking || moved > .75f || dt <= 0 || moved / dt < .12f)
            {
                distance = 0;
                return false;
            }
            distance += moved;
            if (distance < .32f || cooldown > 0) return false;
            distance %= .32f;
            cooldown = .28f;
            return true;
        }
    }
}
