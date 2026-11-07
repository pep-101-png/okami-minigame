using UnityEngine;
namespace Sunward.Remaster
{
    // A swept explosive shell; the source muzzle and original paintings/sounds
    // are supplied by the Yellow Imp's inspected native rig/profile.
    public sealed class ImpCannonProjectile : MonoBehaviour
    {
        GameFlow game;ImpMotionProfile.Cannon data;ImpCannonPaint paint;
        Vector3 velocity;float damage,life;bool exploded;
        public Vector3 Velocity=>velocity;
        public static ImpCannonProjectile Spawn(GameFlow game,Vector3 muzzle,Vector3 target,float damage,ImpMotionProfile.Cannon data)
        {
            var go=new GameObject("Yellow Imp · native-painted cannon shell");go.transform.position=muzzle;
            var shell=go.AddComponent<ImpCannonProjectile>();shell.game=game;shell.data=data;shell.damage=damage;shell.life=3.2f;
            Vector3 horizontal=target-muzzle;horizontal.y=0;float flight=Mathf.Max(.15f,horizontal.magnitude/data.speed);
            shell.velocity=horizontal.normalized*data.speed+Vector3.up*((target.y-muzzle.y)/flight+.5f*data.gravity*flight);
            shell.paint=ImpCannonPaint.Spawn(game,go.transform,muzzle,0);shell.paint.Trail(shell.velocity);
            ImpCannonPaint.Spawn(game,null,muzzle,1);
            if(game.Audio)game.Audio.World(data.fireCue,muzzle,28,.85f,false,data.firePitch);
            return shell;
        }
        void Update()
        {
            if(exploded)return;
            if(!game || !game.InTrial){Destroy(gameObject);return;}
            if(game.Blocked)return;
            float dt=Time.deltaTime;Vector3 step=velocity*dt+Vector3.down*(.5f*data.gravity*dt*dt);
            if(step.sqrMagnitude>.000001f && Physics.SphereCast(transform.position,data.radius,step.normalized,out var hit,step.magnitude,(1<<6)|(1<<7),QueryTriggerInteraction.Ignore))
            {Detonate(hit.point+hit.normal*.04f);return;}
            transform.position+=step;velocity+=Vector3.down*(data.gravity*dt);if(paint)paint.Trail(velocity);
            life-=dt;if(life<=0)Detonate(transform.position);
        }
        void Detonate(Vector3 point)
        {
            if(exploded)return;exploded=true;
            ImpCannonPaint.Spawn(game,null,point,2);
            if(game.Audio)game.Audio.World(data.impactCue,point,28,.9f,false,data.impactPitch);
            Vector3 d=game.Player.transform.position-point;
            if(game.InTrial && d.magnitude<data.splash)game.Hurt(damage,d.normalized);
            Destroy(gameObject);
        }
    }
}
