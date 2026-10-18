import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
export function createPainterlyRenderer(renderer,scene,camera) {
  const composer=new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene,camera));
  const pass=new ShaderPass({uniforms:{tDiffuse:{value:null},resolution:{value:new THREE.Vector2(innerWidth*renderer.getPixelRatio(),innerHeight*renderer.getPixelRatio())}},
  vertexShader:`varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader:`uniform sampler2D tDiffuse;uniform vec2 resolution;varying vec2 vUv;
  float luma(vec3 c){return dot(c,vec3(.299,.587,.114));}
  float noise(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
  void main(){vec2 d=1./resolution;vec3 c=texture2D(tDiffuse,vUv).rgb;
  c*=1.+(noise(gl_FragCoord.xy)-.5)*.016;
  float vignette=smoothstep(.45,.95,distance(vUv,vec2(.5)));c*=1.-vignette*.045;gl_FragColor=vec4(max(c,vec3(0.)),1.);}`});
  composer.addPass(pass);composer.addPass(new OutputPass());
  return {render:()=>composer.render(),resize:(w,h)=>{composer.setSize(w,h);pass.uniforms.resolution.value.set(w*renderer.getPixelRatio(),h*renderer.getPixelRatio());}};
}
