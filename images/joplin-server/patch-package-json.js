#!/usr/bin/env node
// Build-time workspace patch for Joplin Server on loong64.
//
// 1. Remove onenote-converter from @joplin/lib: upstream Dockerfile.server
//    does the same; its native dependency has no loong64 build.
// 2. Blank every workspace "postinstall" (the root one runs `husky && gulp
//    build` even when YARN_ENABLE_SCRIPTS=false). The explicit
//    buildSequential step performs the real build.
// 3. Alias only @joplin/turndown's Rollup 4.2.0 to @rollup/wasm-node 4.2.0.
//    Rollup 4.2.0 predates loong64 native bindings, and Rollup's loader
//    requires an exact-version binding (the earliest published loong64
//    binding is 4.21.3). turndown-plugin-gfm keeps its own Rollup 0.50.1.
const fs = require('fs');
const path = require('path');

const rootPath = path.join(__dirname, 'package.json');
const rootPkg = JSON.parse(fs.readFileSync(rootPath, 'utf8'));
rootPkg.scripts = rootPkg.scripts || {};
rootPkg.scripts.postinstall = '';
rootPkg.resolutions = rootPkg.resolutions || {};
rootPkg.resolutions['@joplin/turndown/rollup'] = 'npm:@rollup/wasm-node@4.2.0';
fs.writeFileSync(rootPath, `${JSON.stringify(rootPkg, null, 2)}\n`);

const packagesDir = path.join(__dirname, 'packages');
for (const name of fs.readdirSync(packagesDir)) {
	const pkgPath = path.join(packagesDir, name, 'package.json');
	if (!fs.existsSync(pkgPath)) continue;
	const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
	if (pkg.scripts && pkg.scripts.postinstall) pkg.scripts.postinstall = '';
	for (const field of ['dependencies', 'devDependencies', 'optionalDependencies']) {
		if (pkg[field] && pkg[field]['onenote-converter']) delete pkg[field]['onenote-converter'];
	}
	fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`);
}

console.log('patched package.json files');
