using UnityEngine;
namespace Sunward.Remaster
{
    // These hints describe Sunward's new quest, not an episode of the original story.
    public static class CelestialHints
    {
        public static string Shop(ProfileData p)=>p.shiranuiUnlock>=2?"Every blessing carries the warmth of the restored sun.":ProgressionRules.Advanced(p)?"Five deeper ranks have appeared along each blessing path.":p.shiranuiUnlock==1?"The old paths may yet deepen when your spirit reaches its thirtieth season.":"Hana: A blessing left untended can leave even a great spirit unbalanced.";
        public static string Villager(ProfileData p,int person)
        {
            if(p.bossWins==0)return person%2==0?"When the bell beneath us grows quiet, listen again to the river. Some roads are hidden by their own song.":"The river keeper used to speak of a light behind the falling water. I have only ever seen mist.";
            if(p.shiranuiUnlock==0)return person%2==0?"A pale light followed the river after that dreadful bell fell silent. Perhaps the old waterfall remembers a road.":"A traveller returned speaking of a sleeping wolf beyond the clouds. The palace keeper may know what troubles his dreams.";
            if(p.shiranuiUnlock==1)return person%2==0?"The garden feels warmer. Yet even at noon, something watches from the palace's far passage.":"Hana has been studying the roots of her blessings. Perhaps visit her again when your spirit has grown.";
            return "Even the river sounds different now. The flowers turn toward the palace as though dawn had come twice.";
        }
        public static string Keeper(ProfileData p)
        {
            if(p.shiranuiUnlock==0)return ProgressionRules.DawnReady(p)?"Your light no longer leans upon one blessing alone. Beyond the palace's eastern eaves, the veiled sentinel has opened its courtyard. Meet its blade with a steady brush; its guard is not unbroken.":"Shiranui dreams within the palace. A sentinel keeps the courtyard beyond its eastern eaves, listening for a spirit in its twentieth season, with no blessing left untended. The village's blessing keeper can help you find your balance.";
            if(p.shiranuiUnlock==1)return ProgressionRules.EclipseReady(p)?"The last passage inside the chamber has begun to stir. Its shadow wears many tails. When they gather to strike, a sure brushstroke may leave it open.":"You have freed the sleeping light, but a deeper shadow remains. In your thirtieth season, five hidden steps will appear along every blessing path. Tend them all; then listen at the chamber's far passage.";
            return "The seal is gone. Shiranui's light moves with you, and even this old garden has remembered how to bloom. There is no guardian left between you and the sun.";
        }
        public static string Gate(ProfileData p,int kind)
        {
            if(kind==1)return "The courtyard seal listens for balanced growth.\n\nSpirit level: "+ProgressionRules.Level(p)+" / 20\nBase blessing paths completed: "+ProgressionRules.CompletedPaths(p)+" / "+ProgressionRules.Upgrades.Length+"\n\n"+(ProgressionRules.DawnReady(p)?"The mist parts. Walk through when you are ready.":"The keeper may recognise what is still missing.");
            return "The eclipse passage waits beyond the first awakening.\n\nSpirit level: "+ProgressionRules.Level(p)+" / 30\nDeepened blessing paths completed: "+ProgressionRules.CompletedPaths(p,true)+" / "+ProgressionRules.Upgrades.Length+"\n\n"+(ProgressionRules.EclipseReady(p)?"The shadow yields a path. Walk through when you are ready.":"Five further ranks in every path awaken after the second form and level thirty.");
        }
    }
}
