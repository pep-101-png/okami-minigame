"""Small buffer helpers for editing the existing portable wolf GLB in place.

No re-export, model reconstruction, texture baking or animation resampling.
"""
import json
import struct
import numpy as np

DTYPES = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class GLB:
    def __init__(self, path):
        raw = path.read_bytes()
        assert struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw))
        length = struct.unpack_from('<I', raw, 12)[0]
        self.doc = json.loads(raw[20:20 + length])
        self.binary = bytearray(raw[28 + length:])

    def view(self, index, count, width, dtype, offset=0):
        v = self.doc['bufferViews'][index]
        dt = np.dtype(dtype)
        return np.ndarray((count, width), dtype=dt, buffer=self.binary,
                          offset=v.get('byteOffset', 0) + offset,
                          strides=(v.get('byteStride', width * dt.itemsize), dt.itemsize))

    def read(self, index):
        a = self.doc['accessors'][index]
        count, width, dtype = a['count'], WIDTHS[a['type']], DTYPES[a['componentType']]
        values = (self.view(a['bufferView'], count, width, dtype, a.get('byteOffset', 0)).copy()
                  if 'bufferView' in a else np.zeros((count, width), dtype=dtype))
        if 'sparse' in a:
            s = a['sparse']; i = s['indices']; v = s['values']
            ids = self.view(i['bufferView'], s['count'], 1, DTYPES[i['componentType']], i.get('byteOffset', 0)).ravel()
            values[ids] = self.view(v['bufferView'], s['count'], width, dtype, v.get('byteOffset', 0))
        return values

    def write(self, index, values):
        a = self.doc['accessors'][index]
        assert 'bufferView' in a and 'sparse' not in a
        self.view(a['bufferView'], a['count'], WIDTHS[a['type']], DTYPES[a['componentType']], a.get('byteOffset', 0))[:] = values
        if 'min' in a:
            a['min'] = values.min(axis=0).tolist()
            a['max'] = values.max(axis=0).tolist()

    def append_view(self, array):
        while len(self.binary) % 4:
            self.binary.append(0)
        index = len(self.doc['bufferViews'])
        self.doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(self.binary), 'byteLength': array.nbytes})
        self.binary.extend(array.tobytes())
        return index

    def write_sparse(self, index, values):
        a = self.doc['accessors'][index]; s = a['sparse']; i = s['indices']; v = s['values']
        ids = self.view(i['bufferView'], s['count'], 1, DTYPES[i['componentType']], i.get('byteOffset', 0)).ravel().copy()
        outside = np.ones(len(values), dtype=bool); outside[ids] = False
        if np.max(np.abs(values[outside]), initial=0) < 1e-6:
            self.view(v['bufferView'], s['count'], WIDTHS[a['type']], DTYPES[a['componentType']], v.get('byteOffset', 0))[:] = values[ids]
            return index
        ids = np.where(np.linalg.norm(values, axis=1) > 1e-6)[0]
        iv = self.append_view(ids.astype('<u4'))
        vv = self.append_view(values[ids].astype('<f4'))
        new = len(self.doc['accessors'])
        self.doc['accessors'].append({'componentType': 5126, 'count': len(values), 'type': a['type'],
                                     'sparse': {'count': len(ids), 'indices': {'bufferView': iv, 'componentType': 5125},
                                                'values': {'bufferView': vv}}})
        return new

    def save(self, path):
        while len(self.binary) % 4:
            self.binary.append(0)
        self.doc['buffers'][0]['byteLength'] = len(self.binary)
        encoded = json.dumps(self.doc, separators=(',', ':')).encode()
        while len(encoded) % 4:
            encoded += b' '
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(self.binary)) +
                         struct.pack('<II', len(encoded), 0x4e4f534a) + encoded +
                         struct.pack('<II', len(self.binary), 0x004e4942) + self.binary)


def to_gltf(p):
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


def to_native(p):
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], axis=-1)
