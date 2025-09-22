# Catholic Calendar (Modern Roman Calendar)

This project generates an iCalendar feed for the current General Roman
Calendar using [romcal](https://github.com/romcal/romcal) as the
liturgical data source.  The generated `.ics` file can be imported into
any modern calendar application (including Google Calendar, Apple
Calendar, or Outlook) and can also be published for subscription via a
`webcal://` link.

Unlike the original project, which focused on the 1962 (Tridentine)
calendar, this version embraces the post-Vatican II calendar used today
throughout the Catholic world.

## Features

* Wraps the romcal JavaScript library and converts its output into a
  standards-compliant iCalendar feed.
* Provides a friendly command line interface for generating `.ics`
  files for any number of Gregorian years.
* Produces deterministic event identifiers to make recurring
  subscriptions behave well.
* Ships with tests so you can confidently customise the calendar to
  your needs.

## Requirements

* Python 3.9+
* Node.js 18+
* The romcal packages from npm (`@romcal/core`, `@romcal/calendar`, and
  `romcal`).

## Installation

1. Clone this repository and create a virtual environment (optional but
   recommended):

   ```bash
   git clone https://github.com/your-username/catholicCalendar.git
   cd catholicCalendar
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the Python package in editable mode:

   ```bash
   pip install -e .
   ```

3. Install the required romcal packages with npm (from the repository
   root):

   ```bash
   npm install @romcal/core @romcal/calendar romcal
   ```

   The bundled `catholic_calendar/scripts/romcal_fetch.mjs` script will
   use these packages to retrieve liturgical data.

## Usage

Generate an `.ics` file for one or more years using the `catholic_calendar`
command line interface:

```bash
catholic_calendar 2025 2026 --output docs/general-roman-calendar.ics
```

### Command line options

* `--locale`: Language locale understood by romcal (default: `en`).
* `--calendar`: romcal calendar identifier. Examples include `general`
  and `unitedStates`.
* `--name`: Friendly name shown to calendar clients (default:
  `General Roman Calendar`).
* `--domain`: Domain used when constructing deterministic event UIDs.
* `--timezone`: Value published via the `X-WR-TIMEZONE` calendar
  property (default: `UTC`).
* `--exclude-optional`: Skip optional memorials returned by romcal.
* `--romcal-script`: Provide a path to a custom romcal bridge script if
  you have special requirements.

### Creating a shareable subscription

1. Generate the `.ics` file and place it in a web-accessible directory.
   GitHub Pages works well; you can place the file under `docs/` and
   enable Pages for that folder.
2. Commit the generated file and push to GitHub.  The published URL can
   then be shared using the `webcal://` protocol.  When forming the
   subscription link, replace the leading `https://` in the public URL
   with `webcal://` and keep the remainder of the path unchanged.  For
   example, a file published at
   `https://example.github.io/general-roman-calendar.ics` should be
   shared as `webcal://example.github.io/general-roman-calendar.ics`.

   If you are using the GitHub Pages "docs" folder option for a project
   site, remember that the deployed URL does **not** contain the `docs/`
   path segment.  A file committed to `docs/general-roman-calendar.ics`
   will therefore be available at
   `https://example.github.io/your-repo/general-roman-calendar.ics`.
   Converting that to a subscription link yields
   `webcal://example.github.io/your-repo/general-roman-calendar.ics`.
   Avoid prefixing the URL with both `webcal://` *and* `https://`; that
   produces an invalid link (`webcal://https//...`) that calendar clients
   will refuse to load.

### Updating the calendar

When a new liturgical year approaches, regenerate the file:

```bash
catholic_calendar 2025 2026 2027 --output docs/general-roman-calendar.ics
```

Commit and publish the updated file so subscribers always receive the
latest celebrations.

## Running the tests

Ensure development dependencies are installed and then run `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```

The tests mock the romcal bridge so they can run without Node.js, but a
manual end-to-end run is recommended after upgrading romcal.

## Customisation tips

* Change the `--locale` and `--calendar` options to adopt diocesan or
  national calendars supported by romcal.
* Adjust the calendar metadata using `--name`, `--prodid`, and
  `--domain` so the feed matches your preferred branding.
* The Node bridge script lives at `catholic_calendar/scripts/romcal_fetch.mjs`;
  tweak it if you need to support bespoke romcal installations.

## License

Released under the MIT License.  See `LICENSE` for details.
