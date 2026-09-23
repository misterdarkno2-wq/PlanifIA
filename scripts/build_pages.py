"""Prepara únicamente el frontend público para GitHub Pages."""
import json
import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent

def build():
    origin = os.environ['PLANIFIA_API_URL'].strip().rstrip('/')
    url = urlsplit(origin)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError('PLANIFIA_API_URL debe ser el origen HTTPS, sin /app ni credenciales.')
    output = ROOT / 'dist' / 'pages'
    output.mkdir(parents=True, exist_ok=True)
    # Lista explícita para evitar publicar archivos del servidor o de desarrollo.
    for directory in ('assets', 'css', 'js'):
        shutil.copytree(ROOT / 'frontend' / directory, output / directory, dirs_exist_ok=True)
    shutil.copyfile(ROOT / 'frontend' / 'favicon.svg', output / 'favicon.svg')
    policy = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src https:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'none'"
    for source in (ROOT / 'frontend').glob('*.html'):
        html = source.read_text(encoding='utf-8').replace('<head>', f'<head><meta http-equiv="Content-Security-Policy" content="{policy}"><meta name="referrer" content="same-origin">', 1)
        (output / source.name).write_text(html, encoding='utf-8')
    (output / 'js' / 'deployment.js').write_text(f'export const apiOrigin={json.dumps(origin)};\n', encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Frontend preparado en {output}')

if __name__ == '__main__':
    build()
