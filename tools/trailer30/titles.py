"""Title cards use the project's original lettering, logo and brush paint."""
from native_renderer import *
from PIL import ImageDraw,ImageChops
class Titles:
 def __init__(self,r,out):
  self.r=r;self.out=out;self.atlas=Image.open(D/'UI/MessageGlyphs.png').convert('RGBA');self.glyphs={g['code']:g for g in json.loads((D/'UI/MessageGlyphs.json').read_text())['glyphs']};self.cards={}
  for name in ['intro','outro']:
   im=Image.new('RGBA',(1920,1080));logo=Image.open(D/'UI/TitleLogo.png').convert('RGBA');logo.thumbnail((235,210));im.alpha_composite(logo,((1920-logo.width)//2,180));self.text(im,'SUNWARD',960,425,100,(1,.96,.84,1));self.text(im,'Windflower Village',960,550,36,(1,.96,.84,1));self.cards[name]=self.card(name,im)
  captions={'village':'A village worth protecting','farm':'Gather. Grow. Restore.','race':'Chase the spirit lights','tundra':'TUNDRA BEADS','instrument':'WIELD THE STORM','heaven':'Above the clouds','shiranui':'AWAKEN SHIRANUI'}
  for name,text in captions.items():
   im=Image.new('RGBA',(1920,1080));self.text(im,text,960,951,35,(1,.96,.85,1));self.cards[name]=self.card(name,im)
  im=Image.new('RGBA',(1920,1080));draw=ImageDraw.Draw(im);draw.rectangle((0,0,1920,37),fill=(0,0,0,240));draw.rectangle((0,1043,1920,1080),fill=(0,0,0,240));self.text(im,'OKAMI FAN PROJECT   ·   CINEMATIC TRAILER',960,1050,18,(.92,.9,.85,1));self.footer=self.card('footer',im)
 def text(self,image,s,cx,y,em,color):
  def adv(c):return (65 if c==' ' else self.glyphs[ord(c)]['advance'])*em/160
  for c in s:
   if c!=' ':assert ord(c) in self.glyphs,repr(c)
  width=sum(adv(c) for c in s);x=cx-width/2
  for c in s:
   if c!=' ':
    g=self.glyphs[ord(c)];glyph=self.atlas.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height'])).resize((max(1,round(g['width']*em/160)),max(1,round(g['height']*em/160))));py=round(y+g['top']*em/160);shadow=ImageChops.multiply(glyph,Image.new('RGBA',glyph.size,(0,0,0,235)));image.alpha_composite(shadow,(round(x)+2,py+3));paint=ImageChops.multiply(glyph,Image.new('RGBA',glyph.size,tuple(round(v*255) for v in color)));image.alpha_composite(paint,(round(x),py))
   x+=adv(c)
 def card(self,name,im):
  p=self.out/(name+'-title.png');im.save(p);return Draw(self.r,[[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]],[[0,1,2],[0,2,3]],[[0,0],[1,0],[1,1],[0,1]],np.ones((4,4)),p,mode=5,twosided=True)
 def draw(self,t,shot,start,end):
  self.r.overlay(self.footer)
  if shot in self.cards:
   age=t-start;tail=end-t;alpha=min(1,max(0,age-.18)/.25,max(0,tail-.08)/.22);self.r.overlay(self.cards[shot],alpha)
