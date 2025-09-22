#!/usr/bin/env node

import process from 'node:process';
import pkg from 'romcal';
const { calendarFor } = pkg;

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

// normalize romcal events to include "date"
function normaliseEvents(events) {
  return events.map(ev => {
    if (ev.moment && !ev.date) {
      return { ...ev, date: ev.moment };
    }
    return ev;
  });
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

  try {
    const events = await calendarFor({ year, locale, calendar });
    const normalised = normaliseEvents(events);

    process.stdout.write(`${JSON.stringify(normalised)}\n`);
  } catch (err) {
    console.error('Unable to execute romcal.');
    console.error(err?.message);
    process.exit(1);
  }
}

main();
