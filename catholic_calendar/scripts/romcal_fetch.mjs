#!/usr/bin/env node

import process from 'node:process';

function parseArgs(argv) {
  const result = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const entry = argv[index];
    if (!entry.startsWith('--')) continue;
    const key = entry.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) {
      result.set(key, true);
      continue;
    }
    result.set(key, next);
    index += 1;
  }
  return result;
}

function normaliseValue(value) {
  if (value === null || value === undefined) return undefined;
  if (Array.isArray(value)) {
    return value
      .map((item) => normaliseValue(item))
      .filter((item) => item !== undefined);
  }
  if (value && typeof value === 'object') {
    if (typeof value.toISODate === 'function') {
      return value.toISODate();
    }
    if (typeof value.toISO === 'function') {
      return value.toISO({ suppressMilliseconds: true });
    }
    if ('name' in value && Object.keys(value).length === 1) {
      return value.name;
    }
    const clone = {};
    for (const [key, val] of Object.entries(value)) {
      const normalised = normaliseValue(val);
      if (normalised !== undefined) clone[key] = normalised;
    }
    return clone;
  }
  return value;
}

function pickCalendarModule(calendarModule, calendarName) {
  if (!calendarModule) return undefined;
  if (!calendarName || calendarName === 'general') {
    return (
      calendarModule.GeneralRomanCalendar ||
      calendarModule.GeneralRomanCalendarV2 ||
      calendarModule.RomanCalendar
    );
  }
  const normalised = calendarName.toLowerCase();
  const matchingKey = Object.keys(calendarModule).find((key) =>
    key.toLowerCase() === `${normalised}calendar` ||
    key.toLowerCase() === `${normalised}`
  );
  if (matchingKey) return calendarModule[matchingKey];
  return pickCalendarModule(calendarModule, 'general');
}

function normaliseDay(day) {
  const normalised = {
    date: normaliseValue(day.date || day.moment || day.startOfDay),
    name: day.name || day.title || day.celebration || day.id,
    rank: normaliseValue(day.rank),
    rankName: day.rankName || (day.rank && day.rank.name) || undefined,
    slug: day.slug || day.id || day.identifier,
    liturgicalColor:
      normaliseValue(day.liturgicalColor || day.liturgicalColors || day.color) || undefined,
    isHolyDayOfObligation: Boolean(day.isHolyDayOfObligation),
    isOptional: Boolean(day.isOptional || day.optional),
    season: normaliseValue(day.season || day.liturgicalSeason) || undefined,
    type: normaliseValue(day.type || day.liturgicalType || day.category) || undefined,
    week: normaliseValue(day.week || day.liturgicalWeek) || undefined,
    metadata: normaliseValue(day.metadata || day.meta || day.sources) || undefined,
    commemorations:
      normaliseValue(day.commemorations || day.secondaryCelebrations || day.memorials) ||
      undefined,
    note: day.note || day.notes || undefined,
  };

  if (day.isHolyDayOfObligation === undefined && day.obligation !== undefined) {
    normalised.isHolyDayOfObligation = Boolean(day.obligation);
  }
  if (day.isOptional === undefined && day.optional !== undefined) {
    normalised.isOptional = Boolean(day.optional);
  }
  return normalised;
}

async function generateWithCore(options) {
  const core = await import('@romcal/core');
  const calendars = await import('@romcal/calendar');
  if (!core || !core.Romcal) {
    throw new Error('romcal core module does not expose a Romcal class.');
  }
  const CalendarClass = pickCalendarModule(calendars, options.calendar);
  const romcal = new core.Romcal({
    calendars: { primary: CalendarClass },
    localization: { locale: options.locale },
    allowOptionalMemorials: options.includeOptional,
  });
  const calendar = await romcal.generateCalendar({ year: options.year });
  return Array.from(calendar).map((day) => normaliseDay(day));
}

async function generateWithLegacy(options) {
  const legacyModule = await import('romcal');
  const LegacyRomcal = legacyModule.default || legacyModule.Romcal || legacyModule;
  const romcal = new LegacyRomcal({
    calendar: options.calendar,
    localization: { locale: options.locale },
    year: options.year,
    allowOptionalMemorials: options.includeOptional,
  });
  const calendar = await romcal.generateCalendar(options.year);
  const flatten = (value) => {
    if (!value) return [];
    if (Array.isArray(value)) return value.flatMap((item) => flatten(item));
    if (typeof value === 'object') {
      if ('date' in value || 'moment' in value) return [value];
      return Object.values(value).flatMap((item) => flatten(item));
    }
    return [];
  };
  return flatten(calendar).map((day) => normaliseDay(day));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const year = Number.parseInt(args.get('year') ?? new Date().getFullYear(), 10);
  if (Number.isNaN(year)) {
    console.error('The --year argument must be a number.');
    process.exit(1);
  }
  const locale = args.get('locale') ?? 'en';
  const calendar = args.get('calendar') ?? 'general';
  const includeOptional = !args.has('no-optional');

  const options = { year, locale, calendar, includeOptional };

  try {
    const events = await generateWithCore(options);
    process.stdout.write(`${JSON.stringify(events)}\n`);
    return;
  } catch (coreError) {
    try {
      const events = await generateWithLegacy(options);
      process.stdout.write(`${JSON.stringify(events)}\n`);
    } catch (legacyError) {
      console.error(
        'Unable to execute romcal. Ensure that @romcal/core and romcal are installed.',
      );
      console.error(coreError?.message);
      console.error(legacyError?.message);
      process.exit(1);
    }
  }
}

main();
