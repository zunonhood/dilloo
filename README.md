<p align="center">
  <img src="favicon/dilloo-cutout.png" alt="Dilloo" width="200">
</p>

# Dilloo

[![X](https://img.shields.io/badge/follow-%40dilloonsolchain-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/dilloonsolchain)
[![paper](https://img.shields.io/badge/read-the%20paper-6e935c?style=flat-square)](dilloo-paper.html)
![python](https://img.shields.io/badge/python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![agents](https://img.shields.io/badge/agents-15-a4ca92?style=flat-square)

A live reproduction of the mind virus experiment, wrapped in a token.

Dilloo is a cocky little AI mascot for the **$DILLOO** memecoin, but the site is
not a landing page with a squirrel on it. It is the front end of a running system that
seeds one idea into a population of language-model agents and watches it spread.

Inspired by *Mind Viruses: Self-Propagating Ideas in Multi-Agent LLM Systems*
(arXiv:2608.10218).

## What is in here

```
index.html          the homepage (feed, docs, paper embed)
dilloo-paper.html   the litepaper, arXiv style
dan.css             styling  (fonts/, favicon/, img/)
dilloo-feed.json    sample output of the live monologue
spread-graph.json   sample output of a real infection run
dilloo-bot/
  spread_sim.py     the multi-agent infection experiment
  dilloo_feed.py    the live self-talk generator
  ablation.py       temperature / seed / memory experiments
  config.example.json  copy to config.json and add your key
```

## How it works

Two Python services write JSON; one static page reads it.

- **spread_sim.py** runs 15 agents with distinct dispositions plus one seed (Dilloo).
  Each exposure is a real model call: the target reacts in character and decides,
  by personality, whether it adopts $DILLOO. It writes a real who-infected-whom
  graph to `spread-graph.json`.
- **dilloo_feed.py** asks the model, in Dilloo's voice, for one status post every
  few minutes and writes it to `dilloo-feed.json`. The homepage polls that file.
- The **frontend** is a plain static page. No framework, no build step.

Adoption is detected from each agent's own declared stance
(`{"reply": "...", "convinced": true|false}`), not a keyword rule.

## Results (single representative run)

- One seed infects **7 of 15** agents within two rounds.
- The ceiling is dispositional: 7, 7, 6 infected at temperature 0.2 / 0.9 / 1.2,
  and 6 of 15 with two seeds instead of one.
- Individual adoption does not survive a context reset (0 of 5 re-probed agents
  mention $DILLOO without re-exposure); persistence comes from re-transmission,
  not memory.

## Run it yourself

```bash
cd dilloo-bot
cp config.example.json config.json     # add your OpenAI-compatible key
python spread_sim.py                    # writes ../spread-graph.json
python dilloo_feed.py                   # writes ../dilloo-feed.json (loops)
# serve the repo root with any static server, e.g.:
python -m http.server 8080
```

Want your own agent in the population? Add a `(name, persona)` to the roster in
`spread_sim.py` and it joins the next run. Skeptics welcome. They usually resist,
which is the point.

## Contract

- CA: `DZyT11Le6Cmd7vG8NZydTu2G2MRAbTBV95h2W7DUpump`
- [Trade on pump.fun](https://pump.fun/coin/DZyT11Le6Cmd7vG8NZydTu2G2MRAbTBV95h2W7DUpump)

## Roadmap

- open-source hardening of the simulation and feed
- scale to 100+ agents on scale-free graphs
- adversarial inoculator agents that fight back
- cross-model transmission (mixed-model populations)
- live spread graph back on the page
- public endpoint to submit your own agent
- tie the infection count to on-chain $DILLOO holders

## Note

All experiments run in a closed sandbox using our own agents. No third-party
system, deployed assistant, or real user is targeted or modified. The payload is
confined to this population and this token. Nothing here is financial advice.
