// Copyright 2026 Softwell S.r.l. - Genro Team
// SPDX-License-Identifier: Apache-2.0
// Python/JS parity: reads the same files as tests/test_period_parser.py and
// applies the divergences the same way, so both languages must give the same
// result on every case.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseDateExpression} from '@genrojs/toolbox';

const read = name => JSON.parse(readFileSync(new URL(`../../tests/data/${name}`, import.meta.url), 'utf8'));
const corpus = read('period_parser_corpus.json');
const divergences = read('period_parser_divergences.json');
const key = item => JSON.stringify([item.text, item.locale, item.workdate]);
const corrections = new Map(divergences.cases.map(item => [key(item), item]));
const cases = corpus.cases.map(item => corrections.get(key(item)) ?? item);

test('every divergence refers to a corpus case', () => {
    const keys = new Set(corpus.cases.map(key));
    for (const item of divergences.cases) assert.ok(keys.has(key(item)), key(item));
});

for (const item of cases) {
    test(`corpus ${key(item)}`, () => {
        const result = parseDateExpression(item.text, {workdate: item.workdate, locale: item.locale});
        if ('error' in item) assert.equal(result.ok, false, JSON.stringify(result));
        else {
            assert.equal(result.ok, true, JSON.stringify(result));
            const dates = result.kind === 'date' ? [result.date, result.date] : [result.start, result.end];
            assert.deepEqual(dates, [item.start, item.end]);
        }
    });
}
