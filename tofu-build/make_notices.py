"""Write THIRD-PARTY-NOTICES.txt for the packages inside Inpaint-web's built JavaScript bundle.

Usage: python3 -I make_notices.py <repo> <sourcemap-build-dir> <out-file> <heroicons-licence> <opencv-copyright>

The package list is read from the bundle's source map, so it names exactly the packages the site ships.
Added for the Tofu gallery; not part of upstream Inpaint-web.
"""
import glob
import json
import os
import sys

repo, mapdir, out, heroicons_licence, opencv_copyright = sys.argv[1:6]
m = json.load(open(glob.glob(os.path.join(mapdir, 'assets', 'index-*.js.map'))[0], encoding='utf-8'))
pkgs = set()
for s in m['sources']:
    i = s.rfind('node_modules/')
    if i < 0:
        continue
    rest = s[i + 13:].split('/')
    pkgs.add(rest[0] + '/' + rest[1] if rest[0].startswith('@') else rest[0])
lines = [
    'Third-party software in this build of Inpaint-web',
    '=================================================',
    '',
    'The JavaScript bundle in assets/ contains the packages below, as resolved by package-lock.json.',
    'Each is listed with its version, its licence and the licence text its package ships.',
    '',
]
for name in sorted(pkgs):
    d = os.path.join(repo, 'node_modules', name)
    meta = json.load(open(os.path.join(d, 'package.json'), encoding='utf-8'))
    lic = meta.get('license') or meta.get('licenses')
    text_path = next((os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().startswith(('license', 'licence', 'copying'))), None)
    note = ''
    if name == '@heroicons/react':
        lic = lic or 'MIT'
        text_path = heroicons_licence
        note = 'The npm package ships no licence file; the text below is LICENSE from tailwindlabs/heroicons at tag v1.0.4.'
    if name == 'opencv-ts':
        note = ('package.json says MIT and the LICENSE file it ships is the Apache License 2.0 (below). It bundles '
                'OpenCV.js 4.5.5 (src/opencv.js), part of OpenCV, licensed under the Apache License 2.0 '
                '(https://github.com/opencv/opencv/blob/4.5.5/LICENSE). OpenCV 4.5.5 COPYRIGHT file:\n\n'
                + open(opencv_copyright, encoding='utf-8').read().rstrip())
    lines += ['-' * 78, f'{name} {meta.get("version")}  ({lic})', meta.get('homepage') or '']
    if note:
        lines += [note]
    lines += ['']
    lines += [open(text_path, encoding='utf-8').read().rstrip() if text_path else '(no licence file shipped)', '']
open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('wrote', out, 'packages:', ', '.join(sorted(pkgs)))
