import * as THREE from 'three';

/** Gentle eyelid compression on the painted skin, with no floating eye meshes. */
export function createFaceDynamics(metadata) {
  const convert=p=>new THREE.Vector3(p[0],p[2],-p[1]);
  const points=[],tangents=[],depthAxes=[];
  for(const eye of metadata.eyes){
    const n=new THREE.Vector3(eye.surface_normal[0],eye.surface_normal[1],0).normalize();
    const tangent=new THREE.Vector3(0,0,1).cross(n).multiplyScalar(eye.side);
    points.push(convert(eye.point));tangents.push(convert(tangent.toArray()));depthAxes.push(convert(n.toArray()));
  }
  const blink=new THREE.Vector2();let time=0;
  const moments=[2.3,7.3,7.72,13.5,19.2];
  function lid(t){
    if(t<0||t>.25)return 0;
    if(t<.075)return THREE.MathUtils.smoothstep(t,0,.075);
    return 1-THREE.MathUtils.smoothstep(t,.10,.25);
  }
  return {
    step(dt){time+=dt;const t=time%24;blink.set(Math.max(...moments.map(m=>lid(t-m))),Math.max(...moments.map(m=>lid(t-m-.008))));},
    reset(){time=0;blink.set(0,0);},
    setBlink(value){blink.set(value,value);},
    get blink(){return blink.toArray();},
    patch(shader){
      Object.assign(shader.uniforms,{swBlink:{value:blink},swEyePoint:{value:points},swEyeTangent:{value:tangents},swEyeDepth:{value:depthAxes}});
      shader.vertexShader=`uniform vec2 swBlink;\nuniform vec3 swEyePoint[2];\nuniform vec3 swEyeTangent[2];\nuniform vec3 swEyeDepth[2];\n${shader.vertexShader}`
        .replace('#include <begin_vertex>',`#include <begin_vertex>
          for(int eye=0;eye<2;eye++){
            vec3 offset=position-swEyePoint[eye];
            float u=dot(offset,swEyeTangent[eye]);
            float v=offset.y-.25*u-.014;
            float across=smoothstep(-.18,-.12,u)*(1.0-smoothstep(.14,.20,u));
            float around=1.0-smoothstep(.045,.11,abs(v));
            float surface=1.0-smoothstep(.12,.18,abs(dot(offset,swEyeDepth[eye])));
            transformed.y-=v*.94*swBlink[eye]*across*around*surface;
          }
        `);
    }
  };
}
