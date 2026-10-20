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

async function projectFixture(t) {
  const f = await fixture(t);
  const project = {
    ...structuredClone(f.skill),
    id: 'sample-project', kind: 'project', source: 'external', status: 'experimental',
    repository_url: 'https://github.com/example/upstream',
    entry_url: 'https://github.com/example/upstream/blob/main/SKILL.md',
    examples: []
  };
  delete project.path;
  f.catalog.schema_version = 2;
  f.catalog.entries.push(project);
  await f.save();
  return { ...f, project };
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

test('schema version 2 retains local skill packaging checks', async t => {
  const f = await fixture(t);
  f.catalog.schema_version = 2;
  f.skill.source = 'local';
  await f.save();
  assert.deepEqual(await implementation.validateRepository(f.root), []);
  f.skill.examples[0].output = 'skills/sample-skill/examples/missing.md';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('missing file')));
});

test('local incubation ideas retain their contract in both schema versions', async t => {
  const f = await fixture(t);
  const idea = { ...structuredClone(f.skill), id: 'sample-idea', kind: 'idea', status: 'incubating', path: 'idea.md', examples: [] };
  await writeFile(path.join(f.root, idea.path), '# An incubation brief\n');
  f.catalog.entries.push(idea);
  for (const schemaVersion of [1, 2]) {
    f.catalog.schema_version = schemaVersion;
    await f.save();
    assert.deepEqual(await implementation.validateRepository(f.root), [], `schema ${schemaVersion}`);
  }
});

test('unsupported schema versions are rejected', async t => {
  const f = await fixture(t);
  f.catalog.schema_version = 3;
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('unsupported schema_version')));
});

test('an external project is navigation metadata without a local skill file', async t => {
  const f = await projectFixture(t);
  assert.deepEqual(await implementation.validateRepository(f.root), []);
});

test('external projects accept both supported statuses', async t => {
  const f = await projectFixture(t);
  f.project.status = 'stable';
  await f.save();
  assert.deepEqual(await implementation.validateRepository(f.root), []);
});

test('external projects require schema version 2', async t => {
  const f = await projectFixture(t);
  f.catalog.schema_version = 1;
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('project requires schema_version 2')));
});

test('external projects reject a local path even when it is empty', async t => {
  const f = await projectFixture(t);
  for (const localPath of ['skills/sample-project/SKILL.md', '']) {
    f.project.path = localPath;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('project must not have a local path')));
  }
});

test('only project entries may use external source', async t => {
  const f = await fixture(t);
  f.skill.source = 'external';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('source')));
});

test('unknown local source values are rejected', async t => {
  const f = await fixture(t);
  f.skill.source = 'remote';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('source')));
});

test('external projects require an explicit external source', async t => {
  const f = await projectFixture(t);
  for (const source of [undefined, 'local', 'remote', null]) {
    f.project.source = source;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('project source must be external')), `source ${source}`);
  }
});

test('external projects reject unsupported status', async t => {
  const f = await projectFixture(t);
  f.project.status = 'incubating';
  await f.save();
  assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('invalid project status')));
});

test('external projects require both repository and entry URLs', async t => {
  const f = await projectFixture(t);
  for (const field of ['repository_url', 'entry_url']) {
    const value = f.project[field];
    delete f.project[field];
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes(field)), field);
    f.project[field] = value;
  }
});

test('project links accept GitHub root, blob, tree, raw and raw-content paths from the same repository', async t => {
  const f = await projectFixture(t);
  f.project.repository_url += '/';
  const links = [
    'https://github.com/example/upstream',
    'https://github.com/example/upstream/',
    'https://github.com/example/upstream/blob/main/SKILL.md',
    'https://github.com/example/upstream/tree/main/skills',
    'https://github.com/example/upstream/raw/main/SKILL.md',
    'https://raw.githubusercontent.com/example/upstream/main/SKILL.md'
  ];
  for (const entryUrl of links) {
    f.project.entry_url = entryUrl;
    await f.save();
    assert.deepEqual(await implementation.validateRepository(f.root), [], entryUrl);
  }
});

