#!/usr/bin/env python3
"""
Load test script for KisanMitra AI service.
Simulates concurrent users sending messages.

Usage:
    python scripts/load_test.py [--url http://localhost:8001] [--users 20] [--rounds 3]
"""

import argparse
import asyncio
import random
import statistics
import time

import httpx

SAMPLE_MESSAGES = [
    ("dairy ke liye koi scheme hai?", "hi"),
    ("tamatar ka bhav batao", "hi"),
    ("loan chahiye 5 lakh ka", "hi"),
    ("PMFME scheme ke liye kya documents chahiye?", "hi"),
    ("wheat price in delhi", "en"),
    ("EMI kitna hoga 3 lakh pe?", "hi"),
    ("namaste", "hi"),
    ("meri eligibility check karo", "hi"),
    ("DPR banao dairy farm ka", "hi"),
    ("pyaz ka rate kya hai lucknow mein?", "hi"),
]


async def send_request(client: httpx.AsyncClient, base_url: str,
                        user_id: str) -> dict:
    """Send one chat request and measure latency."""
    message, lang = random.choice(SAMPLE_MESSAGES)
    payload = {
        "user_id": user_id,
        "message": message,
        "language": lang,
        "channel": "loadtest",
    }

    start = time.time()
    try:
        resp = await client.post(f"{base_url}/ai/v1/agent/chat", json=payload)
        latency = (time.time() - start) * 1000
        if resp.status_code == 200:
            return {"status": "ok", "latency_ms": latency}
        return {"status": "error", "latency_ms": latency, "code": resp.status_code}
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {"status": "error", "latency_ms": latency, "error": str(e)[:100]}


async def run_load_test(base_url: str, num_users: int, rounds: int):
    """Run load test with concurrent users."""
    print(f"\nLoad test: {num_users} concurrent users x {rounds} rounds")
    print(f"Target: {base_url}\n")

    all_results = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for round_num in range(1, rounds + 1):
            print(f"Round {round_num}/{rounds}...", end=" ", flush=True)
            tasks = [
                send_request(client, base_url, f"loadtest-user-{i:03d}")
                for i in range(num_users)
            ]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

            ok = sum(1 for r in results if r["status"] == "ok")
            print(f"OK: {ok}/{num_users}")

    # Calculate stats
    latencies = [r["latency_ms"] for r in all_results]
    successes = [r for r in all_results if r["status"] == "ok"]
    errors = [r for r in all_results if r["status"] == "error"]

    print(f"\n{'='*50}")
    print(f"LOAD TEST RESULTS")
    print(f"{'='*50}")
    print(f"Total requests:  {len(all_results)}")
    print(f"Successful:      {len(successes)} ({len(successes)/len(all_results)*100:.1f}%)")
    print(f"Errors:          {len(errors)}")
    print(f"\nLatency (ms):")
    print(f"  Average:  {statistics.mean(latencies):.0f}")
    print(f"  Median:   {statistics.median(latencies):.0f}")
    if len(latencies) >= 2:
        sorted_lat = sorted(latencies)
        p95_idx = int(len(sorted_lat) * 0.95)
        p99_idx = int(len(sorted_lat) * 0.99)
        print(f"  P95:      {sorted_lat[p95_idx]:.0f}")
        print(f"  P99:      {sorted_lat[p99_idx]:.0f}")
    print(f"  Min:      {min(latencies):.0f}")
    print(f"  Max:      {max(latencies):.0f}")

    if errors:
        print(f"\nError samples:")
        for e in errors[:3]:
            print(f"  {e.get('code', '')} {e.get('error', '')[:80]}")


def main():
    parser = argparse.ArgumentParser(description="KisanMitra Load Test")
    parser.add_argument("--url", default="http://localhost:8001")
    parser.add_argument("--users", type=int, default=20, help="Concurrent users")
    parser.add_argument("--rounds", type=int, default=3, help="Number of rounds")
    args = parser.parse_args()

    asyncio.run(run_load_test(args.url, args.users, args.rounds))


if __name__ == "__main__":
    main()
