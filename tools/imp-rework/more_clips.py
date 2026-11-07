exec(open('tools/imp-rework/inspect.py').read().split('for idx,role')[0])
n=nr.Native(r,'Okami/em00',.861,[-.008,.071,-.275]);n.visible=True;n.bank=nr.pose_bank(W/'em00-all.bytes');r.actors=[n]
clips=['em00_'+s for s in ['001','002','005','014','015','022','023','024','025','033','039','03a','03b','03c','03d','03e','060','061','062','063','064','065','066','084','083','085','087','088','08a','090','091','092','093','094','095','096','097']]
for start in range(0,len(clips),10):
 selected=clips[start:start+10];sheet=Image.new('RGB',(480*6,400*len(selected)),'white');d=ImageDraw.Draw(sheet)
 for row,clip in enumerate(selected):
  for col,phase in enumerate([0,.18,.36,.54,.72,.94]):
   n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+5,row*400+5),f'{clip} {phase}',fill='black')
 sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/f'extra-{start}.jpg')
print('additional native motions rendered')
