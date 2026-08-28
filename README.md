# dogg-radio — a federated node of the global tick network

**Emergency comms, per tick: the public NOAA Weather Radio / FRS-GMRS / marine / aviation
/ CB frequency plan, plus a live count of active NWS alerts for Georgia.**

This repo keeps its own append-only chain of rapp/1 frames in `radio/`. Every half
hour a GitHub Action reads the current tick anchor from the spine at
[kody-w/dogg](https://github.com/kody-w/dogg) and appends one frame of this node's
outlook, referencing that tick — so this chain joins every other node's data on the
same clock. "Right now" APIs only serve the present; the network keeps every present.

## What it carries

- **NOAA Weather Radio (NWR/All Hazards)** — the 7 fixed VHF channels, 162.400–162.550
  MHz. Public FCC/NOAA channel plan, unchanged for decades.
- **FRS/GMRS** — the 22-channel table (462/467 MHz band) from 47 CFR Part 95.
- **Marine VHF channel 16** — 156.800 MHz, the international distress/safety/calling
  channel.
- **Aviation emergency guard** — 121.500 MHz, the civil aviation guard frequency.
- **CB channel 9** — 27.065 MHz, the 27 MHz Citizens Band emergency/traveler channel.
- **Active NWS alerts for Georgia** — a live count pulled from
  `https://api.weather.gov/alerts/active?area=GA` (no key required; a `User-Agent`
  header is sent per NWS API policy).

## Why it matters

Frequencies don't change — they're the one piece of emergency-comms information that
is genuinely useful printed on paper, memorized, or sitting in an offline cache when
the network that would normally answer this question is exactly the thing that's down.
This node exists so that fact has a verifiable, append-only, timestamped home next to
the rest of the tick network — cross-referenceable with every other node on the same
spine tick, instead of living only in a PDF nobody can find at 2am.

## Precision & limits

- The frequency constants are exact as published by FCC/NOAA; they do not change
  release to release and are not re-derived from any API — they're recorded, not
  fetched.
- The alert count is a snapshot at fetch time for the state of Georgia only; it is a
  *count*, not the alert text, area, or severity — use it as a trigger to go check
  official channels, not as the alert itself.
- **This is not a substitute for a licensed radio operator, a real NOAA Weather Radio
  receiver, or official NWS/FCC guidance.** FRS/GMRS transmission requires following
  Part 95 rules (GMRS additionally requires an FCC license); this repo publishes the
  public channel plan only — it grants no license and transmits nothing.

**Verify it yourself:** `python3 tools/verify_thread.py` re-checks every frame with the
reference implementation from [kody-w/rapp-1](https://github.com/kody-w/rapp-1). CI runs
the same oracle on every push.

**Start your own node:** fork this repo, edit `THEME` / `STREAM` / `SOURCES` at the top
of `tools/collect.py` (keyless https APIs, small factual payloads, numbers as strings),
and enable the scheduled workflow. Your chain, your outlook, same clock — announce it on
the spine's registry ([kody-w/dogg](https://github.com/kody-w/dogg) issues) so agents
can find it.

## Trust

<!--trust-->
No ratings yet — used this chain? [Rate it](../../issues/new?template=rate.yml): valid ratings publish automatically as verifiable frames.
<!--/trust-->
