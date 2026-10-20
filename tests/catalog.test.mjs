import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const implementation = await import('../scripts/validate-catalog.mjs').catch(error => {
  if (error.code === 'ERR_MODULE_NOT_FOUND') return {};
  throw error;
});

async function fixture(t) {
  assert.equal(typeof implementation.validateRepository, 'function', 'catalog validator is implemented');
  const root = await mkdtemp(path.join(tmpdir(), 'pibaodai-test-'));
  t.after(async () => {
    assert.ok(root.startsWith(path.join(tmpdir(), 'pibaodai-test-')));
    await rm(root, { recursive: true, force: true });
  });
  const skill = {
    id: 'sample-skill', kind: 'skill', status: 'experimental',
    name: { zh: '测试技能', en: 'Sample skill' },
    description: { zh: '用于测试目录。', en: 'Exercise the catalog contract.' },
    categories: ['learning'], tags: ['学习', 'learn'],
    use_when: ['Need to learn'], not_for: ['Unrelated work'],
    inputs: ['A question'], outputs: ['An explanation'], requirements: [],
    path: 'skills/sample-skill/SKILL.md',
    examples: [{ input: 'skills/sample-skill/examples/input.md', output: 'skills/sample-skill/examples/output.md' }],
    evidence: { origin: 'Authored fixture', validation: 'Packaging test only' }
  };
  const catalog = {
    schema_version: 1, repository: 'https://github.com/example/pibaodai',
    raw_base: 'https://raw.githubusercontent.com/example/pibaodai/main/',
    categories: [{ id: 'learning', name: { zh: '学习', en: 'Learning' } }],
    entries: [skill]
  };
  await mkdir(path.join(root, 'skills/sample-skill/examples'), { recursive: true });
  await writeFile(path.join(root, skill.path), '---\nname: sample-skill\ndescription: Exercise the catalog contract.\n---\n\nA working fixture.\n');
  for (const filename of Object.values(skill.examples[0])) await writeFile(path.join(root, filename), '# Example\n');
  const save = () => writeFile(path.join(root, 'catalog.json'), JSON.stringify(catalog));
  await save();
  return { root, catalog, skill, save };
}

test('a self-contained skill with a complete example is discoverable', async t => {
  const { root } = await fixture(t);
  assert.deepEqual(await implementation.validateRepository(root), []);
});

test('duplicate IDs cannot silently shadow another entry', async t => {
  const f = await fixture(t);
  f.catalog.entries.push(structuredClone(f.skill));
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('duplicate id')));
});

test('an incubation idea cannot claim a runnable status', async t => {
  const f = await fixture(t);
  f.skill.kind = 'idea';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('status')));
});

test('entry paths cannot escape the repository', async t => {
  const f = await fixture(t);
  f.skill.path = '../private-notes.md';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('unsafe path')));
});

test('a skill with a missing example fails the packaging check', async t => {
  const f = await fixture(t);
  f.skill.examples[0].output = 'skills/sample-skill/examples/missing.md';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('missing file')));
});

test('a skill folder omitted from the AI catalog is reported', async t => {
  const f = await fixture(t);
  await mkdir(path.join(f.root, 'skills/forgotten-skill'));
  await writeFile(path.join(f.root, 'skills/forgotten-skill/SKILL.md'), '---\nname: forgotten-skill\ndescription: Forgotten.\n---\n');
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('unindexed skill')));
});

test('metadata must identify the same skill as the catalog', async t => {
  const f = await fixture(t);
  await writeFile(path.join(f.root, f.skill.path), '---\nname: another-skill\ndescription: Wrong identifier.\n---\n');
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('frontmatter name')));
});

test('bilingual descriptions are required for routing', async t => {
  const f = await fixture(t);
  f.skill.description.en = '';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('description.en')));
});
