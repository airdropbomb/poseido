import time
import random
import sys
from tqdm import tqdm
from utils.loader import load_tokens, load_user_agents, ask_use_proxy, load_proxies
from utils.logger import log_info, log_success, log_warn, log_error
from utils.processor import process_token
from utils.spinner import Spinner

def print_header(title):
    width = 80
    print(f"\n{'=' * width}")
    print(f"| {title.center(width - 4)} |")
    print(f"{'=' * width}\n")

def countdown_delay():
    min_seconds = 240
    max_seconds = 450
    wait_time = random.randint(min_seconds, max_seconds)
    print("\n[WAIT] Starting cooldown before next campaign...")

    spinner = Spinner(message="Cooldown")
    spinner.start()
    time.sleep(wait_time)
    spinner.stop(end_message="Cooldown completed!")
    print("\r" + " " * 80 + "\r", end="")  # Clear line after countdown

def main():
    print_header("POSEIDON BOT AUTO UPLOAD VOICE")
    tokens = load_tokens()
    if not tokens:
        log_error("No tokens found in token.txt. Exiting. [ERR]")
        return
    uas = load_user_agents()
    use_proxy = ask_use_proxy()
    proxies = load_proxies() if use_proxy else [None] * len(tokens)

    while True:
        for i, token in enumerate(tokens):
            proxy = random.choice(proxies) if proxies else None
            log_info(f"Starting account {i+1}/{len(tokens)} [START]")
            try:
                process_token(token, uas, proxy)
            except Exception as e:
                log_error(f"Error processing token {i+1}: {e} [ERR]")
                continue
            time.sleep(10)  # Increased delay between accounts
        log_info("Cycle completed. Waiting 24 hours... [WAIT]")
        time.sleep(86400)  # 24 hours delay

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"Fatal error: {e} [ERR]")
        sys.exit(1)