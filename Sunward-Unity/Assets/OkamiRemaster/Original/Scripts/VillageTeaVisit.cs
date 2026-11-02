using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class VillageTeaVisit : MonoBehaviour
    {
        public GameFlow game;
        public bool Invited {get;private set;}
        int story;
        NativeDailyRoutine elder;
        NativeHomeRoom home;
        public string Directions=>"My house is west of the main street, near the first bridge. Its raised timber entrance faces the main street. Walk into that doorway. Come in for tea; I have a few old stories to share.";
        public bool AtHome=>Invited && home && NativeHomeRoom.At(game.Player.transform.position)==home;
        static readonly string[] stories={
            "Long ago, the eight-headed Orochi demanded a maiden from Kamiki Village each year. A white wolf called Shiranui helped the swordsman Nagi defeat the serpent and save Nami. The village remembered that courage for a hundred years.",
            "When darkness returned to Nippon, the wood sprite Sakuya called upon Amaterasu. With Issun as her travelling companion, the sun goddess set out to restore the land, its guardian saplings and the people's hope.",
            "The Celestial Brush is more than a weapon. Its gods grant powers that restore rivers, mend broken things, bring blossoms to barren trees and return life to places touched by curses.",
            "Susano is Nagi's descendant. His loud boasts often hide doubt, yet his story reminds us that courage can grow. Even a frightened person can choose to help someone else.",
            "Shiranui was the white wolf who stood beside Nagi a hundred years before Amaterasu's journey. Stories of that guardian survived in Kamiki long after people forgot the wolf's true nature. A good deed can outlive the one who performs it."
        };
        public string Story=>stories[story%stories.Length];
        public void NextStory(){story=(story+1)%stories.Length;}
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();home=NativeHomeRoom.ByNumber(2);
            if(game.npcObjects.Length>2 && game.npcObjects[2])elder=game.npcObjects[2].GetComponent<NativeDailyRoutine>();

        }
        public void Invite()
        {
            if(!elder && game.npcObjects.Length>2 && game.npcObjects[2])elder=game.npcObjects[2].GetComponent<NativeDailyRoutine>();
            if(!home || !elder){game.Notify("The elder is not ready for a visit yet");return;}
            Invited=true;elder.InviteForTea(home);game.ShowDialogue(Directions);
        }
        public void Talk()
        {
            if(AtHome){game.SetPanel("tea");return;}
            game.ShowDialogue("Village elder\n\n"+(Invited?Directions:"A traveller deserves a quiet cup of tea. Would you like to hear about Shiranui, Amaterasu and the stories of Nippon?"),"elder");
        }
        public void SitForTea()
        {
            if(!AtHome)return;
            game.SetPanel("");game.Services.RestAt(home.transform.position+new Vector3(-.5f,.03f,-.8f),90);
            game.Notify("Tea with the elder · E to stand, then speak to him for another story");
        }
    }
}
