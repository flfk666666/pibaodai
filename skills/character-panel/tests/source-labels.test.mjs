import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const template = version => readFileSync(new URL(`../assets/dashboard-${version}.html`, import.meta.url), 'utf8');
function extractFunction(source, name) {
  const start = source.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `${name} exists`);
  const body = source.slice(start);
  const end = body.search(/\n(?=function |holisticOverview\()/);
  assert.ok(end > 0, `${name} boundary exists`);
  return body.slice(0, end);
}
const sourceText = vm.runInNewContext(`(${extractFunction(template('v08'), 'lifeSourceText')})`, {
  narrativeText: value => String(value ?? ''),
  itemLookup: { B2: { name: '运动表现' } },
});

test('profile references accept arbitrary local prefixes without exposing them', () => {
  for (const prefix of ['', 'vault/fictional-record/', '../imaginary/profile/', '/srv/example/private/', 'Q:\\Demo Vault\\record\\']) {
    assert.equal(sourceText(`${prefix}current.md#/items/B2/inputs/performance`), '角色档案 · B2 运动表现 · 运动表现');
    assert.equal(sourceText(`${prefix}current.md#/items/F6/inputs/custom_field`), '角色档案 · F6 子项材料 · 本人输入');
  }
});

test('local source files receive a generic label regardless of project names', () => {
  for (const path of [
    'imaginary-project/journal.md', 'alpha/beta/notes.json', 'note.txt',
    'fictional-vault/private-record', 'sample-archive/.env',
    './fictional.md', '../../example/private.yaml',
    '/srv/fictional/notes.md', '~/demo/diary.md',
    'Q:\\Fictional\\notes.md', 'Q:/Fictional/notes.md',
    '\\\\demo-host\\example-share\\notes.md',
  ]) {
    assert.equal(sourceText(path), '本地私人记录');
    assert.equal(sourceText(`来源：${path}；已复核`), '来源：本地私人记录；已复核');
  }
});

test('human descriptions and self-report labels remain readable', () => {
  assert.equal(sourceText('本人访谈；本周训练观察'), '本人访谈；本周训练观察');
  assert.equal(sourceText('self_report；本人确认'), '本人自述；本人确认');
  assert.equal(sourceText('访谈/自述'), '访谈/自述');
  assert.equal(sourceText('2026.11.05 访谈'), '2026.11.05 访谈');
  assert.equal(sourceText('版本 1.5 记录'), '版本 1.5 记录');
});

test('public HTTP(S) URLs retain paths and fragments', () => {
  for (const url of ['https://example.org/research/paper.pdf#results', 'http://example.net/current.md#/items/B2/inputs/performance']) {
    assert.equal(sourceText(url), url);
    assert.equal(sourceText(`公开来源：${url}；私人：vault/demo.md`), `公开来源：${url}；私人：本地私人记录`);
  }
});

for (const version of ['v07', 'v08']) {
  test(`${version} housing fallback describes the destination generically`, () => {
    const texts = [];
    const financialOverview = vm.runInNewContext(`(${extractFunction(template(version), 'financialOverview')})`, {
      data: { financial_context: { fallback_housing_scenario: {} } },
      itemLookup: {}, finite: Number.isFinite, list: value => value ?? [],
      money: () => '待补', monthsText: () => '待补',
      add: (_parent, _tag, _className, text) => { texts.push(text ?? ''); return {}; },
    });
    financialOverview({});
    assert.ok(texts.some(text => text.includes('退路所在地生活预算')), 'housing explanation uses a generic destination');
  });
}
