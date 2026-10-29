import { readdir, readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const sourceRoot = fileURLToPath(new URL('../src/', import.meta.url));
const extensions = new Set(['.ts', '.html', '.scss']);
const invalidMarkers = ['Ã', 'â', '�'];
const invalidFiles = [];

async function scan(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await scan(path);
    if (entry.isFile() && extensions.has(extname(entry.name))) {
      const content = await readFile(path, 'utf8');
      if (invalidMarkers.some(marker => content.includes(marker))) {
        invalidFiles.push(path);
      }
    }
  }
}

await scan(sourceRoot);

if (invalidFiles.length) {
  console.error('Se han detectado caracteres con codificación incorrecta:');
  invalidFiles.forEach(path => console.error(` - ${path}`));
  process.exit(1);
}

console.log('Codificación de texto del frontend correcta.');
