import os
import random
import requests
from .logger import log_info, log_warn, log_error

def load_tokens():
    if not os.path.exists('token.txt'):
        log_error("token.txt not found! ?")
        return []
    with open('token.txt', 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    log_info(f"Loaded {len(tokens)} token(s) ??")
    return tokens

def load_user_agents():
    if not os.path.exists('brs.txt'):
        log_warn("brs.txt not found, using default UA ??")
        return [("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/134.0.0.0 Safari/537.36)")]
    with open('brs.txt', 'r') as f:
        uas = [line.strip() for line in f if line.strip()]
    return uas

def ask_use_proxy():
    ans = input("?? Do you want to use proxies? (y/n): ").strip().lower()
    return ans == 'y'

def load_proxies():
    if not os.path.exists('proxy.txt'):
        log_warn("proxy.txt not found, proceeding without proxies ??")
        return []
    with open('proxy.txt', 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    log_info(f"Loaded {len(proxies)} proxy(ies) ??")
    # Validate proxies
    valid_proxies = []
    for proxy in proxies:
        try:
            response = requests.get('https://api.ipify.org', proxies={'http': proxy, 'https': proxy}, timeout=10)
            if response.status_code == 200:
                valid_proxies.append(proxy)
                log_info(f"Valid proxy: {proxy} [OK]")
            else:
                log_warn(f"Invalid proxy: {proxy} (Status: {response.status_code}) ??")
        except Exception as e:
            log_warn(f"Proxy {proxy} failed: {e} ??")
    if not valid_proxies:
        log_warn("No valid proxies found, proceeding without proxies ??")
    return valid_proxies