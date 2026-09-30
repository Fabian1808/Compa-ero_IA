import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const NODE = process.execPath;
const out = mkdtempSync(join(tmpdir(), 'i18nrun-'));

try {
  execFileSync(NODE, ['node_modules/typescript/bin/tsc', 'src/i18n/i18n.ts', 'src/i18n/enumLabel.ts', '--outDir', out, '--module', 'commonjs', '--target', 'es2020', '--skipLibCheck', '--esModuleInterop'], { stdio: 'pipe' });
  const i18n = require(join(out, 'i18n.js'));
  const { enumLabel } = require(join(out, 'enumLabel.js'));

  const cases = [
    ['pages.workmap.sublabels.active', 1],
    ['pages.workmap.sublabels.active', 5],
    ['pages.workmap.sublabels.pending', 0],
    ['pages.workmap.sublabels.pending', 1],
    ['pages.workmap.sublabels.pending', 12],
    ['pages.workmap.sublabels.overdue', 1],
    ['pages.workmap.sublabels.overdue', 3],
    ['pages.workmap.dueInDays', 1],
    ['pages.workmap.dueInDays', 5],
    ['pages.workmap.minutes', 90],
    ['pages.workmap.hours', 2],
  ];

  for (const locale of ['es-PE', 'en-US']) {
    i18n.setActiveLocale(locale);
    console.log('--- ' + locale + ' ---');
    for (const [key, count] of cases) {
      console.log(`  ${key} (${count}) => ${JSON.stringify(i18n.translate(key, { count }))}`);
    }
    console.log('  pages.workmap.progress => ' + JSON.stringify(i18n.translate('pages.workmap.progress', { completed: 3, total: 10, pending: 7 })));
    console.log('  pages.workmap.dueOn => ' + JSON.stringify(i18n.translate('pages.workmap.dueOn', { date: '10/10/2026' })));
    console.log('  work.states.in_progress => ' + JSON.stringify(i18n.translate('work.states.in_progress')));

    const enumCases = [
      ['work.states', 'in_progress'],
      ['work.states', 'waiting_response'],
      ['work.states', 'requires_decision'],
      ['work.states', 'pending'],
      ['work.states', 'cancelled'],
      ['work.projectStates', 'on_hold'],
      ['work.projectStates', 'planning'],
      ['work.priorities', 'urgent'],
      ['work.urgencies', 'critical'],
      ['pages.followups.statuses', 'reminder_sent'],
      ['pages.followups.statuses', 'draft_prepared'],
      ['pages.commitments.statuses', 'expired'],
      ['work.states', 'unknown_value'],
    ];
    console.log('  --- enumLabel ---');
    for (const [group, value] of enumCases) {
      console.log(`  enumLabel(${group}, ${value}) => ${JSON.stringify(enumLabel(i18n.translate, group, value))}`);
    }
    console.log('  work.priorities.high => ' + JSON.stringify(i18n.translate('work.priorities.high')));
  }
} finally {
  rmSync(out, { recursive: true, force: true });
}