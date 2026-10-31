import argparse
import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from agent import experiment, loop, memory
from agent.events import EventSink
from agent.llm import FeatherlessClient, OfflineClient
from agent.settlement import BakedSettlement, ChainSettlement

# Baked runs never touch the chain, so they need no wallet.
STUB_AUTHOR = "0x" + "00" * 20


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="python -m agent")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--task", required=True)
    run.add_argument("--agent", choices=["A", "B"], required=True)
    run.add_argument("--memory", choices=["on", "off"], default="off")
    run.add_argument("--offline", action="store_true")
    run.add_argument("--chain", action="store_true", help="settle on-chain even with --offline LLM replay")
    run.add_argument("--no-chain", action="store_true", help="live models with baked settlement")
    run.add_argument("--scenario", choices=["clean", "regression"], default="clean")
    run.add_argument("--run-id")
    seed = commands.add_parser("seed-memory")
    seed.add_argument("--run-id", required=True)
    ab = commands.add_parser("experiment")
    ab.add_argument("--task", default="ttl-cache")
    ab.add_argument("--trials", type=int, default=5)
    commands.add_parser("experiment-attest")
    return parser.parse_args(argv)


def main(argv=None):
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    args = parse_args(argv)
    if args.command == "seed-memory":
        seeded = memory.seed_from_run(Path("runs") / args.run_id)
        print(f"seeded {len(seeded)} entries from {args.run_id}")
        return
    if args.command == "experiment":
        result = experiment.run(FeatherlessClient(), args.task, memory.retrieve_baked(), args.trials)
        experiment.OUTPUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(f"off {result['off']['mean_total']} on {result['on']['mean_total']} wrote {experiment.OUTPUT}")
        return
    if args.command == "experiment-attest":
        from eth_account import Account

        sink = EventSink(f"ab-attest-{int(time.time())}", "agentB", os.environ["BRIDGE_URL"], os.environ.get("BRIDGE_TOKEN"))
        settlement = ChainSettlement(sink, loop.Tree(sink), os.environ["BRIDGE_URL"], "agentB", token=os.environ.get("BRIDGE_TOKEN"))
        author = Account.from_key(os.environ["AGENT_B_PRIVATE_KEY"]).address
        result = experiment.attest(json.loads(experiment.OUTPUT.read_text(encoding="utf-8")), settlement, author)
        experiment.OUTPUT.write_text(json.dumps(result, indent=1) + chr(10), encoding="utf-8")
        print(result["proven"])
        return
    agent_id = f"agent{args.agent}"
    run_id = args.run_id or f"{args.task}-{agent_id}-{int(time.time())}"

    offline = args.offline or os.environ.get("OFFLINE") == "1"
    llm = OfflineClient(args.task, args.scenario) if offline else FeatherlessClient()
    sink = EventSink(run_id, agent_id, os.environ.get("BRIDGE_URL"), os.environ.get("BRIDGE_TOKEN"))
    tree = loop.Tree(sink)
    author = STUB_AUTHOR
    settlement = BakedSettlement(sink, tree)
    if args.chain or not (offline or args.no_chain):
        from eth_account import Account

        author = Account.from_key(os.environ[f"AGENT_{args.agent}_PRIVATE_KEY"]).address
        settlement = ChainSettlement(
            sink,
            tree,
            os.environ["BRIDGE_URL"],
            agent_id,
            token=os.environ.get("BRIDGE_TOKEN"),
            rpc_url=os.environ.get("SEPOLIA_RPC_URL"),
            registry=os.environ.get("REGISTRY_ADDRESS"),
        )

    best = loop.run(llm, sink, settlement, tree, args.task, agent_id, author, args.memory == "on")
    print(f"{run_id}: kept {best.name} scores={best.scores} total={best.total}")
    print(f"events: {Path(sink.path)}")
