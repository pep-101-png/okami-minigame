exec(open('tools/imp-rework/inspect.py').read().split('for idx,role')[0])
roles=['wisp','reed','ranged','heavy','elite']
for idx,role in enumerate(roles):
 text=(R/f'Sunward-Unity/Assets/Sunward/Generated/Enemy-{role}.prefab').read_text();scale=float(re.search('  modelScale: (.*)',text)[1]);off=[float(x) for x in re.search(r'  modelOffset: \{x: (.*), y: (.*), z: (.*)\}',text).groups()];n=nr.Native(r,f'Okami/em0{idx}',scale,off);n.visible=True;r.actors=[n];n.groups={1,2,3,6} if idx==2 else {1,2,3};clips=['em00_000','em00_010',re.search('  strike: (.*)',text)[1],'em00_032'];sheet=Image.new('RGB',(480*6,400*len(clips)),'white');d=ImageDraw.Draw(sheet)
 for row,clip in enumerate(clips):
  for col,phase in enumerate([0,.18,.36,.54,.72,.94]):
   n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+5,row*400+5),f'{clip} {phase}',fill='black')
 sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/f'{role}-full.jpg');n.visible=False
print('full articulated bodies rendered')
