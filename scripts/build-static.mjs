import { copyFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const output = join(root, 'dist');
const files = [
  'index.html',
  'styles.css',
  'app.js',
  'sw.js',
  'manifest.json',
  'characters-public.json',
  'manus-routes.json',
];

rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
for (const file of files) {
  const source = join(root, file);
  if (!existsSync(source)) throw new Error(`Missing public asset: ${file}`);
  copyFileSync(source, join(output, file));
}
console.log(`Safar 360 static output: ${files.join(', ')}`);
