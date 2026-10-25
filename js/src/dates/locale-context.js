// Copyright 2026 Softwell S.r.l. - Genro Team
// SPDX-License-Identifier: Apache-2.0
import {locales} from './locales.js';

export function localeContext(locale) {
    if (typeof locale !== 'string') throw new RangeError('A supported locale is required.');
    const tag = locale.replaceAll('-', '_');
    const split = tag.indexOf('_');
    const language = (split < 0 ? tag : tag.slice(0, split)).toLowerCase();
    const region = (split < 0 ? '' : tag.slice(split + 1)).toUpperCase();
    if (!Object.hasOwn(locales, language)) throw new RangeError(`Unsupported locale: ${locale}`);
    const dictionary = locales[language];
    const phrases = key => [...new Set([...dictionary.keywords[key], ...locales.en.keywords[key]])];
    return {dictionary, phrases, order: dictionary.date_order[region] ?? dictionary.date_order.default};
}
