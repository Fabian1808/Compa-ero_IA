import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = 'src';
const files = [];
(function walk(dir) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.tsx$/.test(p)) files.push(p);
  }
})(ROOT);

const JSX_TEXT = />([^<>{}]*[A-Za-zÁÉÍÓÚÑáéíóúñ][^<>{}]*)</g;
const JSX_ATTR = /(?:title|label|placeholder|aria-label|alt|description|confirmText)=["']([^"']*[A-Za-zÁÉÍÓÚÑáéíóúñ][^"']*)["']/g;
const QUOTED = /"([A-ZÁÉÍÓÚÑ][^"]{2,60})"/g;

const IGNORE = /^(https?:|[./#]|[\w-]+\.(tsx|ts|json|css|py)$)/;

const rows = [];
for (const f of files) {
  const src = readFileSync(f, 'utf8');
  const hits = new Set();
  for (const re of [JSX_TEXT, JSX_ATTR, QUOTED]) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(src))) {
      const v = m[1].trim();
      if (!v || IGNORE.test(v)) continue;
      if (/^[A-Z_]+$/.test(v)) continue;
      if (/^(className|useEffect|useState|useCallback|async |function |const |return |import |export )/.test(v)) continue;
      hits.add(v);
    }
  }
  if (hits.size) rows.push([f, hits.size]);
}

rows.sort((a, b) => b[1] - a[1]);
let total = 0;
for (const [f, n] of rows) {
  total += n;
  console.log(String(n).padStart(4), f);
}
console.log('TOTAL', total);