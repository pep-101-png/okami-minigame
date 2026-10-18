import * as THREE from 'three';
// Pigment is attached to surfaces, never to screen coordinates or camera position.
export const paintingTime={value:0};
const noise=`
float phash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float pnoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(phash(i),phash(i+vec2(1.,0.)),f.x),mix(phash(i+vec2(0.,1.)),phash(i+1.),f.x),f.y);}
`;
export function pigment(material,kind='wash') {
 material.userData.paintKind=kind;
 material.customProgramCacheKey=()=>`sumi-e-4:${kind}`;
 material.onBeforeCompile=shader=>{
  shader.uniforms.paintingTime=paintingTime;
  shader.vertexShader=shader.vertexShader.replace('#include <common>',`#include <common>\nvarying vec3 vPigment; varying vec2 vPaintUv; uniform float paintingTime;\n${noise}`);
  let deformation='vPigment=position;vPaintUv=uv;';
  if(kind==='ink')deformation+='transformed+=normal*(.005+.015*pnoise(position.xy*9.))*sin(position.x*14.+position.y*9.);';
  if(kind==='leaves'||kind==='grass-blade')deformation+='vec4 windLocal=vec4(position,1.);\n#ifdef USE_INSTANCING\nwindLocal=instanceMatrix*windLocal;\n#endif\nvec3 windPoint=(modelMatrix*windLocal).xyz; transformed.x+=sin(paintingTime*1.3+windPoint.x*.7+windPoint.z*.45)*.09*uv.y; transformed.z+=sin(paintingTime*.9+windPoint.z*.5)*.035*uv.y;';
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n'+deformation);
  shader.fragmentShader=shader.fragmentShader.replace('#include <common>',`#include <common>\nvarying vec3 vPigment; varying vec2 vPaintUv;\n${noise}`);
  const brush=`float wash=pnoise(vPigment.xz*.61+vPigment.y*.45);float dry=pnoise(vec2(vPigment.x*19.+vPigment.y*2.,vPigment.y*1.5+vPigment.z*2.));\n`;
  if(kind==='ink')shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>\n${brush}diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.29,.27,.25),wash*.40+dry*.16); diffuseColor.a*=.70+dry*.26;`);
  else shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>\n${brush}diffuseColor.rgb*=.88+wash*.23;diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.97,.95,.89),smoothstep(.64,.88,dry)*.14);vec2 paintUV=fract(vPaintUv);float edgePool=1.-smoothstep(0.,.10,min(min(paintUV.x,1.-paintUV.x),min(paintUV.y,1.-paintUV.y)));diffuseColor.rgb*=1.-edgePool*${kind==='landscape'||kind==='leaves'||kind==='grass-blade'?'0.0':'.10'}*(.5+wash);`);
  if(material.isMeshToonMaterial)shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>\nfloat pool=pow(1.-abs(dot(normalize(vViewPosition),normal)),3.);diffuseColor.rgb*=1.-pool*(.07+.08*wash);`);
 };
 return material;
}
export function restorePigments(scene){scene.traverse(o=>{for(const m of Array.isArray(o.material)?o.material:[o.material])if(m?.userData.paintKind)pigment(m,m.userData.paintKind);});}
export function random(seed=19){return()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};}
const cache=new Map();
export function brushTexture(kind='wash'){
 if(cache.has(kind))return cache.get(kind);
 const c=document.createElement('canvas');c.width=c.height=512;const x=c.getContext('2d'),r=random(711+kind.length*131);
 x.fillStyle='#fffcf6';x.fillRect(0,0,512,512);
 // Long broken strokes, translucent overlapped washes and dark tide lines.
 for(let i=0;i<180;i++){
  const px=r()*600-45,py=r()*560-25,w=25+r()*150,h=3+r()*27;
  x.save();x.translate(px,py);x.rotate(kind==='wood'?0:kind==='roof'?Math.PI/2:(r()-.5)*.65);
  x.fillStyle=`rgba(72,87,82,${.015+r()*.035})`;x.strokeStyle='rgba(68,76,70,.045)';x.lineWidth=.8;x.beginPath();x.moveTo(-w*.5,0);x.bezierCurveTo(-w*.4,-h,w*.33,-h*.7,w*.5,0);x.bezierCurveTo(w*.3,h*.7,-w*.3,h,-w*.5,0);x.fill();if(i%3===0)x.stroke();x.restore();
 }
 if(kind==='wood')for(let i=0;i<38;i++){const y=i*14;x.strokeStyle=i%5?'rgba(70,57,48,.16)':'rgba(63,49,40,.30)';x.lineWidth=.6+r()*1.5;x.beginPath();x.moveTo(0,y);for(let t=0;t<=512;t+=16)x.lineTo(t,y+Math.sin(t*.024+i)*2.3);x.stroke();}
 if(kind==='roof')for(let i=0;i<11;i++)for(let j=0;j<10;j++){const px=i*52+(j%2)*26,py=j*53;x.strokeStyle='rgba(45,57,63,.20)';x.lineWidth=2;x.beginPath();x.ellipse(px,py,24,12,0,0,Math.PI);x.stroke();x.fillStyle='rgba(255,255,255,.32)';x.fillRect(px-19,py+2,35,1.4);}
 for(let i=0;i<19000;i++){x.fillStyle=i%3?'rgba(64,62,56,.035)':'rgba(255,255,255,.24)';x.fillRect(r()*512,r()*512,r()*2+.5,.4+r());}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;cache.set(kind,t);return t;
}
let bedTexture;
export function gardenWash(){
 if(bedTexture)return bedTexture;
 const c=document.createElement('canvas');c.width=256;c.height=192;const x=c.getContext('2d'),r=random(715);
 for(let i=0;i<160;i++){let a=r()*Math.PI*2,rr=Math.sqrt(r()),px=128+Math.cos(a)*rr*100,py=96+Math.sin(a)*rr*63;x.fillStyle=i%3?'#6d927c16':'#9cae811d';x.beginPath();x.ellipse(px,py,8+r()*20,3+r()*11,r(),0,7);x.fill();}
 bedTexture=new THREE.CanvasTexture(c);bedTexture.colorSpace=THREE.SRGBColorSpace;return bedTexture;
}
