exec(open('tools/imp-rework/inspect.py').read().split('for idx,role')[0])
n=nr.Native(r,'Okami/em02',.822,[-.041,-.18,-.389]);n.bank=nr.pose_bank(W/'em02-all.bytes');n.groups={1,2,3,6};n.visible=True;r.actors=[n];clips=['em00_150','em00_151','em00_152','em00_153','em00_154','em00_155','em00_156','em00_158','em00_159'];sheet=Image.new('RGB',(480*6,400*len(clips)),'white');d=ImageDraw.Draw(sheet)
for row,clip in enumerate(clips):
 for col,phase in enumerate([0,.18,.36,.54,.72,.999]):
  n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+5,row*400+5),f'{clip} {phase}',fill='black')
sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/'ranged-transitions.jpg')
