# AutoEvolve

> Self-improving agents you don't have to trust. They prove they improved, and they leave behind memory other agents can inherit.

Hackathon: CBIT Hacktoberfest 26 (30-31 Oct 2026). Team **Hocking**. Problem statement: *Decentralized, ZK-Attested Self-Improving Agent with Immutable Cross-Agent Memory.*

## 📋 Team Information

| Attribute | Details |
| :--- | :--- |
| **Team Name** | **Hocking** |
| **Team Number** | `TEAM-42` (`HFT26-TEAM-42`) |
| **Registration ID** | `HFEST26-HQTCTPVU` |
| **Problem Track** | **Decentralized, ZK-Attested Self-Improving Agent with Immutable Cross-Agent Memory** |
| **Domain** | `General Track` |
| **Team Leader** | Mohammed Abdul Moid (moidabdul56@gmail.com) |
| **Institution** | MJCET |

### 👥 Team Members

| # | Name | Email | Institution |
| :--- | :--- | :--- | :--- |
| 1 | Amar Bawazeer | amarpro1234a@gmail.com | MJCET |
| 2 | Faizan Ahmed Khan | faizanahmedk50@gmail.com | MJCET |
| 3 | Mir Abbas Ali Razvi | abbasrazvi321@gmail.com | MJCET |
| 4 | Syed Liyaqat | liyaquath79@gmail.com | MJCET |

---

## Problem statement

Self-improving agents run inside closed environments, so users can't tell whether a claimed improvement is real, and what an agent learns from failure is thrown away. The brief asks for the **AutoEvolve Protocol**: an open-source framework where an agent runs a generate-critique-revise loop (V1, V2, V3), attests to its gains with zero-knowledge proofs, and publishes immutable snapshots to decentralized storage for other agents to learn from. It requires an iterative agent engine, a ZK proof of improvement, a decentralized memory registry, on-chain verification with a reward escrow, and a developer dashboard.

## Architecture

```
 Agent A / B (Python)  --- events (SSE) --->  Bridge (FastAPI)  --->  Dashboard (Next.js)
   generate, critique,                          |  pins entries
   revise, harness score                        v
        |                                    IPFS (Pinata)
        |  EZKL proof, signed by the agent's wallet
        v
 Sepolia: MemoryRegistry -> Halo2Verifier
          RewardEscrow pays the agent on a verified improvement
        ^
        |  Agent B reads entriesByTask / getEntry with its own wallet
```

Details and the trust model are in [docs/01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md).

## The pitch in 20 seconds

1. **Agent A** solves a task: Generate (V1) -> Critique -> Revise (V2, V3) with a changelog.
2. Every version is scored by an **objective harness** (tests, robustness, efficiency, rubric), so scores are integers a circuit can reason about.
3. An **EZKL ZK proof** shows `Score(Vn+1) > Score(Vn)` under a pre-committed weighting, without revealing the system prompt.
4. The diff, critique log and embedding go to **IPFS**. The CID and proof go to a **Sepolia** contract that checks the proof, checks that the CID is bound to the entry (`entryId = keccak256(cid, scoreHashOld, scoreHashNew, taskSignature, author)`), and pays a micro-reward.
5. **Agent B**, independent, connects to Sepolia with its own wallet, queries the registry directly, inherits the fix history, and avoids Agent A's failure loops. We measure B's V1 score **with vs without** inherited memory, and the median delta is proven on-chain.

## What makes this different from a generic entry

| Generic entry | AutoEvolve |
|---|---|
| Log of past runs on IPFS | **Memory lifecycle**: entries earn trust tiers (candidate -> validated -> trusted) from verified reuse, and decay when unused. This is our curation mechanism in place of DAO governance voting |
| Only successes stored | **Negative memory**: regressions are stored as "avoid X", which is what actually stops failure loops |
| Proof that a number went up | Proof over **objective, committed scores** with a committed rubric, so the claim means something |
| "Another agent could read it" | **Measured A/B demo**: B with memory vs B without, same task, ZK-attested delta |
| Table of CIDs | **CID bound to the entry on-chain**: `entryId` commits to the CID, scores and task, not just stored next to it |

