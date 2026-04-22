from pathlib import Path

EXTS = {'.py', '.md', '.rst', '.toml', '.ipynb', '.in', '.txt', '.bat', '.yml', '.yaml', '.gitignore'}
SKIP_PARTS = (
    '/.git/',
    '/.venv/',
    '/docs/build/',
    '/__pycache__/',
    '/pyskindose.egg-info/',
    '/src/mypyskindose.egg-info/',
)

replacements = [
    ('mypyskindose', 'mypyskindose'),
    ('src/mypyskindose', 'src/mypyskindose'),
]

changed = 0
for path in Path('.').rglob('*'):
    if not path.is_file():
        continue

    path_posix = path.as_posix()
    if any(part in path_posix for part in SKIP_PARTS):
        continue

    if path.suffix.lower() not in EXTS and path.name != '.gitignore':
        continue

    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        continue

    new_text = text
    for old, new in replacements:
        new_text = new_text.replace(old, new)

    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        changed += 1

print(changed)
