using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class VillageRest : MonoBehaviour
    {
        public GameFlow game;
        public DayNightCycle cycle;
        public string displayName = "Rest until evening";
        public bool watchOnly;
        public float radius = 1.8f;
        public static VillageRest ActiveRest { get; private set; }
        public bool Active => ActiveRest == this;
        static readonly System.Collections.Generic.List<VillageRest> places = new System.Collections.Generic.List<VillageRest>();
        bool previouslyLocked;
        void OnEnable() { places.Add(this); }
        void OnDisable()
        {
            places.Remove(this);
            if (Active)
            {
                StopAllCoroutines();
                Restore();
            }
        }
        public static VillageRest Nearby(Vector3 position)
        {
            VillageRest found = null;
            float nearest = float.PositiveInfinity;
            foreach (var place in places)
            {
                float distance = Vector3.Distance(position, place.transform.position);
                if (distance < place.radius && distance < nearest) { found = place; nearest = distance; }
            }
            return found;
        }
        public void Begin()
        {
            if (!game || game.InTrial || game.Blocked || ActiveRest || game.Home.Active)
                return;
            StartCoroutine(Rest());
        }
        IEnumerator Rest()
        {
            ActiveRest = this;
            var p = game.Player;
            previouslyLocked = p.Locked;
            p.Locked = true;
            game.Combat.Cancel();
            game.Combat.Rest(true);
            // Interactions require proximity; never walk/teleport through furniture to a distant marker.
            p.Teleport(transform.position);
            p.transform.rotation = transform.rotation;
            if (watchOnly) p.animationView.SitObserve(true);
            else p.animationView.Play("Sleep_Down", .15f);
            yield return new WaitForSeconds(watchOnly ? .5f : Mathf.Max(.5f, p.animationView.ClipLength("Sleep_Down")));
            if (!watchOnly) p.animationView.Play("Sleep_Loop", .2f);
            if (!watchOnly)
            {
                if (cycle) cycle.RestUntilNextPhase();
                game.Health = game.MaxHealth;
                game.Stamina = game.MaxStamina;
                game.Energy = game.MaxEnergy;
                game.Notify(cycle && cycle.IsNight ? "Evening lanterns awaken · move or interact to wake" : "A new morning · move or interact to wake");
            }
            else game.Notify("Listening to the food hall musician · move or interact to stand");
            // Wait until the initiating key is released before accepting another interaction.
            while (p.input.Interact.IsPressed()) yield return null;
            while (!p.input.Interact.WasPressedThisFrame() && !p.input.Jump.WasPressedThisFrame() && !p.input.Pause.WasPressedThisFrame() && p.input.Move.ReadValue<Vector2>().sqrMagnitude < .1f)
                yield return null;
            if (!watchOnly)
            {
                p.animationView.Play("Sleep_Up", .12f);
                yield return new WaitForSeconds(Mathf.Max(.2f, p.animationView.ClipLength("Sleep_Up")));
            }
            Restore();
        }
        void Restore()
        {
            if (game && game.Player)
            {
                if (watchOnly) game.Player.animationView.SitObserve(false);
                game.Player.Locked = previouslyLocked;
                game.Combat.Rest(false);
            }
            ActiveRest = null;
        }
    }
}
