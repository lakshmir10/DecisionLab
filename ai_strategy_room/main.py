"""
main.py — CLI entry point for the AI Decision Simulation Lab.

Usage:
    python main.py                          # Interactive: pick a scenario
    python main.py --scenario "Your question here"  # Custom scenario
    python main.py --preset ai_meal_planning_india   # Use a preset
"""

import argparse
import json
import sys

from scenarios.examples import SCENARIOS, list_scenarios
from simulation.runner import run_simulation


def main():
    parser = argparse.ArgumentParser(
        description="AI Decision Simulation Lab — Multi-agent strategic debate"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Custom decision scenario (free text)",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=list_scenarios(),
        help="Use a preset scenario by name",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Write full results to a JSON file",
    )

    args = parser.parse_args()

    # Determine scenario
    if args.scenario:
        scenario = args.scenario
    elif args.preset:
        scenario = SCENARIOS[args.preset]
    else:
        # Interactive selection
        print("\n  Available preset scenarios:")
        for i, (key, text) in enumerate(SCENARIOS.items(), 1):
            print(f"    {i}. [{key}] {text[:70]}...")
        print(f"    {len(SCENARIOS) + 1}. Enter a custom scenario")
        print()

        choice = input("  Select (number): ").strip()
        try:
            idx = int(choice) - 1
            keys = list(SCENARIOS.keys())
            if 0 <= idx < len(keys):
                scenario = SCENARIOS[keys[idx]]
            elif idx == len(keys):
                scenario = input("  Enter your scenario: ").strip()
                if not scenario:
                    print("  No scenario provided. Exiting.")
                    sys.exit(1)
            else:
                print("  Invalid choice. Exiting.")
                sys.exit(1)
        except ValueError:
            print("  Invalid input. Exiting.")
            sys.exit(1)

    # Run simulation
    result = run_simulation(scenario, verbose=not args.quiet)

    # Optionally write JSON output
    if args.output_json:
        # Convert result to serializable dict
        output = {
            "scenario": result.scenario,
            "rounds": {
                str(k): [o.model_dump() for o in v]
                for k, v in result.round_outputs.items()
            },
            "synthesis": result.synthesis.model_dump() if result.synthesis else None,
            "market_snapshots": {
                str(k): {
                    "consensus_score": v.consensus_score,
                    "disagreement_index": v.disagreement_index,
                    "majority_recommendation": v.majority_recommendation,
                    "recommendation_distribution": v.recommendation_distribution,
                }
                for k, v in result.market_snapshots.items()
            },
            "confidence_shifts": result.confidence_shifts,
            "error": result.error,
        }
        with open(args.output_json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"  Results written to {args.output_json}")

    if result.error:
        print(f"\n  ⚠ Error during simulation: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
