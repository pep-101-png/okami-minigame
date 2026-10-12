import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
export function createPainterlyRenderer(renderer, scene, camera) {
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const pass = new ShaderPass({
    uniforms: {
      tDiffuse: { value: null },
      resolution: {
        value: new THREE.Vector2(
          innerWidth * renderer.getPixelRatio(),
          innerHeight * renderer.getPixelRatio(),
        ),
      },
    },
    vertexShader: `varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `
 uniform sampler2D tDiffuse; uniform vec2 resolution; varying vec2 vUv;
 float luma(vec3 c){return dot(c,vec3(.299,.587,.114));}
 float noise(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
 void main(){vec2 d=1./resolution;vec3 c=texture2D(tDiffuse,vUv).rgb;
 float l=luma(texture2D(tDiffuse,vUv-vec2(d.x,0.)).rgb),r=luma(texture2D(tDiffuse,vUv+vec2(d.x,0.)).rgb);
 float t=luma(texture2D(tDiffuse,vUv+vec2(0.,d.y)).rgb),b=luma(texture2D(tDiffuse,vUv-vec2(0.,d.y)).rgb);
 float edge=smoothstep(.10,.35,length(vec2(l-r,t-b)));
 c=mix(c,vec3(.10,.07,.04),edge*.5);c=pow(max(c,vec3(0.)),vec3(1./2.2));c+=vec3(noise(gl_FragCoord.xy)-.5)*.026;
 float vignette=smoothstep(.25,.85,distance(vUv,vec2(.5)));
 c*=1.-vignette*.15;gl_FragColor=vec4(c,1.);}`,
  });
  composer.addPass(pass);
  return {
    render: () => composer.render(),
    resize: (w, h) => {
      composer.setSize(w, h);
      pass.uniforms.resolution.value.set(
        w * renderer.getPixelRatio(),
        h * renderer.getPixelRatio(),
      );
    },
  };
}
