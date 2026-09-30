import { readFileSync } from 'node:fs';

const [file, key, span] = process.argv.slice(2);
const src = readFileSync(file, 'utf8');
const i = src.indexOf(key);
if (i < 0) {
  console.log('NOT FOUND: ' + key);
  process.exit(0);
}
console.log(src.slice(i, i + Number(span || 1500)));