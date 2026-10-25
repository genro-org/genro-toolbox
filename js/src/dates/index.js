/* @ts-self-types="./index.d.ts" */
// Copyright 2026 Softwell S.r.l. - Genro Team
// SPDX-License-Identifier: Apache-2.0
// Same semantics as src/genro_toolbox/dates/period_parser.py.
import {addDays, civil, monday, monthPeriod, parts, daysInMonth} from './civil.js';
import {localeContext} from './locale-context.js';

const yearPattern = /^(?:\d{4}|\d{2})$/;
const dayPattern = /^\d{1,2}$/;
const fail = (code, message) => ({ok: false, error: {code, message}});
const unrecognized = (code = 'UNRECOGNIZED_EXPRESSION', message = 'Text is not a supported date expression.') => {
    throw Object.assign(new SyntaxError(message), {code});
};
const own = (object, key) => Object.hasOwn(object, key);

function decodeYear(text, context) {
    if (text.length === 4) return Number(text);
    const lowest = context.year + context.twoDigitYearAhead - 100;
    return lowest + ((Number(text) - lowest) % 100 + 100) % 100;
}

function boundTexts(text, context) {
    if (text.includes(';')) {
        const bounds = text.split(';').map(part => part.trim());
        if (bounds.length !== 2) return unrecognized('INVALID_RANGE', 'A range must have exactly two endpoints.');
        return {bounds, range: true};
    }
    if (context.phrases('no_period').includes(text)) return {bounds: ['', ''], range: true};
    const to = context.phrases('to'), from = context.phrases('from');
    for (const word of to) {
        if (text.startsWith(`${word} `)) return {bounds: ['', text.slice(word.length + 1).trim()], range: true};
    }
    for (const word of to) {
        const separator = ` ${word} `;
        if (!text.includes(separator)) continue;
        for (const prefix of from) {
            if (text.startsWith(`${prefix} `)) {
                text = text.slice(prefix.length + 1);
                break;
            }
        }
        const bounds = text.split(separator).map(part => part.trim());
        if (bounds.length !== 2) return unrecognized('INVALID_RANGE', 'A range must have exactly two endpoints.');
        return {bounds, range: true};
    }
    for (const word of from) {
        if (text.startsWith(`${word} `)) return {bounds: [text.slice(word.length + 1).trim(), ''], range: true};
    }
    return {bounds: [text, text], range: false};
}

function keywordDate(text, context, isEnd) {
    const candidates = [[text, 0]];
    const offset = /^(.+?)\s*([+-])\s*(\d+)$/.exec(text);
    if (offset) candidates.push([offset[1], Number(offset[2] + offset[3])]);
    const shifts = {today: 0, yesterday: -1, tomorrow: 1,
        this_week: 0, last_week: -1, next_week: 1,
        this_month: 0, last_month: -1, next_month: 1};
    for (const [body, amount] of candidates) {
        for (const [key, shift] of Object.entries(shifts)) {
            if (!context.phrases(key).includes(body)) continue;
            if (key.endsWith('_week')) return addDays(monday(context.workdate), (shift + amount) * 7 + (isEnd ? 6 : 0));
            if (key.endsWith('_month')) {
                const span = monthPeriod(context.year, context.month, shift + amount);
                return isEnd ? span.end : span.start;
            }
            return addDays(context.workdate, shift + amount);
        }
    }
    return null;
}

function quarter(text, context, isEnd) {
    const entries = Object.entries(context.dictionary.quarters).sort((a, b) => b[0].length - a[0].length);
    for (const [name, number] of entries) {
        let year;
        if (text === name) year = null;
        else if (text.startsWith(name) && yearPattern.test(text.slice(name.length).trim())) {
            year = decodeYear(text.slice(name.length).trim(), context);
        } else if (text.endsWith(name) && yearPattern.test(text.slice(0, -name.length).trim())) {
            year = decodeYear(text.slice(0, -name.length).trim(), context);
        } else continue;
        return {year, month: isEnd ? number * 3 : number * 3 - 2};
    }
    return null;
}

function monthNumber(token, dictionary) {
    if (own(dictionary.months, token)) return dictionary.months[token];
    const match = /^m(\d{1,2})$/.exec(token);
    return match && Number(match[1]) >= 1 && Number(match[1]) <= 12 ? Number(match[1]) : null;
}

