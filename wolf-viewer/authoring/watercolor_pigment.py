"""Stable pigment pooling, granulation and soft edges for authored paint masks."""
from PIL import Image, ImageFilter
import numpy as np

def watercolor_pigment(image, seed=317, black=True):
    rgba = np.asarray(image).astype(np.float32)
    h, w = rgba.shape[:2]
    rng = np.random.default_rng(seed)
    def field(size):
        values = rng.uniform(0,255,(max(2,round(h/w*size)),size)).astype('uint8')
        return np.asarray(Image.fromarray(values).resize((w,h),Image.Resampling.BICUBIC),dtype=np.float32)/255
    pools = .58*field(35) + .27*field(110) + .15*field(330)
    grain = field(max(64,round(w*.70)))
    alpha = rgba[:,:,3]/255
    red = (rgba[:,:,0]>125)&(rgba[:,:,0]>rgba[:,:,1]*2.8)&(alpha>.01)
    dark = (rgba[:,:,0]<115)&(rgba[:,:,1]<115)&(alpha>.01)
    interior = np.asarray(Image.fromarray((alpha*255).astype('uint8')).filter(ImageFilter.MinFilter(7)),dtype=np.float32)/255
    edge = np.clip((alpha-interior)*2.5,0,1)
    # Darker pigment settles at the wet edge; broad washes vary within a stroke.
    for c, (base, spread, rim) in enumerate([(140,90,22),(13,25,10),(9,18,6)]):
        values = base + spread*pools - rim*edge + (grain-.5)*8
        rgba[:,:,c][red] = np.clip(values[red],0,255)
    density = .90+.09*pools
    dry = 1-.18*np.clip((grain-.68)*5,0,1)
    rgba[:,:,3][red] *= (density*dry)[red]
    if black:
        for c, (base, spread) in enumerate([(40,60),(35,53),(29,43)]):
            values = base+spread*pools+(grain-.5)*9
            rgba[:,:,c][dark] = values[dark]
        rgba[:,:,3][dark] *= (.77+.21*pools)[dark]
    # A small wet fringe preserves the authored silhouette and pointed tips.
    result = Image.fromarray(np.clip(rgba,0,255).astype('uint8'))
    return Image.blend(result, result.filter(ImageFilter.GaussianBlur(.65)), .42)
