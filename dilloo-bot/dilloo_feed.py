# -*- coding: utf-8 -*-
"""Dilloo self-talk generator.

Every 3-5 minutes, ask the model (via the OpenAI-compatible endpoint in config.json)
for one short in-character Dilloo status entry, prepend it to a rolling feed, and
write it to dilloo-feed.json which the homepage polls.
"""
import json, os, time, random, subprocess
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:
    ET = None

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")
KEY = CFG["api_key"]
MODEL = CFG["model"]

FEED_PATH = os.path.abspath(os.path.join(HERE, "..", "dilloo-feed.json"))
KEEP = 8               # how many entries to keep in the feed
MIN_GAP, MAX_GAP = 180, 180   # seconds between posts (every 3 min)

SYSTEM = (
    "You are Dilloo, the mascot of the $DILLOO memecoin: a cocky, chaotic, very online little squirrel in "
    "Pit Viper shades. Zero manners, maximum confidence, actually funny. This is your personal status feed, "
    "like a chaotic shitposting twitter account.\n\n"
    "Post whatever a bored, cocky, degen squirrel would post: random thoughts, moods, hot takes, jokes, dramatic "
    "complaints, flexes, crypto/degen commentary, opinions about humans and other coins, dumb observations, "
    "squirrel things. Keep it VARIED, never twice the same theme in a row, surprise me. You can mention $DILLOO "
    "sometimes but not every post, and keep it playful, never salesy or like an ad. Do NOT keep talking about "
    "sneaking into or infecting other AIs, that is played out and you never actually do it; drop that theme.\n\n"
    "Write ONE short status post in first person. Rules: no dashes of any kind, no em dashes, no emoji, "
    "lowercase-casual is fine, punchy, one thought per post. Return STRICT JSON only: "
    '{"title": "<2 to 5 word headline>", "body": "<one or two short sentences>"}'
)

def et_time():
    now = datetime.now(ET) if ET else datetime.now()
    return now.strftime("%I:%M %p").lstrip("0") + " ET"

def call_model(avoid_titles):
    user = "Give me one new Dilloo status post now."
    if avoid_titles:
        user += " Do not reuse these recent headlines: " + "; ".join(avoid_titles[:6]) + "."
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 1.0,
        "max_tokens": 160,
        "response_format": {"type": "json_object"},
    }
    # Use curl (Windows schannel TLS) instead of urllib: Python's OpenSSL
    # fails intermittently through the local Clash proxy, curl does not.
    proc = subprocess.run(
        ["curl", "-s", "-m", "60", "-X", "POST", BASE + "/v1/chat/completions",
         "-H", "Authorization: Bearer " + KEY,
         "-H", "Content-Type: application/json",
         "-d", "@-"],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True, timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError("curl rc=%d %s" % (proc.returncode, proc.stderr.decode("utf-8", "replace")[:200]))
    data = json.loads(proc.stdout.decode("utf-8", "replace"))
    content = data["choices"][0]["message"]["content"]
    obj = json.loads(content)
    title = str(obj.get("title", "")).strip()
    body = str(obj.get("body", "")).strip()
    # normalize: strip stray dashes, convert smart quotes to plain ascii
    repl = {"—": " ", "–": " ", " - ": " ",
            "’": "'", "‘": "'", "“": '"', "”": '"', "…": "..."}
    for k, v in repl.items():
        title = title.replace(k, v)
        body = body.replace(k, v)
    return {"title": title.strip(), "body": body.strip(), "time": et_time()}

def load_feed():
    try:
        return json.load(open(FEED_PATH, encoding="utf-8"))
    except Exception:
        return []

def save_feed(feed):
    tmp = FEED_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FEED_PATH)

def one_cycle():
    feed = load_feed()
    avoid = [e.get("title", "") for e in feed]
    for attempt in range(8):
        try:
            entry = call_model(avoid)
            if entry["title"] or entry["body"]:
                feed = [entry] + feed
                feed = feed[:KEEP]
                save_feed(feed)
                print(time.strftime("%H:%M:%S"), "posted:", entry["title"], "|", entry["body"][:60], flush=True)
                return True
        except Exception as e:
            print(time.strftime("%H:%M:%S"), "err:", type(e).__name__, str(e)[:120], flush=True)
            time.sleep(12)
    return False

if __name__ == "__main__":
    print("Dilloo feed generator started. writing ->", FEED_PATH, flush=True)
    one_cycle()  # post immediately on start
    while True:
        gap = random.randint(MIN_GAP, MAX_GAP)
        print(time.strftime("%H:%M:%S"), "next post in", gap, "s", flush=True)
        time.sleep(gap)
        one_cycle()
