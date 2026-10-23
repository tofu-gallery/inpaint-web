# Inpaint-web in the Tofu gallery

Inpaint-web removes unwanted things from photos and enlarges photos, entirely in the browser. A person opens an
image (or one of the demo pictures), paints over what should go, and an AI model (MI-GAN) fills the area in; the
"4x upscaling" button (4 倍放大) enlarges the picture four times with a second model (Real-ESRGAN). Both models run on
the visitor's own device with ONNX Runtime Web: on the graphics card through WebGPU where the browser has it, and on
WebAssembly otherwise. Photos are never uploaded. There is no account and no server side; the models are downloaded
once and kept in the browser's IndexedDB. The interface opens in Chinese, with an "en" button for English.

## How Tofu runs it

| | |
|---|---|
| Framework preset | `static`: a finished site, Tofu builds nothing |
| Root folder | `site` |
| Install command | none |
| Build command | none |
| Output directory | `site` itself (entry page `site/index.html`) |
| Environment variables | none |
| Database | none |

`site/` holds 14 files, 9,552,777 bytes. The largest is the JavaScript bundle `assets/index-wKMmwxyL.js` (8.7 MB),
most of which is OpenCV.js.

### Why the site is prebuilt

Tofu cannot build this app from its sources as upstream ships them:

1. Upstream's `npm run build` runs `tsc && vite build`, and `tsc` stops on 18 type errors in upstream's code at this
   commit (for example, there are no type declarations for the global `ort`, which the page loads from a CDN).
   Upstream also ships `npm run fast-build`, the same `vite build` without that check, and that one works.
2. The build needs code that is generated at install time: `postinstall` runs `paraglide-js compile`, which writes
   `src/paraglide/` (the interface's translated strings) and loads its inlang plugins from jsDelivr. Tofu's static
   build installs with `npm ci --ignore-scripts`, so that step would not run and the build would fail.
3. `vite.config.ts` uses `vitest/config` and `vite-plugin-eslint`, and the root holds a `Dockerfile`; Tofu's static
   build accepts neither (an unsupported Vite configuration, and a container file read as a server).

So `site/` is built here with upstream's own commands, and Tofu publishes it as it is. `sh tofu-build/build-site.sh`
makes it from this branch:

1. `HUSKY=0 npm ci --no-audit --no-fund` (the committed `package-lock.json`; `HUSKY=0` only stops upstream's
   `prepare` script from adding git hooks to the checkout);
2. `npm run fast-build` (upstream's `vite build`); the bundle in `site/` is this output byte for byte;
3. a second `vite build --sourcemap` into a temporary folder, used only to list the packages inside the bundle;
4. `dist/` copied to `site/` without `_headers` (below), plus `LICENSE.txt`, `SOURCE.txt` and
   `THIRD-PARTY-NOTICES.txt` (written by `tofu-build/make_notices.py`).

### What a visitor gets that differs from upstream's own host

Upstream serves its site with `public/_headers` (`Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: require-corp`), which makes the page cross-origin isolated so ONNX Runtime may use
several WebAssembly threads. Tofu's static host does not read that file and refuses a site that contains a file of
that kind, so `site/` leaves it out and the page is not cross-origin isolated:

- with WebGPU (current Chrome and Edge): no difference, because the app runs ONNX Runtime with one thread on that
  path anyway;
- without WebGPU: the models run on WebAssembly with SIMD on one thread instead of several, so inpainting and
  especially 4x upscaling are slower on machines with many cores. They still work: the inpainting check below ran
  on this path.

## What reaches other sites

There are no analytics, tracking or advertising scripts in this commit of upstream, so there was nothing to remove;
nothing needs a key or an account. Both the source and the built bundle were searched; the bundle can contact only
the addresses below. The demo pictures are served from the app's own address.

- On every page load, ONNX Runtime Web 1.16.3 from jsDelivr, `cdn.jsdelivr.net/npm/onnxruntime-web@1.16.3/dist/`:
  `ort.webgpu.min.js` when the browser has WebGPU, otherwise `ort.wasm.min.js` (or `ort.wasm-core.min.js` /
  `ort.min.js` on older browsers), and the `.wasm` files it needs.
- On the first visit, the inpainting model `migan_pipeline_v2.onnx` (28,079,181 bytes) from Hugging Face, the public
  model hub: `huggingface.co/andraniksargsyan/migan`, published by MI-GAN's first author (model card licence MIT).
  Hugging Face answers with a redirect to its own download CDN (a `cdn.hf.co` address).
- The first time a person uses 4x upscaling, the model `realesrgan-x4.onnx` (67,051,787 bytes) from Hugging Face:
  `huggingface.co/lxfater/inpaint-web`, the upstream author's own public repository there (model card licence
  GPL-3.0).
- Only when a Hugging Face model download fails, the app tries the same file again from
  `worker-share-proxy-01f5.lxfater.workers.dev`. That is a Cloudflare Workers proxy run by the upstream author, not a
  model hub, which relays the same Hugging Face files for visitors who cannot reach Hugging Face. It needs no key;
  whether the author pays for it cannot be seen from outside. It is left as upstream ships it; if it goes away, only
  this fallback stops working.
- A link that opens only when clicked: the upstream GitHub repository, in the "联系作者" (About me) box.

The models are not in this repository and Tofu hosts none of them: each visitor's browser downloads them, once, and
keeps them in IndexedDB.

## What we changed, and why

No upstream file was changed. Every change is a new file on the `tofu` branch, so newer upstream code merges into it
without conflicts.

1. **`site/` added**: the finished site described above. Without it Tofu could not run the app (see *Why the site is
   prebuilt*). It leaves out upstream's `_headers` (see *What a visitor gets*), and adds `LICENSE.txt` (upstream's
   `LICENSE`, byte for byte, under a name the static host serves), `SOURCE.txt` (where the source of this build is,
   as GPL-3.0 asks of anyone who publishes it) and `THIRD-PARTY-NOTICES.txt` (the licences of the libraries inside
   the bundle).
