using UnityEngine;

namespace Sunward.Remaster
{
    // Original core DDS artwork with Sunward emission adapters. This is not a
    // claim that the original EST/SEQ event interpreter is fully reconstructed.
    public sealed class OriginalAtmosphere : MonoBehaviour
    {
        public GameFlow game;
        ParticleSystem trail, leaves, spirit, spiritGlow;
        SkinnedMeshRenderer spiritSurface;
        float nextWake;
        public static ParticleSystem Create(string sprite, Transform parent, Vector3 position,
            float rate, float size, float life, float speed, float radius = 0)
        {
            var texture = Resources.Load<Texture2D>("Okami/Effects/" + sprite);
            var surface = Resources.Load<Material>("Okami/Effects/Surface");
            if (!texture || !surface) { Debug.LogError("Original effect sprite/material missing: " + sprite); return null; }
            var go = new GameObject("Original core artwork · " + sprite);
            go.transform.SetParent(parent, false); go.transform.localPosition = position;
            var system = go.AddComponent<ParticleSystem>(); system.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = system.main; main.loop = true; main.startLifetime = life; main.startSize = size;
            main.startSpeed = speed; main.maxParticles = 250; main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
            var emission = system.emission; emission.rateOverTime = rate;
            var shape = system.shape; shape.enabled = radius > 0;
            if (radius > 0) { shape.shapeType = ParticleSystemShapeType.Circle; shape.radius = radius; shape.radiusThickness = 0; shape.rotation = new Vector3(90, 0, 0); }
            var velocity = system.velocityOverLifetime; velocity.enabled = true;
            velocity.space = ParticleSystemSimulationSpace.World;
            velocity.x = new ParticleSystem.MinMaxCurve(-.12f, .22f); velocity.y = new ParticleSystem.MinMaxCurve(.15f, .4f);
            velocity.z = new ParticleSystem.MinMaxCurve(-.1f, .12f);
            var fade = system.colorOverLifetime; fade.enabled = true;
            var gradient = new Gradient(); gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(.8f, .12f), new GradientAlphaKey(0, 1) });
            fade.color = gradient;
            if (sprite == "Leaf" || sprite == "Blossom")
            {
                var sheet = system.textureSheetAnimation; sheet.enabled = true; sheet.numTilesX = 4; sheet.numTilesY = 4;
                sheet.startFrame = new ParticleSystem.MinMaxCurve(0, 1); sheet.frameOverTime = 0;
                var rotation = system.rotationOverLifetime; rotation.enabled = true; rotation.z = new ParticleSystem.MinMaxCurve(-1, 1);
            }
            else if (sprite == "Steam") { var sheet = system.textureSheetAnimation; sheet.enabled = true; sheet.numTilesX = 1; sheet.numTilesY = 2; sheet.startFrame = new ParticleSystem.MinMaxCurve(0, 1); sheet.frameOverTime = 0; }
            else if (sprite == "Spark") { var sheet=system.textureSheetAnimation;sheet.enabled=true;sheet.numTilesX=4;sheet.numTilesY=1;sheet.frameOverTime=1; }
            else if (sprite == "Flame") { var sheet=system.textureSheetAnimation;sheet.enabled=true;sheet.numTilesX=2;sheet.numTilesY=2;sheet.startFrame=new ParticleSystem.MinMaxCurve(0,1);sheet.frameOverTime=1; }
            var renderer = system.GetComponent<ParticleSystemRenderer>();
            renderer.sharedMaterial = new Material(surface) { mainTexture = texture };
            go.AddComponent<OriginalParticleMaterial>(); system.Play(); return system;
        }
        void Start()
        {
            if (!game) game = FindFirstObjectByType<GameFlow>();
            if (!game) return;
            trail = Create("Leaf", game.Player.transform, new Vector3(0, .22f, -.5f), 0, .35f, 1.5f, .25f);
            leaves = Create("Blossom", null, new Vector3(GardenPond.X, 3.7f, GardenPond.Z), 5, .20f, 5, .04f, 2.5f);
            if (leaves) { var v = leaves.velocityOverLifetime; v.y = -.32f; }
            Create("Steam", null, new Vector3(GardenPond.X, GardenPond.Water + .12f, GardenPond.Z), 2, 1.15f, 5, .08f, 1.8f);
        }
        void Update()
        {
            if (!game || !trail) return;
            var emission = trail.emission;
            emission.rateOverTime = !game.Blocked && game.Player.Grounded && game.Player.Speed > WolfMotor.JogSpeed + .4f ? 16 : 0;
            var native = game.Player.GetComponent<NativeAmaterasu>();
            if(native && native.Shiranui && !spirit)
            {
                spirit=Create("Spirit",game.Player.transform,Vector3.zero,0,.10f,.7f,.03f);
                spiritGlow=Create("SpiritGlow",game.Player.transform,Vector3.zero,0,.18f,.6f,.015f);
            }
            if(spirit && native)
            {
                var body=native.BodySurface;
                if(body && body!=spiritSurface)
                {
                    spiritSurface=body;
                    foreach(var p in new[]{spirit,spiritGlow})if(p)
                    {
                        var shape=p.shape;shape.enabled=true;shape.shapeType=ParticleSystemShapeType.SkinnedMeshRenderer;
                        shape.skinnedMeshRenderer=body;shape.meshShapeType=ParticleSystemMeshShapeType.Triangle;
                        var main=p.main;main.simulationSpace=ParticleSystemSimulationSpace.Local;
                        main.startSize=new ParticleSystem.MinMaxCurve(p==spirit?.06f:.12f,p==spirit?.13f:.22f);
                        main.startColor=new Color(1,.94f,.78f,.7f);
                        var velocity=p.velocityOverLifetime;velocity.y=new ParticleSystem.MinMaxCurve(.03f,.10f);
                    }
                }
                bool active=native.Shiranui && !game.Blocked && body;
                var e=spirit.emission;e.rateOverTime=active?48:0;
                if(spiritGlow){var g=spiritGlow.emission;g.rateOverTime=active?24:0;}
                if(!active){spirit.Clear();if(spiritGlow)spiritGlow.Clear();}
            }
            if(game.Player.Swimming && game.Player.Speed>.15f && !game.Blocked && Time.time>=nextWake)
            {
                nextWake=Time.time+.3f;
                var p=Create("Spark",null,new Vector3(game.Player.transform.position.x,-.30f,game.Player.transform.position.z),0,.65f,.55f,.015f);
                if(p)
                {
                    var sheet=p.textureSheetAnimation;sheet.enabled=true;sheet.numTilesX=4;sheet.numTilesY=1;sheet.frameOverTime=1;
                    var velocity=p.velocityOverLifetime;velocity.enabled=false;
                    var renderer=p.GetComponent<ParticleSystemRenderer>();renderer.renderMode=ParticleSystemRenderMode.HorizontalBillboard;
                    p.Emit(1);Destroy(p.gameObject,1);
                }
            }
        }
        public static void Jump(Vector3 point)
        {
            var p = Create("Leaf", null, point + Vector3.up * .15f, 0, .30f, 1.2f, .7f, .3f);
            if (p) { p.Emit(10); Destroy(p.gameObject, 2); }
        }
        public static GameObject Boundary(Vector3 center, float radius)
        {
            var p = Create("Wind", null, center + Vector3.up * 1.25f, 24, 1.6f, 2.8f, .025f, radius);
            return p ? p.gameObject : null;
        }
    }
}
