import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

function getFilesRecursively(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  list.forEach((file) => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getFilesRecursively(fullPath));
    } else {
      results.push(fullPath);
    }
  });
  return results;
}

describe('Design Token Integrity - Zero Raw Hex Values in /src', () => {
  it('enforces that no raw hex color literals exist in any source code file under /src', () => {
    const srcDir = path.resolve(__dirname, '..');
    const files = getFilesRecursively(srcDir).filter(
      (f) =>
        (f.endsWith('.ts') || f.endsWith('.tsx') || f.endsWith('.css') || f.endsWith('.js')) &&
        !f.endsWith('no-raw-hex.test.ts')
    );

    const hexPattern = /#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g;
    const violations: { file: string; line: number; match: string }[] = [];

    files.forEach((file) => {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      lines.forEach((line, index) => {
        // Ignore comments that explicitly mention hex in test strings if any
        const matches = line.match(hexPattern);
        if (matches) {
          matches.forEach((match) => {
            violations.push({
              file: path.relative(srcDir, file),
              line: index + 1,
              match,
            });
          });
        }
      });
    });

    expect(
      violations,
      `Found raw hex color literals in /src: ${JSON.stringify(violations, null, 2)}`
    ).toHaveLength(0);
  });
});
