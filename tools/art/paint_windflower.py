"""Author Sunward's seamless painted surfaces. Python + Pillow + NumPy; no downloads.
Run from any directory. Stable seeds preserve reviewable, reproducible artwork.
Height paintings produce matching relief and packed URP metal/AO/smoothness maps.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parents[2] / 'Sunward-Unity/Assets/Sunward/Textures'
N = 1024
rng = np.random.default_rng(41021)
y, x = np.mgrid[:N, :N] / N

def wash(seed):
    r = np.random.default_rng(seed)
    out = np.zeros((N,N))
    # Periodic washes, with long gestural marks rather than isotropic speckle.
    for frequency, weight in [(2,.45),(5,.23),(13,.13),(37,.07),(91,.025)]:
        for _ in range(4):
            a,b = r.integers(-frequency,frequency+1,2)
            out += np.sin(2*np.pi*(a*x+b*y)+r.uniform(0,6.28))*weight/4
    return out

def wrapped_line(draw, points, fill, width):
    for ox in [-N,0,N]:
        for oy in [-N,0,N]:
            draw.line([(a+ox,b+oy) for a,b in points],fill=fill,width=width,joint='curve')

def paint(name, base, seed):
    w=wash(seed); col=np.clip(np.array(base)[None,None,:]+w[:,:,None]*30,0,255).astype('uint8')
    im=Image.fromarray(col); d=ImageDraw.Draw(im)
    h=Image.fromarray(np.clip(128+w*30,0,255).astype('uint8')); hd=ImageDraw.Draw(h)
    r=np.random.default_rng(seed)
    if name in ('Cedar','Endgrain'):
        if name=='Cedar':
            for i in range(150):
                xx=i*N/150; phase=r.uniform(0,6.28)
                points=[(xx+7*math.sin(j*math.tau/N+phase)+3*math.sin(j*math.tau*3/N+phase),j) for j in range(-16,N+17,8)]
                shade=int(r.integers(-30,32)); color=tuple(int(np.clip(c+shade,0,255)) for c in base)
                wrapped_line(d,points,color,int(r.integers(1,5)));wrapped_line(hd,points,110+shade,2)
            for cx,cy in [(270,350),(755,810)]:
                for radius in range(10,85,7):
                    pts=[(cx+radius*math.cos(t),cy+radius*1.8*math.sin(t)) for t in np.linspace(0,math.tau,80)]
                    wrapped_line(d,pts,(91,53,36),2);wrapped_line(hd,pts,105,2)
        else:
            radial=np.sqrt(((x-.48)*1.02)**2+((y-.51)*.96)**2)
            rings=np.sin(radial*390+wash(seed+2)*2)
            arr=np.clip(col.astype(float)+rings[:,:,None]*14,0,255).astype('uint8')
            im=Image.fromarray(arr);d=ImageDraw.Draw(im)
            h=Image.fromarray(np.uint8(128+rings*12));hd=ImageDraw.Draw(h)
    elif name=='Granite':
        # Natural granite: long ink seams and mineral planes, never brick courses.
        for i in range(120):
            a,b=r.integers(0,N,2);length=int(r.integers(35,330));tone=int(r.integers(-16,17))
            points=[(a,b),(a+length*.3,b-length*.12),(a+length*.65,b+length*.04),(a+length,b-length*.11)]
            wrapped_line(d,points,tuple(int(np.clip(v+tone,0,255)) for v in base),int(r.integers(2,12)))
            wrapped_line(hd,points,128+tone,3)
        for i in range(12):
            a,b=r.integers(0,N,2)
            points=[(a,b),(a+38,b+55),(a+23,b+96),(a+50,b+145)]
            wrapped_line(d,points,(84,105,108),2);wrapped_line(hd,points,100,2)
    elif name in ('Slate','Earth'):
        # Broad irregular stone courses and fired kawara tiles with painted lips.
        rows,cols=(5,5) if name=='Slate' else (4,4) if name=='Granite' else (7,7)
        cw=N/cols;rh=N/rows
        for row in range(-1,rows+1):
            for c in range(-1,cols+1):
                left=c*cw+(row%2)*cw*.5;top=row*rh
                jitter=6 if name=='Slate' else 17
                pts=[(left+8,top+8),(left+cw-8,top+12),(left+cw-5,top+rh-10),(left+12,top+rh-4)]
                pts=[(a+r.uniform(-jitter,jitter),b+r.uniform(-jitter,jitter)) for a,b in pts]
                tint=int(r.integers(-18,20));fill=tuple(int(np.clip(v+tint,0,255)) for v in base)
                for ox in [-N,0,N]:
                    for oy in [-N,0,N]:
                        p=[(a+ox,b+oy) for a,b in pts];d.polygon(p,fill=fill);hd.polygon(p,fill=160+tint)
                        d.line(p+[p[0]],fill=tuple(max(0,v-35) for v in base),width=3)
                        d.line([p[0],p[1]],fill=tuple(min(255,v+42) for v in fill),width=4)
                if name=='Slate':
                    for k in range(4):
                        yy=top+rh-24-k*7;points=[(left+12,yy),(left+cw*.5,yy+5),(left+cw-12,yy)]
                        wrapped_line(d,points,tuple(min(255,v+18-k*3) for v in fill),2)
                elif name=='Granite':
                    points=[(left+cw*.3,top+15),(left+cw*.45,top+rh*.4),(left+cw*.35,top+rh*.68)]
                    wrapped_line(d,points,tuple(max(0,v-33) for v in fill),2)
        if name=='Earth':
            # Earth is a warm beaten path, its stones remain partially submerged.
            im=Image.blend(im,Image.fromarray(col),.58);d=ImageDraw.Draw(im)
    elif name=='Meadow':
        for i in range(11500):
            a,b=r.integers(0,N,2); length=int(r.integers(3,18));lean=int(r.integers(-7,8))
            color=[(92,130,65),(125,151,75),(161,169,86),(60,104,66)][int(r.integers(0,4))]
            wrapped_line(d,[(a,b),(a+lean,b-length)],color,int(r.integers(1,4)))
            wrapped_line(hd,[(a,b),(a+lean,b-length)],155,2)
        for i in range(75):
            a,b=r.integers(0,N,2);d.ellipse((a-2,b-2,a+2,b+2),fill=(209,191,115))
    elif name=='Plaster':
        for i in range(1600):
            a,b=r.integers(0,N,2);length=int(r.integers(8,75));v=int(r.integers(-14,15))
            wrapped_line(d,[(a,b),(a+length,b+2)],tuple(int(np.clip(c+v,0,255)) for c in base),1)
    # Reintroduce translucent paper fibres and pigment pooling over the brushwork.
    arr=np.asarray(im).astype(float);fibres=wash(seed+90)
    arr=np.clip(arr+fibres[:,:,None]*11,0,255).astype('uint8')
    height=np.asarray(h.filter(ImageFilter.GaussianBlur(1.2))).astype(float)/255
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*2.2
    dy=(np.roll(height,-1,0)-np.roll(height,1,0))*2.2
    normal=np.stack([-dx,-dy,np.ones_like(dx)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    normal=np.uint8(np.clip((normal*.5+.5)*255,0,255))
    mask=np.zeros((N,N,4),dtype='uint8');mask[:,:,1]=np.uint8(np.clip(225+height*25,0,255));mask[:,:,2]=255;mask[:,:,3]=35 if name in ('Meadow','Earth','Plaster') else 65
    return Image.fromarray(arr),Image.fromarray(normal),Image.fromarray(mask)

def main():
    palette={'Cedar':(162,105,60),'Endgrain':(183,139,83),'Granite':(128,145,143),'Slate':(64,106,114),'Earth':(168,142,94),'Meadow':(105,136,67),'Plaster':(230,214,170)}
    family={'Cedar':'wood','Granite':'stone','Slate':'roof','Earth':'path','Meadow':'meadow','Plaster':'plaster'}
    swatches=[]
    for i,(name,base) in enumerate(palette.items()):
        color,normal,mask=paint(name,base,100+i)
        for channel,image in [('Color',color),('Normal',normal),('Mask',mask)]:image.save(ROOT/'SurfaceDetail'/f'{name}-{channel}.png',optimize=True)
        if name in family:
            color.save(ROOT/'Art'/f'Paint-{family[name]}.png',optimize=True)
            normal.save(ROOT/'Art'/f'Paint-{family[name]}-normal.png',optimize=True)
        tile=color.resize((300,300));ImageDraw.Draw(tile).text((10,10),name,fill='white');swatches.append(tile)
    sheet=Image.new('RGB',(1200,600),(30,34,40))
    for i,tile in enumerate(swatches):sheet.paste(tile,((i%4)*300,(i//4)*300))
    sheet.save('/tmp/sunward-painted-surfaces.jpg')
if __name__=='__main__':main()
