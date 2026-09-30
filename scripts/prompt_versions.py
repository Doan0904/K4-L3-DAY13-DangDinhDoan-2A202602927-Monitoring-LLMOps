"""Quản lý prompt `day13-chat` trên project Langfuse cá nhân (đọc key từ .env).

    python scripts/prompt_versions.py status              # version nào đang giữ label nào
    python scripts/prompt_versions.py create-v1           # v1 + labels baseline, production
    python scripts/prompt_versions.py create-v2           # v2 + label candidate
    python scripts/prompt_versions.py promote --version 2 # chuyển label production sang v2
    python scripts/prompt_versions.py rollback --version 1

Có thể làm các bước tương tự trên Langfuse UI; script chỉ giúp thao tác lặp lại được.
App cache prompt 60s (`cache_ttl_seconds=60`), nên sau khi đổi label hãy đợi >60s hoặc restart API.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

PROMPT_V1 = (
    "You are a concise support assistant.\n"
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}\n"
    "Answer using only the docs above."
)
# v2: thay đổi nhỏ về format/độ dài câu trả lời, giữ nguyên 3 biến bắt buộc.
PROMPT_V2 = (
    "You are a concise support assistant.\n"
    "Feature={{feature}}\n"
    "Docs={{docs}}\n"
    "Question={{message}}\n"
    "Answer using only the docs above in at most 3 bullet points. "
    "If the docs do not cover the question, say so."
)


def client():
    load_dotenv(REPO_ROOT / ".env")
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        raise SystemExit("Thiếu LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY trong .env")
    from langfuse import Langfuse

    lf = Langfuse()
    if not lf.auth_check():
        raise SystemExit("Langfuse auth_check thất bại: kiểm tra key và LANGFUSE_BASE_URL")
    return lf


def show_status(lf, name: str) -> None:
    print(f"Prompt: {name}")
    for version in range(1, 50):
        try:
            prompt = lf.get_prompt(name, version=version, cache_ttl_seconds=0, max_retries=0)
        except Exception:
            break
        labels = ", ".join(prompt.labels) if getattr(prompt, "labels", None) else "-"
        print(f"  v{prompt.version}: labels=[{labels}]")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["status", "create-v1", "create-v2", "promote", "rollback"])
    parser.add_argument("--version", type=int)
    parser.add_argument("--name", default=os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat"))
    args = parser.parse_args()

    lf = client()
    if args.action == "create-v1":
        prompt = lf.create_prompt(
            name=args.name, prompt=PROMPT_V1, labels=["baseline", "production"], type="text",
            commit_message="v1 baseline",
        )
        print(f"Created {args.name} v{prompt.version}")
    elif args.action == "create-v2":
        prompt = lf.create_prompt(
            name=args.name, prompt=PROMPT_V2, labels=["candidate"], type="text",
            commit_message="v2 candidate: bullet-point answers",
        )
        print(f"Created {args.name} v{prompt.version}")
    elif args.action in {"promote", "rollback"}:
        if args.version is None:
            parser.error("--version là bắt buộc cho promote/rollback")
        print("Trước:")
        show_status(lf, args.name)
        current = lf.get_prompt(args.name, version=args.version, cache_ttl_seconds=0)
        keep = [label for label in (current.labels or []) if label != "latest"]
        lf.update_prompt(name=args.name, version=args.version, new_labels=sorted(set(keep) | {"production"}))
        print(f"{args.action}: production -> v{args.version}")
        print("Sau:")
    show_status(lf, args.name)
    lf.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