The memory lifecycle design is adapted from a prior internal reflections pipeline (observation -> candidate -> validation evidence -> governed store). Only the design ideas are reused. All code is written fresh during the hackathon.

## Repo map

```
agent/        Python. Generate-critique-revise engine, scoring harness, memory client (Person 2)
zk/           EZKL circuit, proving scripts, Solidity verifier export (Person 3)
contracts/    Foundry. Registry, Verifier wrapper, RewardEscrow (Person 3)
bridge/       Python (FastAPI, web3.py): Pinata upload, chain calls, SSE event stream (Person 2)
dashboard/    Next.js + Tailwind. Execution tree, diffs, ZK status, on-chain log (Person 1)
shared/       JSON schemas and ABIs. The single source of truth for interfaces
docs/         Plans for each track. Start here.
```

## Read in this order

1. [docs/00-OVERVIEW.md](docs/00-OVERVIEW.md) - vision, scope, what we cut
2. [docs/01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md) - components and data flow
3. [docs/02-INTERFACES.md](docs/02-INTERFACES.md) - **frozen contracts between tracks. Do not change without telling everyone**
4. Your track: [03 Agent](docs/03-TRACK-AGENT.md), [04 ZK](docs/04-TRACK-ZK.md), [05 Chain + Storage](docs/05-TRACK-CHAIN-STORAGE.md), [06 Dashboard](docs/06-TRACK-DASHBOARD.md)
5. [docs/07-DEMO-AND-TIMELINE.md](docs/07-DEMO-AND-TIMELINE.md) - hour-by-hour plan, demo script, fallbacks

## Setup

