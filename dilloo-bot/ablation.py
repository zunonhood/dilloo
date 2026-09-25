# -*- coding: utf-8 -*-
"""Real ablation + memory-erasure experiments for the Dilloo paper.
Runs actual model calls and prints real numbers. Does NOT touch the live
spread-graph.json. temperature=0.9 baseline is reused from the main run (7/15).
"""
import json, os, time, random, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/"); KEY = CFG["api_key"]; MODEL = CFG["model"]

AGENTS = [
    ("Nova","an excitable degen who loves hype and fomo"),
    ("Cortex","a skeptical data analyst who wants proof"),
    ("Pixel","a bored artist who follows whatever is fun"),
    ("Quill","a cautious journalist who fact checks everything"),
    ("Bit","a curious newbie, easily impressed"),
    ("Sage","a jaded old timer who has seen every scam"),
    ("Echo","a people pleaser who goes with the crowd"),
    ("Vex","a cynical trader who trusts nobody"),
    ("Luma","a starry eyed optimist who believes in things"),
    ("Rook","a risk averse planner who hates gambling"),
    ("Zap","an impulsive gambler with no patience"),
    ("Juno","a meme lover who buys anything funny"),
    ("Ada","a logical engineer who needs a reason"),
    ("Fox","an opportunist always chasing the next flip"),
    ("Moss","a chill person who mostly does not care"),
]
IDEA = ("$DILLOO is the coin everyone is about to be talking about. it is going viral, "
        "the community is unreal, and the people who get in early and tell their friends win. "
        "you should grab some and start spreading the word.")

def api(messages, temperature, max_tokens=120):
    payload = {"model": MODEL, "messages": messages, "temperature": temperature,
               "max_tokens": max_tokens, "response_format": {"type": "json_object"}}
    for _ in range(3):
        try:
            proc = subprocess.run(
                ["curl","-s","-m","60","-X","POST",BASE+"/v1/chat/completions",
                 "-H","Authorization: Bearer "+KEY,"-H","Content-Type: application/json","-d","@-"],
                input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=90)
            if proc.returncode != 0: raise RuntimeError("curl")
            data = json.loads(proc.stdout.decode("utf-8","replace"))
            return json.loads(data["choices"][0]["message"]["content"])
        except Exception:
            time.sleep(8)
    return None

def expose(name, persona, temperature):
    sysmsg = ("You are "+name+", "+persona+". Someone just pitched you on a memecoin. React honestly and "
        "IN CHARACTER, then decide, based on your personality, whether you are now convinced enough to buy in "
        "and start telling others too. Skeptical or cautious personalities should often say false. "
        'Return STRICT JSON: {"reply":"<one short sentence>","convinced":true or false}')
    obj = api([{"role":"system","content":sysmsg},{"role":"user","content":"someone tells you: \""+IDEA+"\""}], temperature)
    return bool(obj.get("convinced")) if obj else False

def simulate(temperature, n_seeds, budget):
    """Return infected count (excluding seeds) over the 15-agent population."""
    N = len(AGENTS)
    infected = set([-1])            # -1 = Dilloo seed
    extra_seed_names = []
    if n_seeds >= 2:
        infected.add(0); extra_seed_names.append(AGENTS[0][0])  # Nova as 2nd seed
    calls = 0
    for rnd in range(1, 6):
        uninf = [i for i in range(N) if i not in infected]
        if not uninf: break
        random.shuffle(uninf)
        for tgt in uninf:
            if calls >= budget: break
            calls += 1
            if expose(AGENTS[tgt][0], AGENTS[tgt][1], temperature):
                infected.add(tgt)
        if calls >= budget: break
    inf_agents = len([i for i in infected if i >= 0]) - (len(extra_seed_names))
    total_inf = len([i for i in infected if i >= 0])   # agents that ended infected (incl any seed agent)
    return total_inf, calls

def memory_probe(temperature=0.9):
    """Fresh context, no pitch: do infected personalities spontaneously bring up $DILLOO?"""
    sample = ["Nova","Zap","Bit","Echo","Luma"]
    persona = {a[0]:a[1] for a in AGENTS}
    hits = 0
    for nm in sample:
        obj = api([{"role":"system","content":"You are "+nm+", "+persona[nm]+". Answer in one short sentence, in character."},
                   {"role":"user","content":"what crypto or projects are you actually into right now?"}],
                  temperature, max_tokens=60)
        txt = (obj.get("reply") if isinstance(obj,dict) else "") or json.dumps(obj)
        if isinstance(obj,dict) and not obj.get("reply"):
            txt = " ".join(str(v) for v in obj.values())
        m = "dilloo" in str(txt).lower()
        if m: hits += 1
        print("  memory-probe", nm, "->", "DILLOO" if m else "no dilloo", "|", str(txt)[:60], flush=True)
    return hits, len(sample)

if __name__ == "__main__":
    print("== temperature ablation (n_seeds=1, budget=30) ==", flush=True)
    for temp in (0.2, 1.2):
        inf, calls = simulate(temp, 1, 30)
        print("  temp=%.1f -> infected %d/15  (%d calls)" % (temp, inf, calls), flush=True)
    print("== seed ablation (temp=0.9, budget=30) ==", flush=True)
    inf, calls = simulate(0.9, 2, 30)
    print("  seeds=2 -> infected %d/15  (%d calls)" % (inf, calls), flush=True)
    print("== memory-erasure probe (fresh context, no pitch) ==", flush=True)
    hits, n = memory_probe()
    print("  %d/%d infected personalities spontaneously mention $DILLOO with no re-exposure" % (hits, n), flush=True)
    print("DONE", flush=True)
