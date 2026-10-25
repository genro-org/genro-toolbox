/** Natural-language civil dates and periods, independent of DOM, clock and timezone. */
export interface DateExpressionOptions {
    /** Required Gregorian civil ISO date, YYYY-MM-DD (0001–9999). */
    workdate: string;
    /** Supported Italian/English locale; defaults to it-IT. */
    locale?: string;
    /** Integer 0–99, default 20. Inclusive window [work year + ahead - 100, work year + ahead - 1]. */
    twoDigitYearAhead?: number;
}
export type DateExpressionErrorCode = 'INVALID_CONTEXT' | 'INVALID_INPUT' |
    'UNRECOGNIZED_EXPRESSION' | 'INVALID_DATE' |
    'INVALID_RANGE';
export type DateExpressionResult =
    {ok: true; kind: 'date'; date: string} |
    {ok: true; kind: 'period'; start: string | null; end: string | null} |
    {ok: false; error: {code: DateExpressionErrorCode; message: string}};
/** Parse a complete expression without reading or modifying page state. */
export function parseDateExpression(text: string, options: DateExpressionOptions): DateExpressionResult;
