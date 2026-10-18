using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class HomeRest : MonoBehaviour
    {
        public GameFlow game;
        public bool Sleeping { get; private set; }
        public bool Active { get; private set; }

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
            Vector3 from = p.transform.position, to = new Vector3(-36, .18f, -14.1f);
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
            p.animationView.Play("Sleep_Loop", .1f);
            game.Health = game.MaxHealth;
            game.Stamina = game.MaxStamina;
            game.Energy = game.MaxEnergy;
            game.Profile.milestones.sleptAtHome = true;
            game.Save.Save();
            game.Notify("A quiet dream · E or movement to wake");
            while (!p.input.Interact.WasPressedThisFrame() && !p.input.Pause.WasPressedThisFrame() && !p.input.Jump.WasPressedThisFrame() && p.input.Move.ReadValue<Vector2>().sqrMagnitude < .1f)
                yield return null;
            Sleeping = false;
            p.animationView.Play("Sleep_Up", .1f);
            yield return new WaitForSeconds(p.animationView.ClipLength("Sleep_Up"));
            p.Teleport(new Vector3(to.x, .105f, to.z));
            p.Locked = false;
            game.Combat.Rest(false);
            Active = false;
        }
    }
}
