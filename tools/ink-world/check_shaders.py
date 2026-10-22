"""Static ShaderLab contract checks. This does NOT compile or render Unity shaders."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SHADERS = ROOT / 'Sunward-Unity/Assets/Sunward/Shaders'
NAMES = ('Pigment', 'InkContour', 'BrushWater', 'GardenPond', 'PaintedSky')


def run():
    for name in NAMES:
        path = SHADERS / (name + '.shader')
        source = path.read_text()
        code = re.sub(r'//[^\n]*', '', source)
        code = re.sub(r'"[^"\n]*"', '""', code)
        for opening, closing in (('{', '}'), ('(', ')'), ('[', ']')):
            level = 0
            for char in code:
                level += (char == opening) - (char == closing)
                assert level >= 0, (name, 'unbalanced', opening)
            assert level == 0, (name, 'unbalanced', opening)
        assert source.count('HLSLPROGRAM') == source.count('ENDHLSL') == 1, name
        assert source.count('CBUFFER_START(UnityPerMaterial)') == source.count('CBUFFER_END') == 1, name
        assert 'RenderPipeline' in source and 'UniversalPipeline' in source, name
        assert '#pragma vertex Vert' in source and '#pragma fragment Frag' in source, name
        assert Path(str(path) + '.meta').is_file(), name
        assert len(re.search(r'guid: (\w+)', Path(str(path) + '.meta').read_text())[1]) == 32
    ink = (SHADERS / 'InkContour.shader').read_text()
    # Explicit renderer integration is intentional: never assume a second forward
    # pass on the same mesh will be drawn by URP's DrawObjectsPass.
    assert ink.count('Pass\n') == 1
    assert 'Cull Front ZWrite On ZTest LEqual' in ink
    assert 'min(_InkWorldMax,' in ink and 'TransformObjectToWorldNormal(v.normalOS)' in ink
    assert 'Queue"="Geometry-1' in ink
    assert 'ShadowCaster' not in ink
    water = (SHADERS / 'BrushWater.shader').read_text()
    assert 'min(16,(int)_RockCount)' in water
    assert 'pow((z' not in water  # Avoid pow on negative bases for Gaussian bends.
    assert 'SampleSceneDepth' in water and 'SampleSceneColor' in water
    urp = (ROOT / 'Sunward-Unity/Assets/Sunward/Generated/ValleyURP.asset').read_text()
    assert 'm_RequireDepthTexture: 1' in urp and 'm_RequireOpaqueTexture: 1' in urp
    print('PASS: five shader static contracts; Unity compilation/rendering NOT tested.')


if __name__ == '__main__':
    run()
