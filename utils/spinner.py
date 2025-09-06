import sys
import threading
import time

class Spinner:
    spinner_cycle = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, message="Processing..."):
        self.stop_running = False
        self.thread = None
        self.message = message

    def start(self):
        def run_spinner():
            idx = 0
            while not self.stop_running:
                sys.stdout.write(f"\r{self.spinner_cycle[idx % len(self.spinner_cycle)]} {self.message}")
                sys.stdout.flush()
                idx += 1
                time.sleep(0.1)
        self.thread = threading.Thread(target=run_spinner)
        self.thread.start()

    def stop(self, end_message="Done"):
        self.stop_running = True
        if self.thread:
            self.thread.join()
        sys.stdout.write(f"\r{end_message}\n")