// Copyright 2026 Softwell S.r.l. - Genro Team
// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import {readdirSync, readFileSync} from 'node:fs';
import {locales} from '../src/dates/locales.js';

test('locales.js holds the Python vocabulary (run js/scripts/build-locales.js)', () => {
    const source = new URL('../../src/genro_toolbox/dates/locales/', import.meta.url);
    const expected = {};
    for (const file of readdirSync(source).filter(name => name.endsWith('.json'))) {
        expected[file.slice(0, -'.json'.length)] = JSON.parse(readFileSync(new URL(file, source), 'utf8'));
    }
    assert.deepEqual(locales, expected);
});
