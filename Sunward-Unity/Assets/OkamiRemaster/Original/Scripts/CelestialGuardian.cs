using UnityEngine;
namespace Sunward.Remaster
{
    // Sunward encounter direction using recovered original attack postures.
    // Source clips remain intact; this driver owns tells, movement and contact.
    public sealed class CelestialGuardian:MonoBehaviour
    {
        EnemyBrain enemy;OriginalActor actor;GameFlow game;float remaining,duration,openUntil;int cycle;string state="approach",move="charge";Vector3 aim;bool struck;LineRenderer tell;
        public void Initialise(EnemyBrain brain,OriginalActor native)
        {enemy=brain;actor=native;game=brain.game;remaining=duration=1.2f;Set("approach",1.2f);}
        bool Eclipse=>enemy.definition.id=="guardian-eclipse";
        public float FilterDamage(float value)=>value*(Time.time<openUntil || state=="recover"?1:state=="windup"?.55f:.8f);
        public void BrushCounter()
        {
            if(!enemy || enemy.Dead || state!="windup" || remaining<.12f)return;
            openUntil=Time.time+3.2f;struck=true;Set("recover",2.6f);game.Audio.Cue("heavy-impact");
            game.Fx.Ring(transform.position+Vector3.up*.3f,new Color(1,.86f,.4f),4);game.Notify("The guardian's guard breaks");
        }
        void Set(string next,float length)
        {
            state=next;remaining=duration=length;enemy.CelestialState(state,move,duration,remaining);
            if(tell){Destroy(tell.gameObject);tell=null;}
        }
        void Update()
        {
            if(!enemy || enemy.Dead || !game || !game.InTrial || game.Blocked)return;
            float dt=Time.deltaTime;remaining-=dt;var delta=game.Player.transform.position-transform.position;delta.y=0;float distance=delta.magnitude;
            if(state=="approach")
            {
                if(delta.sqrMagnitude>.001f)transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(delta),dt*4);
                if(distance>(Eclipse?9:4.5f))Move(delta.normalized*dt*(Eclipse?4.3f:3.5f));
                if(remaining<=0 && distance<(Eclipse?13:7))
                {
                    move=new[]{"charge","slam","fan"}[cycle++%3];aim=delta.normalized;struck=false;
                    // The brush counter has a readable hold before the native attack.
                    Set("windup",Eclipse?1.1f:1.3f);
                    tell=game.Fx.Ring(move=="slam"?transform.position:game.Player.transform.position,new Color(.9f,.38f,.2f),move=="slam"?6:1.7f,duration+.1f);
                }
            }
            else if(state=="windup" && remaining<=0)
            {Set("strike",Mathf.Max(.38f,actor.ActivityLength(actor.AttackMotion(move))*.37f));game.Audio.World("attack",transform.position,22,.35f);}
            else if(state=="strike")
            {
                float progress=1-remaining/duration;
                if(move=="charge")
                {
                    Vector3 from=transform.position;Move(aim*dt*(Eclipse?15:12));Vector3 travel=transform.position-from;
                    float t=travel.sqrMagnitude<.0001f?0:Mathf.Clamp01(Vector3.Dot(game.Player.transform.position-from,travel)/travel.sqrMagnitude);
                    if(!struck && Vector3.Distance(from+travel*t,game.Player.transform.position)<2.5f){struck=true;game.Hurt(enemy.AttackDamage,aim);game.Audio.World("heavy-impact",transform.position,24,.4f);}
                }
                else if(!struck && progress>=.38f)
                {
                    struck=true;
                    if(move=="slam")
                    {
                        SolarPaint.Create(game,transform.position,2);game.Audio.World("heavy-impact",transform.position,28,.6f);var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.Shake(.12f,.3f);
                        if(distance<6 && game.Player.transform.position.y<transform.position.y+1.2f)game.Hurt(enemy.AttackDamage*1.15f,delta.normalized);
                    }
                    else
                    {
                        Vector3 at=transform.position+Vector3.up*1.3f;var toward=(game.Player.transform.position+Vector3.up*.6f-at).normalized;int n=Eclipse?7:3;
                        for(int i=0;i<n;i++)game.Projectile(at,Quaternion.Euler(0,(i-(n-1)*.5f)*13,0)*toward,enemy.AttackDamage*.7f,Eclipse);
                        game.Audio.World("heavy-impact",at,24,.28f);
                    }
                }
                if(remaining<=0){openUntil=Time.time+1.8f;Set("recover",1.8f);}
            }
            else if(state=="recover" && remaining<=0)Set("approach",enemy.Hp<enemy.MaxHp*.5f?.6f:1.1f);
            enemy.CelestialState(state,move,duration,remaining);
        }
        void Move(Vector3 step)
        {
            var centre=game.Celestial.ArenaCentre;var next=transform.position+step;var d=next-centre;d.y=0;if(d.magnitude>21)next=centre+d.normalized*21;next.y=centre.y+.03f;enemy.CelestialMove(next-transform.position);
        }
        void OnDisable(){if(tell)Destroy(tell.gameObject);}
    }
}
