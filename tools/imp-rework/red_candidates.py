exec(open('tools/imp-rework/inspect.py').read().split('for idx,role')[0])
n=nr.Native(r,'Okami/em01',.9,[0,.18,0]);n.bank=nr.pose_bank(W/'em01-all.bytes');n.groups={1,2,3};n.visible=True;r.actors=[n];clips=['em00_'+s for s in ['180','181','182','183','184','185','186','187','188','189','18a','18b','1b0','1b1','1b2','1b3','1b4','1b5','1b6','1b7','1b8']]
for start in range(0,len(clips),7):
 selected=clips[start:start+7];sheet=Image.new('RGB',(480*6,400*len(selected)),'white');d=ImageDraw.Draw(sheet)
 for row,clip in enumerate(selected):
  for col,phase in enumerate([0,.18,.36,.54,.72,.999]):
   n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,1.25,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+5,row*400+5),f'{clip} {phase}',fill='black')
 sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/f'red-options-{start}.jpg')
