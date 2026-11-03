namespace Sunward.Remaster
{
    // Original instrument identities; descriptions explain Sunward's implementation,
    // rather than inventing quotations or claiming these are the original item strings.
    public static class WeaponLore
    {
        public static string Description(OriginalWeaponCatalog.Entry e)
        {
            string technique=e.family=="rosary"?"Long-reaching bead whips. Chain light attacks; hold and release for a charged cast.":e.family=="glaive"?"A cutting instrument with advancing sword strikes. Charge a deliberate heavy blow.":"A divine mirror for broad close-range strikes and heavy charged blows.";
            if(e.resource=="wp2e")technique+=" Tundra Beads release an icy spiral. Keep space around Ammy for its reach.";
            return technique;
        }
        public static string Lore(OriginalWeaponCatalog.Entry e)
        {
            switch(e.resource)
            {
                case "wp20":return "Divine Retribution is Amaterasu's first reflector in Ōkami, a mirror carried above her back.";
                case "wp21":return "Snarling Beast is one of Ōkami's five reflectors, shaped around a fearsome beast motif.";
                case "wp22":return "Infinity Judge is a divine reflector with a distinct judgement-themed design.";
                case "wp23":return "Trinity Mirror is a late reflector in Amaterasu's original arsenal.";
                case "wp24":return "Solar Flare is the final reflector in Ōkami. Its burning appearance suits the sun goddess.";
                case "wp25":return "Tsumugari is the first of Amaterasu's glaives, linking her arsenal with the sword legend of Orochi.";
                case "wp26":return "Seven Strike is an original glaive, one of the five blades available to Amaterasu.";
                case "wp27":return "Blade of Kusanagi bears the name of the legendary grass-cutting sword.";
                case "wp28":return "Eighth Wonder is a late glaive, distinct from the earlier blades in shape and decoration.";
                case "wp29":return "Thunder Edge is the final glaive in Ōkami and carries a lightning identity.";
                case "wp2a":return "Devout Beads introduce Amaterasu's rosary family: sacred beads wielded as a reaching weapon.";
                case "wp2b":return "Life Beads are the second original rosary, continuing the sacred-bead instrument family.";
                case "wp2c":return "Exorcism Beads carry the traditional association of sacred instruments with driving out evil.";
                case "wp2d":return "Resurrection Beads are a late rosary in Amaterasu's original collection.";
                default:return "Tundra Beads are the final rosary in Ōkami, distinguished by their ice identity.";
            }
        }
    }
}
