/**
 * One-off migration helper: replaces literal UI copy in a page with a `t()` call.
 *
 * Reads and writes UTF-8 explicitly so accented Spanish text cannot be
 * corrupted by an encoding mismatch, which is what a naive
 * PowerShell Get-Content/Set-Content round trip does.
 *
 * Usage: node scripts/migrate-i18n.mjs <file> <specJsonFile>
 */
import { readFileSync, writeFileSync } from 'node:fs';

const [file, specFile] = process.argv.slice(2);

if (!file || !specFile) {
  console.error('usage: node migrate-i18n.mjs <file> <specJsonFile>');
  process.exit(2);
}

const before = readFileSync(file, 'utf8');
let after = before;
const spec = JSON.parse(readFileSync(specFile, 'utf8').replace(/^\uFEFF/, ''));
const missed = [];

for (const { find, replace, all } of spec) {
  if (after.includes(find)) {
    after = all ? after.split(find).join(replace) : after.replace(find, replace);
  } else {
    missed.push(find);
  }
}

if (after === before) {
  console.log(`no change: ${file}`);
  process.exit(missed.length ? 1 : 0);
}

writeFileSync(file, after, 'utf8');

const mojibake = (after.match(/[ÃÂ]/g) || []).length;
console.log(`updated: ${file} | mojibake markers: ${mojibake}`);

if (missed.length) {
  console.log(`MISSED ${missed.length}:`);
  for (const m of missed) console.log(`  ${JSON.stringify(m)}`);
}

process.exit(missed.length ? 1 : 0);