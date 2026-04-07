import os, sys

base = os.path.dirname(__file__)
mcp_dir = os.path.join(base, '..', 'autoroutine_mcp')

for root, dirs, files in os.walk(mcp_dir):
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content.replace(
            'from mcp.tools.', 'from autoroutine_mcp.tools.'
        )
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'  Updated: {fname}')
        else:
            print(f'  No change: {fname}')

print('Done.')
