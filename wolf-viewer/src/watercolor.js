import * as THREE from 'three';

// Object-space pigment stays attached to the surface as the skin animates.
export const pigmentGLSL = `
float swHash(vec3 p) { return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453); }
float swNoise(vec3 p) {
  vec3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
  return mix(mix(mix(swHash(i),swHash(i+vec3(1,0,0)),f.x),mix(swHash(i+vec3(0,1,0)),swHash(i+vec3(1,1,0)),f.x),f.y),
    mix(mix(swHash(i+vec3(0,0,1)),swHash(i+vec3(1,0,1)),f.x),mix(swHash(i+vec3(0,1,1)),swHash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float swFbm(vec3 p) { return .58*swNoise(p)+.28*swNoise(p*2.03+7.1)+.14*swNoise(p*4.17+19.3); }
`;

export function applyWatercolorMaterial(material, face) {
  material.roughness = 1;
  material.metalness = 0;
  material.onBeforeCompile = shader => {
    shader.vertexShader = `varying vec3 vPaintPosition;\n${shader.vertexShader}`
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n vPaintPosition=position;');
    shader.fragmentShader = `varying vec3 vPaintPosition;\n${pigmentGLSL}\n${shader.fragmentShader}`
      .replace('#include <color_fragment>', `#include <color_fragment>
        float granulation=swNoise(vPaintPosition*145.0);
        float pools=smoothstep(.25,.75,swFbm(vPaintPosition*3.2));
        float coat=smoothstep(.16,.55,min(diffuseColor.r,min(diffuseColor.g,diffuseColor.b)));
        float tide=1.0-smoothstep(.012,.065,abs(pools-.42));
        vec3 wash=mix(vec3(.84,.91,.96),vec3(1.07,1.035,.95),pools);
        wash *= (.94+.09*granulation)*(1.0-.045*tide);
        diffuseColor.rgb *= mix(vec3(1.0),wash,coat);
      `)
      .replace('#include <opaque_fragment>', `
        // Diffuse colour peeks through the lighting like a translucent wash.
        // Preserve form shadows while reducing the polished 3D-material look.
        outgoingLight=mix(outgoingLight,diffuseColor.rgb,.22);
        #include <opaque_fragment>
      `);
    face?.patch(shader);
  };
  material.customProgramCacheKey = () => face ? 'sunward-watercolor-face-1' : 'sunward-watercolor-1';
  material.needsUpdate = true;
}

/** A quiet paper backdrop; grain is fixed rather than animated screen noise. */
export function createPaperBackground() {
  const canvas=document.createElement('canvas');canvas.width=canvas.height=768;
  const context=canvas.getContext('2d'),pixels=context.createImageData(768,768);
  let state=1977;
  const random=()=>{state=(1664525*state+1013904223)>>>0;return state/4294967296;};
  for(let y=0;y<768;y++)for(let x=0;x<768;x++){
    const i=(y*768+x)*4,grain=(random()-.5)*7;
    const wash=2.2*Math.sin(x*.014+Math.sin(y*.011))+1.3*Math.sin(y*.031+x*.007);
    pixels.data[i]=235+grain+wash;pixels.data[i+1]=226+grain+wash;pixels.data[i+2]=204+grain+wash;pixels.data[i+3]=255;
  }
  context.putImageData(pixels,0,0);
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
  return texture;
}