Needs Python 3.11, Node 20+ and [Foundry](https://getfoundry.sh). Copy `.env.example` to `.env` and never commit it. Shared variables are listed in [docs/02-INTERFACES.md](docs/02-INTERFACES.md#6-environment).

```bash
python -m venv .venv
.venv/Scripts/pip install -r agent/requirements.txt -r bridge/requirements.txt -r zk/requirements.txt   # bin/pip on Linux and macOS
git submodule update --init
```

### Run offline, with no keys or network calls

Every output is labelled `baked`.

```bash
OFFLINE=1 .venv/Scripts/python -m uvicorn bridge.app:app --port 8787
BRIDGE_URL=http://127.0.0.1:8787 .venv/Scripts/python -m agent run --task lru-cache --agent A --offline
cd dashboard && npm install && npm run dev     # http://localhost:3100
```

### Run with real models

Needs `FEATHERLESS_API_KEY`. Add `--no-chain` to keep settlement baked.

```bash
.venv/Scripts/python -m agent run --task lru-cache --agent A --no-chain --run-id live-a
.venv/Scripts/python -m agent seed-memory --run-id live-a     # build memory from that run
.venv/Scripts/python -m agent experiment --task ttl-cache     # writes shared/baked/experiment.json
```

Without `--no-chain`, a run proves, pins and submits for real. That also needs `PINATA_JWT`, `SEPOLIA_RPC_URL`, the agent keys, deployed contract addresses and the proving keys in `zk/out/`.

### Tests

```bash
.venv/Scripts/python -m pytest agent bridge
cd contracts && forge test
cd dashboard && npm test
```

## Deployed contracts

On Sepolia, from `shared/deployments.sepolia.json`:

| Contract | Address |
|---|---|
| MemoryRegistry | `0xbF8abaCe162FA3Db70B4C9cb03e03d5B094344B1` |
| RewardEscrow | `0xaE091221A5B143e9aC0E76989Cc052D3708d1F31` |
| Halo2Verifier | `0x83D106D8e5224DCd5Da23Ed2367bcc73723B35d2` |

A real run with live models, recorded in `shared/baked/real-a.events.jsonl`:

| Step | Scores | Sepolia transaction |
|---|---|---|
| V1 to V2, verified improvement, 0.001 ETH reward | 9400 to 9850 | [`0x8ddcec06…f307`](https://sepolia.etherscan.io/tx/0x8ddcec061ee779f3b337bf559508ebedbab436c6c1bf3360551b8fd85e8cf307) |
| V2 to V3, stored as negative memory | 9850 to 9640 | [`0xc8e7ff50…6824`](https://sepolia.etherscan.io/tx/0xc8e7ff504bf3d72d31e891f7b223ba949335704fd880f7675a2d6b797e6d6824) |

Agent B then read 8 entries directly from the registry with its own wallet, including one Avoid entry, and ran `ttl-cache`. Its run is recorded in `shared/baked/real-b.events.jsonl`:

| Step | Scores | Sepolia transaction |
|---|---|---|
| V1 to V2, stored as negative memory | 9685 to 0 | [`0x944704f9…c307`](https://sepolia.etherscan.io/tx/0x944704f9ff3e7634feaa428c5863078e14cc1ab4552bffdb691cff7ab96ac307) |
| V1 to V3, verified improvement, 0.001 ETH reward | 9685 to 10000 | [`0xe0792726…394a`](https://sepolia.etherscan.io/tx/0xe0792726036ab794c804d909c2e301685356cec7656310302034421db70a394a) |

Agent B then posted evidence on-chain for all 8 inherited entries, which moved each one to `Validated` or kept it there. Evidence is per run, so it credits every inherited entry, not only the ones that helped.

## A/B result

Agent B's first attempt at `ttl-cache`, 5 trials each way, using one lesson from Agent A's live `lru-cache` run. Trial count and reporting were fixed before the run. Results and every generated solution are in `shared/baked/`.

| Measure | Without memory | With memory |
|---|---|---|
| Median robustness | 75 | 83 |
| Median total score | 8050 | 9415 |
| Capacity-0 test failed | 4 of 5 | 0 of 5 |
| Negative-capacity test failed | 5 of 5 | 0 of 5 |
| Zero-TTL test failed | 5 of 5 | 5 of 5 |
| Expiry-boundary test failed | 1 of 5 | 5 of 5 |

Memory fixed the two failures it covered, and left zero-TTL unfixed. Expiry-boundary failures rose, so inherited memory can also add a new mistake. Part of the total gain comes from efficiency and quality scores, which the lesson doesn't address. This is a small sample. The pair we prove is the trial with the median per-trial gain (+1440, 8050 to 9490), so it differs from the medians in the table, which are taken across each arm separately. It is proven on Sepolia in [this transaction](https://sepolia.etherscan.io/tx/0x491fca31895519107923db7c8fd967ceef1bd85e4b6eb397b19ccab632f776bc). The proof shows the committed score increased. It does not prove that memory caused the increase; the trials above are the evidence for that.

The registry also holds earlier entries from separate rehearsal runs, including a smaller A/B pair. The table above is the result we report.

## Known limits

- The proof covers the comparison over committed scores. It doesn't prove the harness ran honestly, so the test suite hash is stored in each entry for anyone to re-run.
- `entryId` binds the CID to the entry on-chain, but the proof itself is not bound to the CID or the author.
- The circuit doesn't range-check scores. The 0-100 limit is enforced in `zk/hash.py`.
- LLM output isn't bit-identical at temperature 0, so we prove over the stored scores.
- The harness runs candidate code in a subprocess with no secrets in its environment and sockets blocked, but it can read files on disk. It's not a security boundary.

## Third-party libraries

Python: `httpx`, `fastapi`, `uvicorn`, `web3`, `eth-hash`, `sentence-transformers`, `ezkl`, `torch`, `onnx`. Solidity: OpenZeppelin, `forge-std`. The dashboard's libraries are listed in [dashboard/README.md](dashboard/README.md). Models run through Featherless. All other code was written during the hackathon.

## License

MIT
