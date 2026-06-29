# astro-events

An AI agent that, **every morning (around 07:00 Europe/Rome)**, works out which
interesting astronomical objects are visible over the next few nights from
**Bevagna (PG), Italy** with a **Celestron Inspire 80AZ** (80 mm refractor),
checks whether the **sky will be clear**, and sends a **Telegram** notification
with a `in 3 nights → in 2 nights → tomorrow → tonight` countdown.

It is not a web-scraping agent: visibility is *computed* with real ephemerides,
so the results are specific to your location, your telescope, and the actual
weather forecast.

## How it works

| Stage | Tooling |
|------|---------|
| What's above the horizon, when, and how high | **Skyfield** + the `de421` ephemeris (Sun, Moon, planets) and a curated deep-sky/double-star catalogue suited to an 80 mm scope |
| Is the sky clear? | **Open-Meteo** hourly cloud-cover forecast (free, no key) |
| Time-sensitive extras (comets, aurora, meteor peaks) | **Tavily** search |
| Writing the message | **Claude** (`claude-opus-4-8` by default) with a plain-text fallback |
| Delivery | **Telegram** bot |
| Runs daily, free | **GitHub Actions** (cron) |

Each morning the agent looks at **tonight + the next 3 nights**. A target that is
well-placed *and* under a clear sky on a given night is therefore announced on
the three mornings before it and again on the night itself. A small
`agent/state/seen.json` file (committed back to the repo by the workflow)
remembers what was already sent so you get each countdown step exactly once.

## Setup

### 1. Get the credentials (put them in GitHub repo secrets)

`Settings → Secrets and variables → Actions → New repository secret`:

| Secret | Where to get it | Cost |
|--------|-----------------|------|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | pay-per-use (pennies/day) |
| `TAVILY_API_KEY` | app.tavily.com → sign up → API key | free tier (~1,000/mo) |
| `TELEGRAM_BOT_TOKEN` | Telegram → message **@BotFather** → `/newbot` | free |
| `TELEGRAM_CHAT_ID` | see below | free |

To get `TELEGRAM_CHAT_ID`: message your new bot once ("hi"), then run locally:

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC..."; python -m agent.get_chat_id
```

### 2. That's it

The workflow [.github/workflows/daily.yml](.github/workflows/daily.yml) is already
configured. Once the secrets are set, it runs automatically. To test it now:
**Actions → Daily astro-events → Run workflow** (the manual run forces execution
regardless of the time-of-day guard).

> **On timing:** GitHub's cron is UTC and best-effort — scheduled runs often
> start a few minutes late and occasionally much later. The agent does **not**
> gate on the clock, so a late start still sends the alert. Two crons fire each
> morning (05:07 & 06:07 UTC ≈ 07:07 CEST / 06:07 CET) for redundancy; the
> dedup state means you still get exactly one notification per day.
>
> Note: GitHub also disables scheduled workflows after 60 days of repo
> inactivity. The daily state commit keeps the repo active, so that won't bite.

## Run locally

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ASTRO_FORCE="1"                # re-send even if already notified (ignore dedup)
$env:TELEGRAM_BOT_TOKEN="..."; $env:TELEGRAM_CHAT_ID="..."
$env:ANTHROPIC_API_KEY="..."; $env:TAVILY_API_KEY="..."   # optional
python -m agent.main
```

With no Telegram secrets set, the message is printed to the console instead of
sent — handy for a dry run. With no `ANTHROPIC_API_KEY`, a built-in plain
formatter writes the message instead of Claude.

## Tuning

Everything is overridable via environment variables (see
[agent/config.py](agent/config.py)). The most useful:

| Variable | Default | Meaning |
|----------|---------|---------|
| `ASTRO_DSO_MAG_LIMIT` | `9.5` | faintest deep-sky object to consider |
| `ASTRO_MIN_ALT_DSO` | `25` | minimum culmination altitude for deep-sky targets (°) |
| `ASTRO_CLOUD_CLEAR_PCT` | `30` | mean night-time cloud cover counted as "clear" (%) |
| `ASTRO_MAX_HIGHLIGHTS` | `7` | max targets listed per night |
| `ASTRO_LANG` | `en` | output language — ISO code (`it`, `es`, `fr`, `de`, `pt`, `ja`, …) or a plain language name (`Swedish`, `Português`). Any language Claude speaks works |
| `ASTRO_MODEL` | `claude-opus-4-8` | Claude model (e.g. `claude-haiku-4-5` to cut cost) |
| `ASTRO_LAT` / `ASTRO_LON` / `ASTRO_ELEVATION_M` | Bevagna | observer location |

To add targets, edit the `_ROWS` table in [agent/catalog.py](agent/catalog.py)
(name, J2000 RA°, Dec°, magnitude, kind, difficulty, description).
