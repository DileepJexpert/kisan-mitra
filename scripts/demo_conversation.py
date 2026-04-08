#!/usr/bin/env python3
"""
Interactive terminal demo for KisanMitra AI platform.
Simulates WhatsApp conversations without needing Gupshup.

Usage:
    python scripts/demo_conversation.py [--url http://localhost:8001]
"""

import argparse
import json
import sys
import time

import httpx

# ANSI colors
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

DEMO_USER_ID = "demo-user-001"

DEMO_SCENARIOS = {
    "1": ("Scheme Discovery", "main aam ka achaar banata hoon, koi scheme hai?"),
    "2": ("Mandi Price", "tamatar ka rate kya hai kanpur mein?"),
    "3": ("Loan Query", "dairy farm ke liye loan chahiye, 10 gaay"),
    "4": ("Dispute Filing", "buyer ne 3.5 lakh nahi diye, 2 mahine ho gaye"),
    "5": ("DPR Generation", "dairy farm ka DPR banao 10 cow ka"),
    "6": ("Help", "madad"),
    "7": ("Greeting", "namaste"),
}


def print_header():
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  KisanMitra AI Platform — Interactive Demo{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"\n{YELLOW}Type a message in Hindi or English, or pick a scenario:{RESET}")
    for key, (name, msg) in DEMO_SCENARIOS.items():
        print(f"  {BOLD}{key}{RESET}. {name}: \"{msg}\"")
    print(f"  {BOLD}q{RESET}. Quit")
    print()


def send_message(base_url: str, message: str, language: str = "hi") -> dict:
    """Send a message to the AI service and get a response."""
    url = f"{base_url}/ai/v1/agent/chat"
    payload = {
        "user_id": DEMO_USER_ID,
        "message": message,
        "language": language,
        "channel": "terminal",
    }

    start = time.time()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        return {"error": f"Cannot connect to {base_url}. Is the AI service running?"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}

    latency = int((time.time() - start) * 1000)
    data["latency_ms"] = latency
    return data


def main():
    parser = argparse.ArgumentParser(description="KisanMitra Demo")
    parser.add_argument("--url", default="http://localhost:8001", help="AI service URL")
    parser.add_argument("--language", default="hi", choices=["hi", "en"])
    args = parser.parse_args()

    print_header()

    while True:
        try:
            user_input = input(f"{GREEN}{BOLD}You > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{YELLOW}Bye!{RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            print(f"{YELLOW}Bye!{RESET}")
            break

        # Check if it's a scenario number
        if user_input in DEMO_SCENARIOS:
            name, message = DEMO_SCENARIOS[user_input]
            print(f"{YELLOW}  [Scenario: {name}]{RESET}")
            print(f"{GREEN}  Message: \"{message}\"{RESET}")
        else:
            message = user_input

        # Detect language
        language = args.language
        if any(ord(c) > 127 for c in message):
            language = "hi"

        # Send to AI service
        print(f"{YELLOW}  Thinking...{RESET}", end="", flush=True)
        result = send_message(args.url, message, language)
        print("\r" + " " * 30 + "\r", end="")  # Clear "Thinking..."

        if "error" in result:
            print(f"{RED}  Error: {result['error']}{RESET}\n")
            continue

        # Print response
        reply = result.get("reply_text", "(no response)")
        agents = result.get("agents_used", [])
        actions = result.get("actions_taken", [])
        latency = result.get("latency_ms", 0)

        print(f"{BLUE}{BOLD}KisanMitra > {RESET}{BLUE}{reply}{RESET}")
        print(f"{YELLOW}  [{', '.join(agents) if agents else 'general'}] "
              f"Tools: {', '.join(actions) if actions else 'none'} "
              f"| {latency}ms{RESET}\n")


if __name__ == "__main__":
    main()
