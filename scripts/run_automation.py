#!/usr/bin/env python3
"""
Run CheatCV automation on live device.

Usage:
  python3 run_automation.py [--debug] [--dry-run]

Flags:
  --debug: Enable debug logging (step-by-step info)
  --dry-run: Simulate without actually tapping (for testing CV detection only)
"""

import sys
from pathlib import Path
import logging
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.brain.automation import CheatCVAutomation, State


def setup_logging(debug: bool = False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(description='Run CheatCV automation')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without tapping')
    parser.add_argument('--max-cycles', type=int, default=500, help='Max cycles (safety limit)')
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    print("\n" + "="*70)
    print("CheatCV Automation - Phase 3 Test")
    print("="*70)
    print("Config:")
    print(f"  Downscale:  0.5 (540x1200 for CV)")
    print(f"  Tap delays: 500-1500ms (random)")
    print(f"  Max cycles: {args.max_cycles}")
    print(f"  Debug:      {args.debug}")
    print(f"  Dry-run:    {args.dry_run}")
    print("="*70 + "\n")

    if args.dry_run:
        print("⚠️  DRY-RUN MODE - Will detect but NOT tap\n")

    try:
        # Initialize automation
        automation = CheatCVAutomation(
            downscale=0.5,
            tap_delay_range=(500, 1500),
            max_fill_iterations=50,
            debug=args.debug,
        )

        # Run automation
        print("Starting automation... Press Ctrl+C to stop\n")

        final_state = automation.run_until_complete(max_cycles=args.max_cycles)

        # Results
        if final_state == State.SUCCESS:
            print("\n✓ SUCCESS - All colors completed!")
        elif final_state == State.ERROR:
            print("\n✗ ERROR - Automation stopped due to error")
        else:
            print(f"\n⚠ Stopped in state: {final_state.value}")

        # Stats summary
        stats = automation.stats
        elapsed = automation.stats.state_transitions[-1][0] - automation.stats.start_time if stats.state_transitions else 0

        print("\nFinal Statistics:")
        print(f"  Total time:        {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"  Total taps:        {stats.taps_total}")
        print(f"  Total captures:    {stats.captures_total}")
        print(f"  Colors completed:  {stats.colors_completed}")
        print(f"  Avg taps/capture:  {stats.taps_total / stats.captures_total if stats.captures_total > 0 else 0:.1f}")
        print(f"  Avg time/tap:      {elapsed / stats.taps_total if stats.taps_total > 0 else 0:.2f}s")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