test('repository URLs must identify a clean HTTPS GitHub repository root', async t => {
  const f = await projectFixture(t);
  const invalidUrls = [
    'http://github.com/example/upstream',
    'https://gitlab.com/example/upstream',
    'https://github.com/example/upstream/blob/main/README.md',
    'https://github.com/example',
    'https://github.com/user:secret@example/upstream',
    'https://user:secret@github.com/example/upstream',
    'https://github.com/example/upstream?tab=readme',
    'https://github.com/example/upstream#readme',
    'https://github.com/example/upstream?',
    'https://github.com/example/upstream#',
    'https://github.com:8443/example/upstream'
  ];
  for (const repositoryUrl of invalidUrls) {
    f.project.repository_url = repositoryUrl;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('repository_url')), repositoryUrl);
  }
});

test('entry URLs reject unrelated hosts, repositories, protocols and non-entry routes', async t => {
  const f = await projectFixture(t);
  const invalidUrls = [
    'http://github.com/example/upstream',
    'https://example.com/example/upstream/blob/main/SKILL.md',
    'https://github.com/example/another/blob/main/SKILL.md',
    'https://github.com/another/upstream/tree/main/skills',
    'https://raw.githubusercontent.com/example/another/main/SKILL.md',
    'https://github.com/example/upstream/issues/1',
    'https://github.com/example/upstream/blob/',
    'https://github.com/user:secret@example/upstream',
    'https://user:secret@github.com/example/upstream',
    'https://github.com/example/upstream?tab=readme',
    'https://github.com/example/upstream#readme',
    'https://raw.githubusercontent.com/example/upstream/main/SKILL.md?token=secret',
    'https://raw.githubusercontent.com/example/upstream/main/SKILL.md#section',
    'https://github.com:8443/example/upstream',
    'skills/sample-project/SKILL.md'
  ];
  for (const entryUrl of invalidUrls) {
    f.project.entry_url = entryUrl;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('entry_url')), entryUrl);
  }
});

test('project examples can link to an input and output from the same repository', async t => {
  const f = await projectFixture(t);
  f.project.examples = [{
    input: 'https://github.com/example/upstream/blob/main/examples/input.md',
    output: 'https://raw.githubusercontent.com/example/upstream/main/examples/output.md'
  }];
  await f.save();
  assert.deepEqual(await implementation.validateRepository(f.root), []);
});

test('project examples require an array of complete same-repository URL pairs', async t => {
  const f = await projectFixture(t);
  for (const examples of [
    undefined,
    {},
    [{ input: 'https://github.com/example/upstream/blob/main/examples/input.md' }],
    [{ input: 'https://github.com/example/another/blob/main/input.md', output: 'https://github.com/example/upstream/blob/main/output.md' }],
    [{ input: 'http://github.com/example/upstream/blob/main/input.md', output: 'https://github.com/example/upstream/blob/main/output.md' }],
    [{ input: 'https://github.com/example/upstream/blob/main/input.md', output: 'https://user:secret@github.com/example/upstream/blob/main/output.md' }],
    [{ input: 'https://github.com/example/upstream/blob/main/input.md', output: 'https://github.com/example/upstream/blob/main/output.md?raw=true' }],
    [{ input: 'https://github.com/example/upstream/blob/main/input.md', output: 'https://github.com/example/upstream/blob/main/output.md#example' }],
    [{ input: 'skills/sample-skill/examples/input.md', output: 'skills/sample-skill/examples/output.md' }]
  ]) {
    f.project.examples = examples;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('examples')), JSON.stringify(examples));
  }
});

test('project entries retain the generic metadata requirements', async t => {
  const f = await projectFixture(t);
  for (const field of ['name', 'description', 'categories', 'tags', 'use_when', 'not_for', 'inputs', 'outputs', 'requirements', 'evidence']) {
    const value = f.project[field];
    delete f.project[field];
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes(`sample-project.${field}`)), field);
    f.project[field] = value;
  }
});

test('malformed entry categories report validation errors without throwing', async t => {
  const f = await fixture(t);
  for (const categories of [{ learning: true }, 42, null]) {
    f.skill.categories = categories;
    await f.save();
    assert.ok((await implementation.validateRepository(f.root)).some(x => x.includes('categories must be a nonempty string array')));
  }
});
