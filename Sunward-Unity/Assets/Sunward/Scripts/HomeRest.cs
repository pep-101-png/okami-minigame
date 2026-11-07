using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class HomeRest : MonoBehaviour
    {
        public GameFlow game;
        public bool Sleeping { get; private set; }
        public bool Active { get; private set; }
        public void CancelRest()
        {
            if(!Active)return;
            StopAllCoroutines();Active=Sleeping=false;
            if(game && game.Player)game.Player.Locked=false;
        }

        public void Begin()
        {
            if (!Active)
                StartCoroutine(Rest());
        }

        IEnumerator Rest()
        {
            Active = true;
            var p = game.Player;
            p.Locked = true;
            game.Combat.Cancel();
            game.Combat.Rest(true);
            Vector3 from = p.transform.position, to = HomeLayout.Bed;
            Quaternion rotation = p.transform.rotation;
            float t = 0;
            p.animationView.Play("Walk_Natural");
            while (t < .8f)
            {
                t += Time.deltaTime;
                float u = Mathf.SmoothStep(0, 1, t / .8f);
                p.Teleport(Vector3.Lerp(from, to, u));
                p.transform.rotation = Quaternion.Slerp(rotation, Quaternion.Euler(0, -90, 0), u);
                yield return null;
            }

            p.animationView.Play("Sleep_Down", .1f);
            yield return new WaitForSeconds(p.animationView.ClipLength("Sleep_Down"));
            Sleeping = true;
            var festival=game.GetComponent<Sunward.Remaster.VillageFestival>();if(festival)festival.SleepToNextTime();
            p.animationView.Play("Sleep_Loop", .1f);
            Sunward.Remaster.HomeBlessings.BedBonus(game.Profile,Sunward.Remaster.HomeBlessings.Now);
            game.Health = game.MaxHealth;
            game.Stamina = game.MaxStamina;
            game.Energy = game.MaxEnergy;
            game.Profile.milestones.sleptAtHome = true;
            game.Save.Save();
            game.Notify("Bed blessing · +50 health and stamina for fifteen minutes · E or movement to wake");
            while (!p.input.Interact.WasPressedThisFrame() && !p.input.Pause.WasPressedThisFrame() && !p.input.Jump.WasPressedThisFrame() && p.input.Move.ReadValue<Vector2>().sqrMagnitude < .1f)
                yield return null;
            Sleeping = false;
            p.animationView.Play("Sleep_Up", .1f);
            yield return new WaitForSeconds(p.animationView.ClipLength("Sleep_Up"));
            p.Teleport(new Vector3(to.x, game.valley.Height(to)+.025f, to.z));
            p.Locked = false;
            game.Combat.Rest(false);
            Active = false;
        }
    }
}
