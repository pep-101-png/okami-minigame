using System;

namespace Sunward
{
    // Keep combo history separate from the currently held/queued input. In
    // particular, releasing RMB must never reuse an older queued light input.
    public sealed class AttackSequence
    {
        bool active, previousHeavy;
        int index;
        public int Select(bool heavy, bool continuation, int lightCount, int heavyCount)
        {
            int count = heavy ? heavyCount : lightCount;
            if (count < 1)
                throw new ArgumentOutOfRangeException(nameof(count));
            index = active && continuation && previousHeavy == heavy ? (index + 1) % count : 0;
            previousHeavy = heavy;
            active = true;
            return index;
        }

        public void Reset()
        {
            active = false;
            index = 0;
        }
    }
}
