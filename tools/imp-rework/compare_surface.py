exec(open('tools/imp-rework/inspect.py').read().split('for idx,role')[0])
for idx in range(5):
 n=nr.Native(r,f'Okami/em0{idx}',.7);n.visible=True;r.actors=[n];sheet=Image.new('RGB',(480*4,400),'white');d=ImageDraw.Draw(sheet)
 for col,mask in enumerate([{0,3},{0,1,3} if idx==2 else {0,2,3},{1,3},{0,3,4}]):
  n.groups=mask;n.update('em00_000',.3);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',36);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,0));d.text((col*480+5,5),str(mask),fill='black')
 sheet.save(W/f'surface-{idx}.jpg');n.visible=False
