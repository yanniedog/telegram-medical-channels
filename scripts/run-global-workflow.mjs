import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const directory = process.env.CURSOR_WORKFLOW_SCRIPTS;
const [script, ...args] = process.argv.slice(2);
if (!directory || !['chief-scan.mjs', 'pr-bot-feedback-check.mjs'].includes(script)) {
  console.error('Set CURSOR_WORKFLOW_SCRIPTS to the shared workflow scripts directory.');
  process.exit(1);
}
const result = spawnSync(process.execPath, [join(directory, script), ...args], {
  stdio: 'inherit', windowsHide: true,
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
