using System;
namespace Sunward.Editor.Automation
{
    // Only inherited by the runner's isolated Unity process; normal editing is unchanged.
    public static class AutomationIsolation
    {
        public static bool Enabled => Environment.GetEnvironmentVariable("SUNWARD_AUTOMATION_READONLY") == "1";
    }
}
