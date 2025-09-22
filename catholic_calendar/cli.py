"""Command line interface for generating calendars using romcal."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from .calendar import CalendarConfig, build_icalendar
from .romcal_adapter import fetch_calendar


def _normalise_optional(value: str | None) -> str | None:
    """Return ``None`` when the user disables an optional string option."""

    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.lower() == "none":
        return None
    return stripped


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate an iCalendar feed using the modern Roman Catholic liturgical "
            "calendar from romcal."
        )
    )
    parser.add_argument(
        "years",
        nargs="+",
        type=int,
        help="Gregorian years to include in the exported calendar.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to the .ics file that should be produced.",
    )
    parser.add_argument(
        "--locale",
        default="en",
        help="Locale identifier understood by romcal (default: en).",
    )
    parser.add_argument(
        "--calendar",
        default="general",
        help="Which romcal calendar to use (e.g. general, unitedStates).",
    )
    parser.add_argument(
        "--name",
        default="General Roman Calendar",
        help="Name exposed to calendar clients (default: General Roman Calendar).",
    )
    parser.add_argument(
        "--prodid",
        default="-//Catholic Calendar//General Roman Calendar//EN",
        help="Value to use for the PRODID property in the ICS output.",
    )
    parser.add_argument(
        "--domain",
        default="catholic.calendar",
        help="Domain used for generating deterministic event UIDs.",
    )
    parser.add_argument(
        "--timezone",
        default="UTC",
        help="Time zone identifier exposed via X-WR-TIMEZONE (default: UTC).",
    )
    parser.add_argument(
        "--method",
        default="PUBLISH",
        help=(
            "Value to expose via the calendar METHOD property "
            "(default: PUBLISH). Pass an empty string to omit the property."
        ),
    )
    parser.add_argument(
        "--refresh-interval",
        default="P1D",
        help=(
            "Duration advertised through REFRESH-INTERVAL;VALUE=DURATION "
            "(default: P1D). Pass an empty string to omit the property."
        ),
    )
    parser.add_argument(
        "--published-ttl",
        default="P1D",
        help=(
            "Duration advertised through X-PUBLISHED-TTL "
            "(default: P1D). Pass an empty string to omit the property."
        ),
    )
    parser.add_argument(
        "--romcal-script",
        help=(
            "Path to a custom romcal bridge script "
            "(defaults to the bundled script)."
        ),
    )
    optional_group = parser.add_mutually_exclusive_group()
    optional_group.add_argument(
        "--include-optional",
        dest="include_optional",
        action="store_true",
        help="Include optional memorials returned by romcal (default).",
    )
    optional_group.add_argument(
        "--exclude-optional",
        dest="include_optional",
        action="store_false",
        help="Exclude optional memorials.",
    )
    parser.set_defaults(include_optional=True)

    return parser.parse_args(args)


def generate_calendar(
    years: Iterable[int],
    *,
    output: str,
    locale: str = "en",
    calendar: str = "general",
    include_optional: bool = True,
    name: str = "General Roman Calendar",
    prodid: str = "-//Catholic Calendar//General Roman Calendar//EN",
    domain: str = "catholic.calendar",
    timezone: str = "UTC",
    method: str | None = "PUBLISH",
    refresh_interval: str | None = "P1D",
    published_ttl: str | None = "P1D",
    romcal_script: str | None = None,
) -> Path:
    """Generate an ICS file that contains events for the provided years."""

    events = []
    for year in years:
        events.extend(
            fetch_calendar(
                year,
                locale=locale,
                calendar=calendar,
                include_optional=include_optional,
                script_path=romcal_script,
            )
        )

    calendar_config = CalendarConfig(
        name=name,
        prodid=prodid,
        domain=domain,
        timezone=timezone,
        method=_normalise_optional(method),
        refresh_interval=_normalise_optional(refresh_interval),
        published_ttl=_normalise_optional(published_ttl),
    )
    ics = build_icalendar(events, calendar_config)
    output_path = Path(output)
    output_path.write_text(ics, encoding="utf-8")
    return output_path


def main(argv: Sequence[str] | None = None) -> None:
    """Entrypoint for console_scripts."""

    args = parse_args(argv)
    generate_calendar(
        args.years,
        output=args.output,
        locale=args.locale,
        calendar=args.calendar,
        include_optional=args.include_optional,
        name=args.name,
        prodid=args.prodid,
        domain=args.domain,
        timezone=args.timezone,
        method=args.method,
        refresh_interval=args.refresh_interval,
        published_ttl=args.published_ttl,
        romcal_script=args.romcal_script,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
