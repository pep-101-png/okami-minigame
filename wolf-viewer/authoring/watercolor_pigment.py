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
    # Roughen only the red paint: the approved charcoal artwork stays in place.
    red_source=(rgba[:,:,0]>125)&(rgba[:,:,0]>rgba[:,:,1]*2.8)&(rgba[:,:,3]>0)
    isolated=rgba.copy();isolated[:,:,3]*=red_source
    yy,xx=np.indices((h,w),dtype=np.float32)
    sx=np.clip(np.rint(xx+(field(95)-.5)*w*.003),0,w-1).astype(np.int32)
    sy=np.clip(np.rint(yy+(field(145)-.5)*h*.004),0,h-1).astype(np.int32)
    warped=Image.fromarray(np.clip(isolated[sy,sx],0,255).astype('uint8'))
    rgba[:,:,3][red_source]=0
    base=Image.fromarray(rgba.astype('uint8'));base.alpha_composite(warped)
    rgba=np.asarray(base).astype(np.float32)
    del isolated,yy,xx,sx,sy
    pools = .58*field(35) + .27*field(110) + .15*field(330)
    grain = field(max(64,round(w*.70)))
    alpha = rgba[:,:,3]/255
    red = (rgba[:,:,0]>125)&(rgba[:,:,0]>rgba[:,:,1]*2.8)&(alpha>.01)
    dark = (rgba[:,:,0]<115)&(rgba[:,:,1]<115)&(alpha>.01)
    interior = np.asarray(Image.fromarray((alpha*255).astype('uint8')).filter(ImageFilter.MinFilter(7)),dtype=np.float32)/255
    edge = np.clip((alpha-interior)*2.5,0,1)
    # Darker pigment settles at the wet edge; broad washes vary within a stroke.
    for c, (base, spread, rim) in enumerate([(145,110,30),(7,30,10),(5,19,7)]):
        values = base + spread*pools - rim*edge + (grain-.5)*8
        rgba[:,:,c][red] = np.clip(values[red],0,255)
    density = .92+.08*np.clip((pools-.20)*1.65,0,1)
    fibres=rng.uniform(0,255,(max(2,h//12),max(2,w//2))).astype('uint8')
    fibres=np.asarray(Image.fromarray(fibres).resize((w,h),Image.Resampling.BICUBIC),dtype=np.float32)/255
    # Sparse bristle channels expose paper inside a dense stroke, rather than
    # merely sprinkling uniform noise over an otherwise perfect ribbon.
    # Keep wet cores dense; concentrate the broken bristles at the perimeter.
    # This avoids a repeated scratched/striped texture through every stroke.
    dry=1-(.08+.22*edge)*np.clip((fibres-.65)*3.3,0,1)-.07*np.clip((grain-.68)*5,0,1)
    rgba[:,:,3][red] *= (density*dry)[red]
    if black:
        for c, (base, spread) in enumerate([(40,60),(35,53),(29,43)]):
            values = base+spread*pools+(grain-.5)*9
            rgba[:,:,c][dark] = values[dark]
        rgba[:,:,3][dark] *= (.77+.21*pools)[dark]
    # A small wet fringe preserves the authored silhouette and pointed tips.
    result = Image.fromarray(np.clip(rgba,0,255).astype('uint8'))
    return Image.blend(result, result.filter(ImageFilter.GaussianBlur(1.2)), .35)