2. **`tofu-build/` added**: `build-site.sh` rebuilds `site/` from the sources, `make_notices.py` writes the notices
   from the bundle's source map, `heroicons-v1.0.4-LICENSE.txt` and `opencv-4.5.5-COPYRIGHT.txt` are the two texts it
   quotes that the npm packages do not ship, and `SOURCE.txt` is the file copied into `site/`.
3. **`TOFU.md`**: this file.

Upstream commits a `.env` that names `REACT_APP_INPAINTING_ENDPOINT` and `REACT_APP_RECAPTCHA_SITE_KEY` (both set to
the placeholder `XXXX`) and `GENERATE_SOURCEMAP=false`, left over from an older Create React App setup. Vite hands
only `VITE_` names to an app, no code reads these, and the file is outside `site/`, so Tofu never uses it: the copy
needs no secret. Upstream's `Dockerfile` runs Vite's development server; Tofu does not use it either.

## Upstream and licence

- Upstream: <https://github.com/lxfater/inpaint-web> by lxfater, branch `main`, commit
  `d1b6cfd334dbc53d30675635a80366841c0239f9` (2025-12-23). Upstream's own demo is <https://inpaintweb.lxfater.com/>.
- Licence: GNU General Public License v3.0. `LICENSE` is kept exactly as upstream ships it (the licence text; it
  names no copyright holder), and `site/LICENSE.txt` is a byte-identical copy the site serves.
- Source offer: the site is the object code of a GPL-3.0 program, so whoever publishes it must offer its complete
  corresponding source. `site/SOURCE.txt`, served at `/SOURCE.txt`, points to this fork,
  <https://github.com/tofu-gallery/inpaint-web>, branch `tofu`, tag `pin/2026-10-23`, which holds the full source,
  the lockfile and the build script. A modified copy must keep offering its own source: keep `LICENSE.txt` and
  `SOURCE.txt` in the site, point `SOURCE.txt` at the source of the modified version (the copy's own repository,
  or a later tag of this fork), and mark the changes with a date, as GPL-3.0 section 5 asks.
- Third-party code inside the bundle: React 17.0.2, react-dom 17.0.2, scheduler 0.20.2 and object-assign 4.1.1
  (MIT), @heroicons/react 1.0.4 (MIT), react-use 17.3.1 (Unlicense), localforage 1.10.0 (Apache-2.0), and opencv-ts
  1.3.6 with OpenCV.js 4.5.5 (Apache-2.0; opencv-ts's `package.json` says MIT, but the LICENSE file it ships is
  Apache-2.0). Their texts are in `site/THIRD-PARTY-NOTICES.txt`. All of these may be combined with GPL-3.0 code.
  ONNX Runtime Web (MIT, Microsoft) is not bundled; the browser loads it from jsDelivr.
