#!/bin/sh
# Rebuild site/, the finished Inpaint-web that Tofu publishes, from this branch's own sources.
# Added for the Tofu gallery; not part of upstream Inpaint-web. Run from anywhere: sh tofu-build/build-site.sh
# Needs Node.js and npm (verified with Node 22.22.3 and npm 10.9.8), python3, and network access to
# registry.npmjs.org and cdn.jsdelivr.net: the postinstall step (paraglide-js compile) loads the inlang
# plugins named in project.inlang/settings.json from jsDelivr.
set -eu
cd "$(dirname "$0")/.."
# HUSKY=0 keeps upstream's prepare script (husky install) from adding git hooks to the checkout.
HUSKY=0 npm ci --no-audit --no-fund
# Upstream's `npm run build` runs tsc first, which stops on type errors in upstream's code at this commit;
# `fast-build` is upstream's own script for the same `vite build` without that check.
npm run fast-build
# A second build with source maps, only to list the packages inside the bundle for the notices.
maps=$(mktemp -d)
npx --no-install vite build --sourcemap --outDir "$maps" --emptyOutDir
rm -rf site
mkdir site
cp -R dist/. site/
# _headers is a Netlify / Cloudflare Pages header file (COOP and COEP). Tofu's static host does not read it
# and refuses a site holding a file with no published file type, so the site leaves it out.
rm -f site/_headers
cp LICENSE site/LICENSE.txt
cp tofu-build/SOURCE.txt site/SOURCE.txt
# Tofu, 2026-10-24: retain the visible source link and dated About-link notice in the finished site (see TOFU.md).
python3 -I tofu-build/add_source_link.py site/index.html
python3 -I tofu-build/make_notices.py . "$maps" site/THIRD-PARTY-NOTICES.txt \
  tofu-build/heroicons-v1.0.4-LICENSE.txt tofu-build/opencv-4.5.5-COPYRIGHT.txt
rm -rf "$maps"
