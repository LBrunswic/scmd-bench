"""A text-LLM baseline through an OpenAI-compatible or Ollama chat endpoint.

    python -m baselines.llm --items data/v1/dev.jsonl --track anon --k 64 --n 8 \\
        --backend ollama --model qwen2.5:7b --out results/qwen2.5-7b/dev.anon.sub.jsonl

One prompt per item (the item view, nothing else), `n` independent samples at the given
temperature. Resumable. The prompt is fixed here so a row is reproducible; RULES §5 requires the
budget to be declared, and `--n` is it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path

from scmd_bench.schema import load_items, read_jsonl

SYSTEM = ("You are an expert Lean 4 and mathlib prover. You will be given a theorem statement and a "
          "numbered set of premises. Write a proof of the theorem. You may cite ONLY the given "
          "premises (and Lean core / tactics). {cite} Reply with the proof term or tactic block "
          "that goes after `:=`, inside one ```lean code block, and nothing else.")
CITE = {"named": "Cite a premise by its name.",
        "anon": "Premises are named ⟪p0⟫, ⟪p1⟫, …; cite a premise by exactly that placeholder."}


def render(view: dict) -> str:
    lines = [f"Theorem:\n{view['target']}", "", f"Premises ({len(view['base'])}):"]
    lines += [s["statement"] for s in view["base"]]
    return "\n".join(lines)


_FENCE = re.compile(r"```(?:lean4?)?\s*\n(.*?)```", re.S)


def extract(text: str) -> str:
    blocks = [b for b in _FENCE.findall(text or "") if b.strip()]
    body = blocks[-1] if blocks else (text or "")
    body = body.strip()
    m = re.match(r"(?s)^(?:theorem|lemma|example)\b.*?:=\s*(.*)$", body)
    if m:
        body = m.group(1)
    return body.removeprefix(":=").strip()


def chat(backend: str, model: str, system: str, user: str, temperature: float, seed: int) -> str:
    if backend == "ollama":
        url = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/api/chat"
        body = {"model": model, "stream": False,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "options": {"temperature": temperature, "seed": seed, "num_predict": 1024,
                            "num_ctx": 16384}}
        if os.environ.get("SCMD_BENCH_OLLAMA_NUM_GPU") is not None:
            body["options"]["num_gpu"] = int(os.environ["SCMD_BENCH_OLLAMA_NUM_GPU"])
        req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3600) as r:
            return json.loads(r.read())["message"]["content"]
    raise SystemExit(f"unknown backend {backend}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--track", choices=("named", "anon"), required=True)
    ap.add_argument("--k", type=int, default=64)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only-premise-necessary", action="store_true")
    ap.add_argument("--backend", default="ollama")
    ap.add_argument("--model", required=True)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    items = [it for it in load_items(a.items) if str(a.k) in it.prompt["base"]
             and (not a.only_premise_necessary or it.meta.get("premise_necessary"))]
    if a.limit:
        items = items[:a.limit]
    done = {(r["item_id"], r["sample_idx"]) for r in read_jsonl(a.out)} if a.out.is_file() else set()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    system = SYSTEM.format(cite=CITE[a.track])
    with a.out.open("a", encoding="utf-8") as fh:
        for j, it in enumerate(items):
            user = render(it.view(a.track, a.k))
            for s in range(a.n):
                if (it.item_id, s) in done:
                    continue
                t0 = time.time()
                try:
                    text = chat(a.backend, a.model, system, user, a.temperature, seed=s)
                except Exception as exc:  # noqa: BLE001
                    print(f"{it.item_id} s{s}: {exc}", flush=True)
                    continue
                fh.write(json.dumps({"item_id": it.item_id, "sample_idx": s, "proof": extract(text),
                                     "raw": text, "gen_s": round(time.time() - t0, 1)},
                                    ensure_ascii=False) + "\n")
                fh.flush()
            print(f"{j + 1}/{len(items)} items", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
