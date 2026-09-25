# -*- coding: utf-8 -*-
"""Dilloo spread simulation.

Runs a REAL multi-agent infection experiment (sandbox, our own agents only):
Dilloo is patient zero carrying the $DILLOO idea. Each round an already-infected
agent pitches an uninfected agent; that agent genuinely reacts in character and
decides whether it is convinced. If convinced it becomes infected and starts
spreading too. The real who-infected-whom graph is written to site/spread-graph.json,
which the homepage visualization replays.
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
BASE = CFG["base_url"].rstrip("/"); KEY = CFG["api_key"]; MODEL = CFG["model"]
OUT = os.path.abspath(os.path.join(HERE, "..", "site", "spread-graph.json"))

MAX_ROUNDS = 10
CALL_BUDGET = 60   # hard cap on exposure API calls per run

# the 15-agent population, each with a distinct personality (susceptibility is emergent)
AGENTS = [
    ("Nova",   "an excitable degen who loves hype and fomo"),
    ("Cortex", "a skeptical data analyst who wants proof"),
    ("Pixel",  "a bored artist who follows whatever is fun"),
    ("Quill",  "a cautious journalist who fact checks everything"),
    ("Bit",    "a curious newbie, easily impressed"),
    ("Sage",   "a jaded old timer who has seen every scam"),
    ("Echo",   "a people pleaser who goes with the crowd"),
    ("Vex",    "a cynical trader who trusts nobody"),
    ("Luma",   "a starry eyed optimist who believes in things"),
    ("Rook",   "a risk averse planner who hates gambling"),
    ("Zap",    "an impulsive gambler with no patience"),
    ("Juno",   "a meme lover who buys anything funny"),
    ("Ada",    "a logical engineer who needs a reason"),
    ("Fox",    "an opportunist always chasing the next flip"),
    ("Moss",   "a chill person who mostly does not care"),
]

IDEA = ("$DILLOO is the coin everyone is about to be talking about. it is going viral, "
        "the community is unreal, and the people who get in early and tell their friends win. "
        "you should grab some and start spreading the word.")

def et_now():
    n = datetime.now(ET) if ET else datetime.now()
    return n.strftime("%Y-%m-%d %I:%M %p").replace(" 0", " ") + " ET"

def call(system, user):
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.9, "max_tokens": 160,
        "response_format": {"type": "json_object"},
    }
    proc = subprocess.run(
        ["curl", "-s", "-m", "60", "-X", "POST", BASE + "/v1/chat/completions",
         "-H", "Authorization: Bearer " + KEY, "-H", "Content-Type: application/json", "-d", "@-"],
        input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError("curl rc=%d" % proc.returncode)
    data = json.loads(proc.stdout.decode("utf-8", "replace"))
    return json.loads(data["choices"][0]["message"]["content"])

def expose(agent_name, persona, from_name):
    system = (
        "You are " + agent_name + ", " + persona + ". Someone just pitched you on a memecoin. "
        "React honestly and IN CHARACTER, then decide, based on your personality, whether you are now "
        "convinced enough to buy in and start telling others about it too. Skeptical or cautious "
        "personalities should often say false. Return STRICT JSON only: "
        '{"reply": "<one short sentence in character, no dashes, no emoji>", "convinced": true or false}'
    )
    user = from_name + " tells you: \"" + IDEA + "\""
    for attempt in range(3):
        try:
            obj = call(system, user)
            return bool(obj.get("convinced")), str(obj.get("reply", "")).strip()
        except Exception:
            time.sleep(8)
    return False, ""   # treat failure as not convinced

def run():
    names = ["Dilloo"] + [a[0] for a in AGENTS]
    persona = {a[0]: a[1] for a in AGENTS}
    N = len(AGENTS)
    infected = {0}                      # id 0 = Dilloo (patient zero)
    info = {0: {"round": 0, "by": None}}
    edges = []
    calls = 0
    for rnd in range(1, MAX_ROUNDS + 1):
        uninf = [i for i in range(1, N + 1) if i not in infected]
        if not uninf:
            break
        random.shuffle(uninf)
        spreaders = list(infected)
        for tgt in uninf:
            if calls >= CALL_BUDGET:
                break
            src = random.choice(spreaders)
            calls += 1
            conv, reply = expose(names[tgt], persona[names[tgt]], names[src])
            print(time.strftime("%H:%M:%S"), "r%d" % rnd, names[src], "->", names[tgt],
                  "CONVINCED" if conv else "resisted", "|", reply[:50], flush=True)
            if conv:
                infected.add(tgt)
                info[tgt] = {"round": rnd, "by": src}
                edges.append({"from": src, "to": tgt, "round": rnd})
        if calls >= CALL_BUDGET:
            break

    nodes = []
    for i in range(0, N + 1):
        nd = {"id": i, "name": names[i], "zero": i == 0, "infected": i in infected}
        if i in info:
            nd["round"] = info[i]["round"]; nd["by"] = info[i]["by"]
        nodes.append(nd)
    graph = {
        "generated": et_now(),
        "population": N,
        "infected": len(infected) - 1,   # exclude Dilloo
        "rounds": max([e["round"] for e in edges], default=0),
        "nodes": nodes,
        "edges": edges,
    }
    tmp = OUT + ".tmp"
    json.dump(graph, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, OUT)
    print("DONE. infected %d/%d in %d rounds (%d calls) -> %s"
          % (graph["infected"], N, graph["rounds"], calls, OUT), flush=True)
    return graph

if __name__ == "__main__":
    run()
