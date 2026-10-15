"""Keep the approved paint, move the shoulder spiral onto the body, and fit the face."""
text=(root.parent/'wolf-animation-viewer'/'authoring'/'paint.py').read_text().replace('if stage>=10:','if True:')
text=text.replace('(-1.05+r*math.cos(a),3.81+r*math.sin(a))','(-.25+r*math.cos(a),3.56+r*math.sin(a))')
text=text.replace("a=source.index('# Layered ivory coat:');b=source.index('# Swept layered mane',a);exec(source[a:b])", "a=source.index('# Layered ivory coat:');b=source.index('# Swept layered mane',a);shader=source[a:b].replace('(.43,.46,.46,1)','(.32,.37,.40,1)').replace('(.67,.68,.65,1)','(.58,.62,.61,1)').replace('default_value=.35','default_value=.43');exec(shader)")
text=text.replace('exec(paint_code)' ,"a=paint_code.index('# Calligraphic brow sweeps');b=paint_code.index('# Delicate ink fur strokes',a);paint_code=paint_code[:a]+paint_code[b:]\nexec(paint_code)")
text=text.replace('# Use the existing UV arrangement',"exec(compile((root/'authoring'/'face_material.py').read_text(),str(root/'authoring'/'face_material.py'),'exec'))\n# Use the existing UV arrangement")
text+='\nif coat.data.color_attributes.get(\'BodyInkOnly\'):coat.data.color_attributes.remove(coat.data.color_attributes[\'BodyInkOnly\'])\n'
exec(compile(text,'paint-body-and-face','exec'))
