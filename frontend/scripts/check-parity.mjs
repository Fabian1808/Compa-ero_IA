import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const NODE = process.execPath;
const out = mkdtempSync(join(tmpdir(), 'i18nparity-'));

function run(args, cwd = process.cwd()) {
  return execFileSync(NODE, args, { cwd, encoding: 'utf8', stdio: 'pipe' });
}

try {
  run(['node_modules/typescript/bin/tsc', 'src/i18n/i18n.ts', '--outDir', out, '--module', 'commonjs', '--target', 'es2020', '--skipLibCheck', '--esModuleInterop']);

  const es = require(join(out, 'locales/es-PE.js')).esPE;
  const en = require(join(out, 'locales/en-US.js')).enUS;

  const flat = (o, p = '') =>
    Object.entries(o).flatMap(([k, v]) =>
      v && typeof v === 'object' && !('forms' in v) ? flat(v, `${p}${k}.`) : [`${p}${k}`]
    );

  const a = flat(es).sort();
  const b = flat(en).sort();
  const onlyEs = a.filter((k) => !b.includes(k));
  const onlyEn = b.filter((k) => !a.includes(k));

  console.log('claves es-PE:', a.length, '| claves en-US:', b.length);
  if (onlyEs.length === 0 && onlyEn.length === 0) {
    console.log('PARIDAD: OK');
  } else {
    console.log('PARIDAD: ROTA');
    onlyEs.forEach((k) => console.log('  solo es-PE:', k));
    onlyEn.forEach((k) => console.log('  solo en-US:', k));
    process.exitCode = 1;
  }

  // Empty / untranslated checks
  const empties = a.filter((k) => {
    const val = k.split('.').reduce((acc, part) => (acc ? acc[part] : undefined), es);
    return typeof val === 'string' && val.trim() === '';
  });
  if (empties.length) {
    console.log('valores vacios en es-PE:', empties.join(', '));
    process.exitCode = 1;
  }
} finally {
  rmSync(out, { recursive: true, force: true });
}