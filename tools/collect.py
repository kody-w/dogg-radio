#!/usr/bin/env python3
"""A federated tick-network node: this repo's own append-only chain, keyed to the
global tick spine at kody-w/dogg.

Every run reads the spine's current tick anchor, takes this node's themed snapshot of
keyless public APIs, and appends one frame referencing that tick. Different repos, run
by different people, each with their own outlook — all joinable on the tick key. To
start your own node: fork this repo, edit THEME/STREAM/SOURCES below, enable the
scheduled workflow. Frames verify with the reference implementation (tools/rapp.py,
from kody-w/rapp-1); CI re-verifies the whole chain on every push.
"""
import json, sys, pathlib, datetime, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rapp as R
import chainio

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPINE_HEAD = "https://raw.githubusercontent.com/kody-w/dogg/main/ticks/HEAD.json"
TIMEOUT = 8

# ---- edit these three for your node -------------------------------------------------
THEME = "radio"                       # also the data directory name
STREAM = "radio:@kody-w/dogg-radio"                        # your stream id (your repo, your name)
# SOURCES: name -> zero-arg callable returning a SMALL dict of facts.
# rapp/1 canonical hashing forbids floats: numeric facts ride as strings or ints.
# -------------------------------------------------------------------------------------

def utc():
    n = datetime.datetime.now(datetime.timezone.utc)
    return n.strftime("%Y-%m-%dT%H:%M:%S.") + f"{n.microsecond // 1000:03d}Z"

def get(url, headers=None):
    hdrs = {"User-Agent": f"tick-node-{THEME}"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())

# NOAA Weather Radio (NWR/NOAA All Hazards) broadcasts on 7 fixed VHF channels in the
# 162.400-162.550 MHz band. Public FCC/NOAA allocation, unchanged since the 1970s-90s
# channel plan — not fetched, just recorded as a constant reference.
NOAA_WX_CHANNELS = {
    "WX1": "162.550", "WX2": "162.400", "WX3": "162.475", "WX4": "162.425",
    "WX5": "162.450", "WX6": "162.500", "WX7": "162.525",
}

# FRS/GMRS channel plan (47 CFR Part 95). Channels 1-7 and 15-22 are shared FRS/GMRS at
# 2W (FRS) / 5W (GMRS licensed); channels 8-14 are FRS-only at 0.5W; channel 1 is also
# the widely used unofficial GMRS/FRS calling/emergency channel. Public FCC allocation.
FRS_GMRS_CHANNELS = {
    "1": "462.5625", "2": "462.5875", "3": "462.6125", "4": "462.6375",
    "5": "462.6625", "6": "462.6875", "7": "462.7125", "8": "467.5625",
    "9": "467.5875", "10": "467.6125", "11": "467.6375", "12": "467.6625",
    "13": "467.6875", "14": "467.7125", "15": "462.5500", "16": "462.5750",
    "17": "462.6000", "18": "462.6250", "19": "462.6500", "20": "462.6750",
    "21": "462.7000", "22": "462.7250",
}

def alerts_ga():
    d = get("https://api.weather.gov/alerts/active?area=GA",
             headers={"Accept": "application/geo+json"})
    return {"active_count": int(len(d.get("features", [])))}

SOURCES = {
    "noaa_wx": lambda: {"band": "162.400-162.550", "unit": "MHz", "channels": NOAA_WX_CHANNELS},
    "frs_gmrs": lambda: {"unit": "MHz", "channels": FRS_GMRS_CHANNELS},
    "marine_vhf": lambda: {"ch16_mhz": "156.800", "note": "international distress/safety/calling"},
    "aviation_guard": lambda: {"mhz": "121.500", "note": "civil aviation emergency guard"},
    "cb": lambda: {"ch9_mhz": "27.065", "note": "27 MHz Citizens Band emergency/traveler channel"},
    "alerts": alerts_ga,
}

def load_chain(d):
    return chainio.load_chain(d)

def main():
    spine = get(SPINE_HEAD)
    tick_n, tick_hash = spine["count"] - 1, spine["head_frame"]
    d = ROOT / THEME
    d.mkdir(exist_ok=True)
    chain = load_chain(d)
    head = chain[-1] if chain else None
    if head is not None and head["payload"].get("tick") == tick_n:
        print(f"{THEME}: tick {tick_n} already recorded — nothing to do")
        return
    data, failed = {}, []
    for name, fn in SOURCES.items():
        try:
            data[name] = fn()
        except Exception:
            failed.append(name)
    # numeric mission fields promoted to the payload top level (all positive magnitudes,
    # numbers as strings/ints per rapp/1 canonicalization — see module docstring)
    frequencies = {
        "noaa_wx_ch1_khz": 162400, "marine_ch16_khz": 156800, "guard_khz": 121500,
    }
    active_alerts_ga = data.get("alerts", {}).get("active_count")
    payload = {"tick": tick_n, "tick_frame": tick_hash, "spine": "kody-w/dogg",
               "fetched_utc": utc(), "frequencies": {**{k: v for k, v in data.items() if k != "alerts"}},
               "alerts": data.get("alerts", {}),
               "active_alerts_ga": active_alerts_ga if active_alerts_ga is not None else 0,
               "noaa_wx_ch1_khz": frequencies["noaa_wx_ch1_khz"],
               "marine_ch16_khz": frequencies["marine_ch16_khz"],
               "guard_khz": frequencies["guard_khz"],
               "sources_failed": failed}
    if head is None:
        payload["about"] = (f"A federated node of the global tick network: this repo's "
                            f"own {THEME} outlook, one frame per observed tick, keyed to "
                            "the spine's tick anchors so it joins every other node's "
                            "data on the same clock.")
    f = R.build_frame(f"{THEME}.snapshot", STREAM, (head["seq"] + 1) if head else 0,
                      utc(), payload, prev=(head["payload_hash"] if head else None))
    ok, step, why = R.verify_frame(f, head=head, stream_id_of_record=STREAM)
    if not ok:
        raise ValueError(f"refusing invalid frame: {step}: {why}")
    chainio.append_frame(d, f, STREAM)
    print(f"{THEME} frame {f['seq']} @ spine tick {tick_n}: {', '.join(data) or 'nothing'}"
          + (f" (failed: {', '.join(failed)})" if failed else ""))

if __name__ == "__main__":
    main()
