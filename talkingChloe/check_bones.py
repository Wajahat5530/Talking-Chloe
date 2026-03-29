import json, struct

path = r'myapp/static/models/chloe.glb'
with open(path, 'rb') as f:
    f.read(12)
    chunk_len = struct.unpack('<I', f.read(4))[0]
    f.read(4)
    data = json.loads(f.read(chunk_len))

nodes = data.get('nodes', [])
print('ALL RELEVANT BONES:')
for i, node in enumerate(nodes):
    name = node.get('name', '')
    lower = name.lower()
    if any(x in lower for x in ['jaw','chin','mouth','lip','teeth','tongue','head','neck','spine','chest']):
        print(f'  [{i}] {name}')

print('\nALL BONES (full list):')
for i, node in enumerate(nodes):
    print(f'  [{i}] {node.get("name", "unnamed")}')