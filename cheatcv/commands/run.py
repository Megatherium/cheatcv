"""Run CheatCV automation on live device."""

import sys
import logging
import click

from cheatcv.brain.automation import CheatCVAutomation, State


def setup_logging(debug: bool = False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--dry-run', is_flag=True, help='Simulate without tapping')
@click.option('--max-cycles', type=int, default=500, help='Max cycles (safety limit)')
def run(debug, dry_run, max_cycles):
    """Run CheatCV automation on live device."""
    setup_logging(debug=debug)

    print("\n" + "="*70)
    print("CheatCV Automation - Phase 3 Test")
    print("="*70)
    print("Config:")
    print(f"  Downscale:  0.5 (540x1200 for CV)")
    print(f"  Tap delays: 500-1500ms (random)")
    print(f"  Max cycles: {max_cycles}")
    print(f"  Debug:      {debug}")
    print(f"  Dry-run:    {dry_run}")
    print("="*70 + "\n")

    if dry_run:
        print("⚠️  DRY-RUN MODE - Will detect but NOT tap\n")

    try:
        # Initialize automation
        automation = CheatCVAutomation(
            downscale=0.5,
            tap_delay_range=(500, 1500),
            max_fill_iterations=50,
            debug=debug,
        )

        # Run automation
        print("Starting automation... Press Ctrl+C to stop\n")

        final_state = automation.run_until_complete(max_cycles=max_cycles)

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
