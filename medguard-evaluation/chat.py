#!/usr/bin/env python3
"""
Simple multi-turn chat REPL for local vLLM (OpenAI-compatible) servers.

Defaults:
- base_url: http://localhost:8000/v1
- api_key: token-abcd1234
- model:   meta-llama/Llama-3.1-8B-Instruct

Usage:
  - Run directly:
      uv run python chat.py
    Or via Makefile (preferred):
      make chat
    With a different model:
      make chat model=google/medgemma-27b-text-it

Commands in REPL:
  /exit, /quit, :q   Exit the chat
  /reset              Clear conversation history (keeps system prompt)
  /help               Show this help
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Dict, Any

import openai


DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_API_KEY = "token-abcd1234"
DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-turn chat against an OpenAI-compatible endpoint (e.g., vLLM)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OpenAI base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY", DEFAULT_API_KEY),
        help="API key (default: env OPENAI_API_KEY or token-abcd1234)",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Optional system prompt",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (default: 0.2)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Max new tokens for each response (default: 512)",
    )
    # Python 3.10 supports BooleanOptionalAction
    parser.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Stream tokens (default: enabled). Use --no-stream to disable.",
    )
    return parser.parse_args()


def print_help() -> None:
    print(
        """
Commands:
  /exit, /quit, :q   Exit the chat
  /reset              Clear conversation history (keeps system prompt)
  /help               Show this help
        """.strip()
    )


def build_client(base_url: str, api_key: str) -> openai.OpenAI:
    return openai.OpenAI(api_key=api_key, base_url=base_url)


def create_completion(
    client: openai.OpenAI,
    *,
    model: str,
    messages: List[Dict[str, Any]],
    stream: bool,
    temperature: float,
    max_tokens: int,
):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def run_repl(args: argparse.Namespace) -> int:
    client = build_client(args.base_url, args.api_key)

    messages: List[Dict[str, str]] = []
    if args.system:
        messages.append({"role": "system", "content": args.system})

    print(f"Model: {args.model}")
    print("Type /help for commands. Start chatting.\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not user_input:
            continue

        if user_input in {"/exit", "/quit", ":q"}:
            return 0
        if user_input == "/help":
            print_help()
            continue
        if user_input == "/reset":
            messages = []
            if args.system:
                messages.append({"role": "system", "content": args.system})
            print("Context cleared.")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            if args.stream:
                assistant_text_parts: List[str] = []
                for chunk in create_completion(
                    client,
                    model=args.model,
                    messages=messages,
                    stream=True,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                ):
                    for choice in chunk.choices:
                        delta = getattr(choice, "delta", None)
                        if delta is None:
                            # Some servers may use message instead of delta for first chunk
                            msg = getattr(choice, "message", None)
                            content_piece = getattr(msg, "content", "") if msg else ""
                        else:
                            content_piece = getattr(delta, "content", "") or ""
                        if content_piece:
                            assistant_text_parts.append(content_piece)
                            print(content_piece, end="", flush=True)
                print()
                assistant_text = "".join(assistant_text_parts)
            else:
                resp = create_completion(
                    client,
                    model=args.model,
                    messages=messages,
                    stream=False,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                )
                assistant_text = resp.choices[0].message.content or ""
                print(assistant_text)

            messages.append({"role": "assistant", "content": assistant_text})

        except KeyboardInterrupt:
            print("\n[Interrupted]")
            continue
        except Exception as exc:  # Keep REPL resilient
            print(f"[Error] {exc}", file=sys.stderr)
            continue

    return 0


def main() -> None:
    args = parse_args()
    sys.exit(run_repl(args))


if __name__ == "__main__":
    main()
