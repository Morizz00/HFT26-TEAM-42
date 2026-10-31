# AutoEvolve dashboard (Track D)

Next.js frontend for the architecture in [docs/01](../docs/01-ARCHITECTURE.md), built to the contract in [docs/02](../docs/02-INTERFACES.md). It renders only from the event stream and bridge reads, and never imports agent code.

## Run

```
npm install
npm run dev          # http://localhost:3100
```

Works with no backend. It ships with the two real agent runs, which replay on a timer, and a snapshot of the Sepolia registry. With `.env.local` set, the On-chain screen reads Sepolia directly.

| Command | Does |
|---|---|
| `npm test` | Reducer, score and diff tests |
| `npm run typecheck` | TypeScript |
| `npm run lint` | ESLint |
| `node scripts/export-registry.mjs` | Refreshes `shared/baked/registry.json` from Sepolia and IPFS. Read-only |
| `node mock/generate.mjs` | Rebuilds `mock/baked.json` from the real runs and that snapshot |
| `node scripts/mock-bridge.mjs [events.jsonl ...]` | Local stand-in for the bridge on :8787. Pass `runs/<run_id>/events.jsonl` paths to replay agent runs |

## Deployment

On Vercel, set the root directory to `dashboard`, and copy these from `.env.example`:

- `NEXT_PUBLIC_REGISTRY_ADDRESS`
- `NEXT_PUBLIC_SEPOLIA_RPC_URL`

Leave `NEXT_PUBLIC_BRIDGE_URL` empty, so no **Connect live** button appears. Every `NEXT_PUBLIC_` value reaches the browser, so never put a keyed RPC URL there.

## Live mode

Set `NEXT_PUBLIC_BRIDGE_URL` in `.env.local`. A **Connect live** button then appears in the dock. An HTTPS deploy needs an HTTPS bridge.

The stream must send unnamed `data:` lines. `EventSource.onmessage` silently misses events sent with an `event:` name.

## Data

Everything bundled is real. The Compare screen and the landing's last beat read `shared/baked/experiment.json` and `shared/baked/memory_seed.json`. `mock/baked.json` holds the runs in `shared/baked/real-*.events.jsonl` and the registry snapshot, with each entry's critique read from IPFS.

To add a recorded run, add it to the `runs` list in `mock/generate.mjs`. Offline runs from a bridge carry `baked: true` and render as `baked`, with no links on their hashes.

## Where things are

| Path | Holds |
|---|---|
| `lib/events.ts` | The event contract |
| `lib/runState.ts` | Pure reducer from events to UI state |
| `lib/store.tsx` | Replay, live SSE, run provider |
| `lib/runLayout.ts` | Groups a run into version columns around the mirror line |
| `lib/water.ts` | Landing water: wave simulation plus a small WebGL shader. Falls back to a static reflection without WebGL or under reduced motion |
| `components/Story.tsx`, `app/styles/story.css` | The landing: one fixed stage where scroll plays each beat in place |
| `lib/flood.ts`, `components/Flood.tsx` | The water transition out of the landing page. Provider sits in the root layout so it survives the route change |
| `app/(landing)` | Landing page, the only place with Lenis |
| `app/(app)` | The six screens |

## Third-party libraries

Next.js, React, Tailwind CSS, `framer-motion`, `lenis`, `viem`. Fonts: Redaction, IBM Plex Sans, IBM Plex Mono via Fontsource.