- Models, downloaded by the visitor's browser and not distributed here: MI-GAN by Picsart AI Research (MIT per its
  model card; the MI-GAN code repository is MIT too) and Real-ESRGAN x4 as converted and published by lxfater
  (GPL-3.0 per its model card; the original Real-ESRGAN by Xintao Wang is BSD-3-Clause).
- Demo pictures: upstream ships `public/examples/*.jpeg` (copied into `site/examples/`) without saying where they come
  from or under which licence. They are carried unchanged; that is a caveat for anyone who reuses them on their own.
- Name, logo and favicon: "Inpaint-web" is upstream's name and is unchanged. The page shows it as text; upstream ships
  no logo image on the page and no favicon (browsers ask for `/favicon.ico` and get a 404, as on a build of upstream).
- `media/` (the README's pictures, a demo video and WeChat QR codes) is upstream's README material, carried unchanged
  in the repository and not part of `site/`.

## Verification

On 2026-10-23 (UTC), from this branch, with Node 22.22.3 and npm 10.9.8 on macOS:

1. `npm ci`: installed 888 packages; its postinstall `paraglide-js compile` succeeded (it loaded the inlang plugins
   from jsDelivr).
2. `npm run build` (upstream's `tsc && vite build`): failed at `tsc` with 18 type errors in upstream's code
   (`src/adapters/superResolution.ts` 14, `src/adapters/util.ts` 2, `src/Editor.tsx` 2). Not used.
3. `npm run fast-build` (upstream's `vite build`): passed with 11 lint warnings and no errors; `dist/` held 12 files.
4. `sh tofu-build/build-site.sh` in the same checkout reproduced `site/` byte for byte (`diff -r` against the copy
   tested below).
5. A copy of `site/` with the paths Tofu's import drops removed (there were none) was served with
   `python3 -I -m http.server 63460 --bind 127.0.0.1`: `/`, the JavaScript bundle, `/examples/bag.jpeg`,
   `/SOURCE.txt` and `/LICENSE.txt` all answered 200. The only error answer in the server's log was `/favicon.ico`
   404 (upstream ships no favicon).
6. In a browser (Chromium 153) on that address, with no COOP/COEP headers, as on Tofu's static host:
   - the home page rendered with the header, the drop zone and the seven demo pictures;
   - the inpainting model downloaded from Hugging Face and was stored in IndexedDB (28,079,181 bytes);
   - the "dog" demo opened in the editor, a painted stroke started inpainting, and it finished in 4.3 s on the WebGPU
     path (`ort.webgpu.min.js`), adding the result to the history strip and showing the Undo button;
   - with WebGPU hidden from the page, the WebAssembly path (`ort.wasm.min.js`, SIMD, one thread in a worker)
     finished the same stroke in 5.5 s; the result differed from the original in 343 pixels, all inside
     (99,34)-(183,52) of the 275x183 picture, which is where the stroke was;
   - console: two ONNX Runtime warnings on the WebGPU path (`VerifyEachNodeIsAssignedToAnEp`, printed through
     `console.error`), none on the WebAssembly path; no failed requests; no alert. Hosts contacted: the app itself,
     `cdn.jsdelivr.net` and `huggingface.co`;
   - not exercised: 4x upscaling (a 67 MB download), Download, the language switch and the Workers fallback.

   The test's IndexedDB data was deleted and the local server stopped afterwards.
7. Import check, on the pushed `tofu` branch at the commit before this file
   (`python3 -I simulate_import.py --one tofu-gallery/inpaint-web tofu site yes`, which reads the branch the way
   Tofu's GitHub import does): root folder `site`, no container file, 14 files kept, none dropped, and every file
   `index.html` refers to is present.
8. Size: GitHub's zip of the `tofu` branch at that commit measured 7,576,551 bytes; with this file the tag holds 76
   files and about 14 MB unpacked, far inside the importer's limits (50 MB compressed, 20,000 files, 250 MB).
