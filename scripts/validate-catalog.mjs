import { readFile, readdir, realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export async function validateRepository(directory) {
  const root = await realpath(directory);
  const errors = [];
  const fail = message => errors.push(message);
  const nonempty = value => typeof value === 'string' && value.trim().length > 0;
  const strings = value => Array.isArray(value) && value.every(nonempty);
  const bilingual = (value, label) => {
    for (const language of ['zh', 'en']) if (!nonempty(value?.[language])) fail(`${label}.${language} must be nonempty`);
  };
  const file = async relative => {
    if (!nonempty(relative) || relative.includes('\\') || relative.split('/').includes('..') || path.isAbsolute(relative) || /^[a-z]+:/i.test(relative)) {
      fail(`unsafe path: ${relative}`);
      return null;
    }
    const absolute = path.resolve(root, relative);
    try {
      const resolved = await realpath(absolute);
      const within = path.relative(root, resolved);
      if (within.startsWith('..') || path.isAbsolute(within)) {
        fail(`unsafe path: ${relative}`);
        return null;
      }
      if (!(await stat(resolved)).isFile()) throw new Error('not a file');
      return resolved;
    } catch {
      fail(`missing file: ${relative}`);
      return null;
    }
  };
  let catalog;
  try { catalog = JSON.parse(await readFile(path.join(root, 'catalog.json'), 'utf8')); }
  catch (error) { return [`cannot read catalog.json: ${error.message}`]; }
  if (catalog.schema_version !== 1) fail('unsupported schema_version');
  for (const key of ['repository', 'raw_base']) {
    if (!nonempty(catalog[key]) || !catalog[key].startsWith('https://')) fail(`${key} must be an HTTPS URL`);
  }
  if (!catalog.raw_base?.endsWith('/')) fail('raw_base must have a trailing slash');
  const categories = new Set();
  if (!Array.isArray(catalog.categories)) fail('categories must be an array');
  else for (const category of catalog.categories) {
    if (!nonempty(category?.id) || categories.has(category.id)) fail('invalid or duplicate category id');
    categories.add(category?.id);
    bilingual(category?.name, `category ${category?.id}.name`);
  }
  if (!Array.isArray(catalog.entries)) return [...errors, 'entries must be an array'];
  const ids = new Set();
  const indexed = new Set();
  for (const entry of catalog.entries) {
    if (!entry || typeof entry !== 'object') { fail('entry must be an object'); continue; }
    const id = entry.id;
    if (typeof id !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id) || id.length > 64) fail(`invalid id: ${id}`);
    if (ids.has(id)) fail(`duplicate id: ${id}`);
    ids.add(id);
    for (const key of ['name', 'description']) bilingual(entry[key], `${id}.${key}`);
    for (const key of ['categories', 'tags', 'use_when', 'not_for', 'inputs', 'outputs']) {
      if (!strings(entry[key]) || entry[key].length === 0) fail(`${id}.${key} must be a nonempty string array`);
    }
    if (!strings(entry.requirements)) fail(`${id}.requirements must be a string array`);
    for (const category of entry.categories ?? []) if (!categories.has(category)) fail(`${id}: unknown category ${category}`);
    for (const key of ['origin', 'validation']) if (!nonempty(entry.evidence?.[key])) fail(`${id}.evidence.${key} is required`);
    const entryFile = await file(entry.path);
    if (entry.kind === 'skill') {
      if (!['experimental', 'stable'].includes(entry.status)) fail(`${id}: invalid skill status`);
      if (entry.path !== `skills/${id}/SKILL.md`) fail(`${id}: skill path must match its id`);
      indexed.add(entry.path);
      if (entryFile) {
        const text = await readFile(entryFile, 'utf8');
        const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)?.[1];
        const name = frontmatter?.match(/^name:\s*(.+)$/m)?.[1]?.trim().replace(/^['"]|['"]$/g, '');
        if (name !== id) fail(`${id}: frontmatter name does not match catalog`);
        if (!/^description:\s*\S.+$/m.test(frontmatter ?? '')) fail(`${id}: frontmatter description is missing`);
      }
      if (!Array.isArray(entry.examples) || entry.examples.length === 0) fail(`${id}: a complete example is required`);
      else for (const example of entry.examples) for (const key of ['input', 'output']) await file(example?.[key]);
    } else if (entry.kind === 'idea') {
      if (entry.status !== 'incubating') fail(`${id}: idea status must be incubating`);
      if (!Array.isArray(entry.examples) || entry.examples.length !== 0) fail(`${id}: ideas must not advertise runnable examples`);
    } else fail(`${id}: unknown kind`);
  }
  async function walk(directory, relative = '') {
    let children;
    try { children = await readdir(directory, { withFileTypes: true }); }
    catch (error) { if (error.code === 'ENOENT') return; throw error; }
    for (const child of children) {
      const relativePath = relative ? `${relative}/${child.name}` : child.name;
      if (child.isSymbolicLink()) { fail(`symlink in skills directory: ${relativePath}`); continue; }
      if (child.isDirectory()) await walk(path.join(directory, child.name), relativePath);
      else if (child.name === 'SKILL.md' && !indexed.has(`skills/${relativePath}`)) fail(`unindexed skill: skills/${relativePath}`);
    }
  }
  await walk(path.join(root, 'skills'));
  return errors;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const errors = await validateRepository(root);
  if (errors.length) {
    for (const error of errors) console.error(`- ${error}`);
    process.exitCode = 1;
  } else {
    const catalog = JSON.parse(await readFile(path.join(root, 'catalog.json'), 'utf8'));
    const skills = catalog.entries.filter(entry => entry.kind === 'skill').length;
    console.log(`Catalog OK: ${skills} skills, ${catalog.entries.length - skills} ideas; paths and metadata verified.`);
  }
}
