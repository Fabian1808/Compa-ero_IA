import { readFileSync } from 'node:fs';

const file = process.argv[2];
const src = readFileSync(file, 'utf8');

const JSX_TEXT = />([^<>{}]*[A-Za-zÁÉÍÓÚÑáéíóúñ][^<>{}]*)</g;
const JSX_ATTR = /(?:title|label|placeholder|aria-label|alt|description|confirmText)=["']([^"']*[A-Za-zÁÉÍÓÚÑáéíóúñ][^"']*)["']/g;
const QUOTED = /"([A-ZÁÉÍÓÚÑ][^"]{2,60})"/g;

const seen = new Set();
for (const re of [JSX_TEXT, JSX_ATTR, QUOTED]) {
  re.lastIndex = 0;
  let m;
  while ((m = re.exec(src))) {
    const v = m[1].trim();
    if (!v || seen.has(v)) continue;
    seen.add(v);
    console.log(JSON.stringify(v));
  }
}