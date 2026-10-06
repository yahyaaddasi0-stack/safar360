import { copyFileSync, cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
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
  'khizana.html',
  'products.json',
  'cinema.html',
  'cinema.json',
];

rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
for (const file of files) {
  const source = join(root, file);
  if (!existsSync(source)) throw new Error(`Missing public asset: ${file}`);
  copyFileSync(source, join(output, file));
}
const assets = join(root, 'assets');
if (existsSync(assets)) cpSync(assets, join(output, 'assets'), { recursive: true });
console.log(`Safar 360 static output: ${files.join(', ')}`);