function namedMonth(text, context) {
    const tokens = text.split(/\s+/);
    const positions = tokens.map((token, i) => monthNumber(token, context.dictionary) ? i : -1).filter(i => i >= 0);
    if (!positions.length) return null;
    if (positions.length !== 1) return unrecognized();
    const position = positions[0], month = monthNumber(tokens[position], context.dictionary);
    const before = tokens.slice(0, position), after = tokens.slice(position + 1), others = [...before, ...after];
    if (others.length === 1 && context.phrases('last').includes(others[0])) {
        return {year: context.year - (month > context.month ? 1 : 0), month};
    }
    if (others.length === 1 && context.phrases('next').includes(others[0])) {
        return {year: context.year + (month < context.month ? 1 : 0), month};
    }
    if (!others.length) return {year: null, month};
    if (!before.length && after.length === 1 && yearPattern.test(after[0])) return {year: decodeYear(after[0], context), month};
    if (before.length === 1 && dayPattern.test(before[0])) {
        if (!after.length) return civil(context.year, month, Number(before[0]));
        if (after.length === 1 && yearPattern.test(after[0])) return civil(decodeYear(after[0], context), month, Number(before[0]));
    }
    if (!before.length && after.length === 2 && dayPattern.test(after[0]) && yearPattern.test(after[1])) {
        return civil(decodeYear(after[1], context), month, Number(after[0]));
    }
    return unrecognized();
}

function numericDate(text, context) {
    const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
    if (iso) return civil(...iso.slice(1).map(Number));
    const numeric = /^(\d{1,4})[/\-. ]+(\d{1,4})[/\-. ]+(\d{1,4})$/.exec(text);
    const values = {};
    if (numeric) context.order.split('').forEach((letter, i) => { values[letter] = numeric[i + 1]; });
    else if (/^(?:\d{6}|\d{8})$/.test(text)) {
        const yearWidth = text.length === 8 ? 4 : 2;
        for (const letter of context.order) {
            const width = letter === 'Y' ? yearWidth : 2;
            values[letter] = text.slice(0, width);
            text = text.slice(width);
        }
    } else return null;
    if (!yearPattern.test(values.Y) || values.D.length > 2 || values.M.length > 2) return unrecognized();
    let day = Number(values.D), month = Number(values.M);
    if (numeric && month > 12 && day <= 12) [day, month] = [month, day];
    return civil(decodeYear(values.Y, context), month, day);
}

function getBound(text, context, isEnd) {
    if (!text) return null;
    const articles = context.phrases('articles');
    text = text.split(/\s+/).filter(token => !articles.includes(token)).join(' ');
    if (!text) return unrecognized();
    if (yearPattern.test(text)) return civil(decodeYear(text, context), isEnd ? 12 : 1, isEnd ? 31 : 1);
    const value = keywordDate(text, context, isEnd) ?? quarter(text, context, isEnd) ?? namedMonth(text, context);
    if (value !== null) return value;
    if (own(context.dictionary.weekdays, text)) return addDays(monday(context.workdate), context.dictionary.weekdays[text]);
    return numericDate(text, context) ?? unrecognized();
}

function startDate(start, end, context) {
    if (start === null || typeof start === 'string') return start;
    let year = start.year ?? context.year;
    const endYear = typeof end === 'string' ? parts(end)[0] : end?.year;
    const endMonth = typeof end === 'string' ? parts(end)[1] : end?.month;
    if (endYear) {
        if (year > endYear) year = endYear;
        if (year === endYear && start.month > endMonth) year--;
    }
    return civil(year, start.month, 1);
}

function endDate(end, start, context) {
    if (end === null || typeof end === 'string') return end;
    let year = end.year ?? context.year;
    if (start !== null) {
        const [startYear, startMonth] = parts(start);
        if (year < startYear) year = startYear;
        if (year === startYear && startMonth > end.month) year++;
    }
    return civil(year, end.month, daysInMonth(year, end.month));
}

/** Parse a complete date expression using Toolbox semantics and structured JS outcomes. */
export function parseDateExpression(text, options = {}) {
    if (!options || typeof options !== 'object' || Array.isArray(options)) return fail('INVALID_CONTEXT', 'Options must provide a civil workdate and supported locale.');
    let context;
    try {
        const {locale = 'it-IT', workdate, twoDigitYearAhead = 20} = options;
        const [year, month] = parts(workdate);
        if (!Number.isInteger(twoDigitYearAhead) || twoDigitYearAhead < 0 || twoDigitYearAhead > 99) throw new RangeError('twoDigitYearAhead must be an integer from 0 to 99.');
        context = {...localeContext(locale), workdate, year, month, twoDigitYearAhead};
    } catch (error) { return fail('INVALID_CONTEXT', error.message); }
    if (typeof text !== 'string') return fail('INVALID_INPUT', 'Expression must be a string.');
    try {
        const expression = text.toLowerCase().trim().replaceAll(',', '');
        const {bounds, range} = boundTexts(expression, context);
        const right = getBound(bounds[1], context, true), left = getBound(bounds[0], context, false);
        const start = startDate(left, right, context), end = endDate(right, start, context);
        if (!range && typeof left === 'string' && start === end) return {ok: true, kind: 'date', date: start};
        return {ok: true, kind: 'period', start, end};
    } catch (error) {
        if (error instanceof RangeError) return fail('INVALID_DATE', error.message);
        if (error instanceof SyntaxError) return fail(error.code, error.message);
        throw error;
    }
}
