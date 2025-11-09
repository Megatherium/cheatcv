"""Run CheatCV automation with hotkey control."""

import sys
import logging
import threading
import click

from cheatcv.brain.automation import CheatCVAutomation, State


class HotkeyController:
    """Hotkey controller for automation."""

    def __init__(self, automation: CheatCVAutomation):
        self.automation = automation
        self.automation_thread = None
        self.exit_flag = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def start_automation(self):
        """Start automation in background thread."""
        if self.automation_thread and self.automation_thread.is_alive():
            self.logger.warning("Automation already running!")
            return

        self.logger.info("🚀 Starting automation...")

        def automation_worker():
            try:
                final_state = self.automation.run_until_complete(max_cycles=500)

                if final_state == State.SUCCESS:
                    self.logger.info("✓ Automation completed successfully!")
                elif final_state == State.ERROR:
                    self.logger.error("✗ Automation stopped with error")
                else:
                    self.logger.info(f"Automation stopped in state: {final_state.value}")

            except Exception as e:
                self.logger.error(f"Automation thread error: {e}")
                import traceback
                traceback.print_exc()

        self.automation_thread = threading.Thread(target=automation_worker, daemon=True)
        self.automation_thread.start()

    def stop_automation(self):
        """Stop automation."""
        if not self.automation_thread or not self.automation_thread.is_alive():
            self.logger.warning("Automation not running!")
            return

        self.logger.info("⏸  Stopping automation...")
        self.automation.stop()

        # Wait for thread to finish (with timeout)
        self.automation_thread.join(timeout=5)

        if self.automation_thread.is_alive():
            self.logger.warning("Automation thread did not stop cleanly")
        else:
            self.logger.info("✓ Automation stopped")

    def on_press(self, key):
        """Handle key press events."""
        from pynput import keyboard

        try:
            # F9 - Toggle automation
            if key == keyboard.Key.f9:
                if self.automation.running:
                    self.stop_automation()
                else:
                    self.start_automation()

            # ESC - Emergency exit
            elif key == keyboard.Key.esc:
                self.logger.info("⚠ Emergency stop requested (ESC)")
                self.exit_flag = True
                if self.automation.running:
                    self.stop_automation()
                return False  # Stop listener

        except Exception as e:
            self.logger.error(f"Hotkey handler error: {e}")

    def run(self):
        """Run hotkey listener loop."""
        from pynput import keyboard

        print("\n" + "="*70)
        print("CheatCV Automation - Hotkey Mode")
        print("="*70)
        print("Hotkeys:")
        print("  F9  - Start/Stop automation toggle")
        print("  ESC - Emergency stop (exit program)")
        print("="*70)
        print("\nListening for hotkeys... Press ESC to exit.\n")

        # Start keyboard listener
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

        # Cleanup
        if self.automation_thread and self.automation_thread.is_alive():
            self.logger.info("Waiting for automation to finish...")
            self.automation_thread.join(timeout=10)

        self.logger.info("Exiting...")


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def hotkey(debug):
    """Run automation with hotkey control (F9=start/stop, ESC=exit)."""
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    try:
        # Initialize automation
        automation = CheatCVAutomation(
            downscale=0.5,
            tap_delay_range=(500, 1500),
            max_fill_iterations=50,
            debug=debug,
        )

        # Run hotkey controller
        controller = HotkeyController(automation)
        controller.run()

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
