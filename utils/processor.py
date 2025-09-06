import time
import hashlib
import requests
from tabulate import tabulate
from tqdm import tqdm
from .logger import log_info, log_warn, log_error, log_success, spinner_task
from .utils import generate_audio_buffer, get_random_ua, request_with_retry
from .spinner import Spinner

def format_campaign_table(campaigns):
    headers = ["Campaign Name", "Language", "Status", "Quota"]
    rows = [
        [
            camp.get('campaign_name', 'Unknown')[:20],
            camp.get('supported_languages', ['N/A'])[0],
            "Active" if camp.get('registration_status') == 'CONFIRMED' else "Pending",
            camp.get('remaining_quota', 0)
        ]
        for camp in campaigns
    ]
    spinner = Spinner(message="Rendering campaigns...")
    spinner.start()
    time.sleep(1)  # Simulate rendering
    spinner.stop(end_message="Campaigns rendered!")
    print("\n" + tabulate(rows, headers, tablefmt="fancy_grid") + "\n")

def process_token(token, uas, proxy=None):
    headers = {
        'User-Agent': get_random_ua(uas),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    base_url = "https://poseidon-depin-server.storyapis.com"

    # Get user info
    user_info = request_with_retry('get', f"{base_url}/users/me", token=token, headers=headers)
    if not user_info:
        log_error(f"Failed to fetch user info for token {token[:10]}... [ERR]")
        return
    username = user_info.get('name', 'Unknown')
    points = user_info.get('points', 'N/A')
    log_info(f"Processing account: {username}, points: {points} [ACC]")

    # Fetch campaigns
    campaigns_data = request_with_retry('get', f"{base_url}/campaigns?page=1&size=100", token=token, headers=headers)
    if not campaigns_data or 'items' not in campaigns_data:
        log_warn("No campaigns fetched [WARN]")
        return
    campaigns = [
        c for c in campaigns_data['items']
        if c.get('campaign_type') == 'AUDIO' and c.get('is_scripted')
    ]
    log_info(f"{len(campaigns)} eligible campaigns found [LIST]")

    # Fetch quotas for all campaigns and filter out those with zero quota
    for camp in campaigns:
        camp_id = camp.get('virtual_id')
        quota_data = request_with_retry('get', f"{base_url}/campaigns/{camp_id}/access", token=token, headers=headers)
        camp['remaining_quota'] = quota_data.get('remaining', 0) if quota_data else 0

    # Filter campaigns with remaining quota
    active_campaigns = [c for c in campaigns if c.get('remaining_quota', 0) > 0]
    if not active_campaigns:
        log_info("No campaigns with remaining quota [INFO]")
        return

    # Display campaign table
    format_campaign_table(active_campaigns)

    for camp in active_campaigns:
        camp_name = camp.get('campaign_name', 'Unknown')
        camp_id = camp.get('virtual_id')
        lang = camp.get('supported_languages', ['en'])[0]
        remaining = camp.get('remaining_quota', 0)
        log_info(f"Processing campaign '{camp_name}', remaining quota: {remaining} [CAMP]")

        with tqdm(total=remaining, desc=f"Uploading for {camp_name}", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            while remaining > 0:
                quota_data = request_with_retry('get', f"{base_url}/campaigns/{camp_id}/access", token=token, headers=headers)
                remaining = quota_data.get('remaining', 0) if quota_data else 0
                if remaining <= 0:
                    log_info(f"No remaining quota for '{camp_name}', skipping [CAMP]")
                    break
                script_data = request_with_retry(
                    'get',
                    f"{base_url}/scripts/next?language_code={lang}&campaign_id={camp_id}",
                    token=token, headers=headers
                )
                if not script_data:
                    log_warn(f"Failed to fetch next script for '{camp_name}', skipping [WARN]")
                    break
                script_text = script_data.get('script', {}).get('content', '')
                assignment_id = script_data.get('assignment_id')

                try:
                    audio_buffer = generate_audio_buffer(script_text, lang)
                except Exception as e:
                    log_warn(f"Audio generation failed: {e} [WARN]")
                    break

                file_name = f"audio_{int(time.time()*1000)}.mp3"
                presigned_payload = {
                    'content_type': 'audio/webm',
                    'file_name': file_name,
                    'script_assignment_id': assignment_id
                }
                presigned_data = request_with_retry(
                    'post',
                    f"{base_url}/files/uploads/{camp_id}",
                    token=token, data=presigned_payload, headers=headers
                )
                if not presigned_data:
                    log_warn("Failed to get presigned URL [WARN]")
                    break

                try:
                    upload_resp = requests.put(
                        presigned_data['presigned_url'],
                        data=audio_buffer,
                        headers={'content-type': 'audio/webm'}
                    )
                    if upload_resp.status_code not in [200, 201]:
                        log_warn(f"Upload failed: {upload_resp.status_code} [WARN]")
                        break
                except Exception as e:
                    log_warn(f"Upload error: {e} [WARN]")
                    break

                hash_val = hashlib.sha256(audio_buffer).hexdigest()
                confirm_payload = {
                    'content_type': 'audio/webm',
                    'object_key': presigned_data.get('object_key'),
                    'sha256_hash': hash_val,
                    'filesize': len(audio_buffer),
                    'file_name': file_name,
                    'virtual_id': presigned_data.get('file_id'),
                    'campaign_id': camp_id
                }
                confirm_resp = request_with_retry(
                    'post',
                    f"{base_url}/files",
                    token=token, data=confirm_payload, headers=headers
                )
                if confirm_resp:
                    log_success(f"Uploaded and confirmed: {camp_name} -> {file_name} [OK]")
                else:
                    log_warn(f"Failed to confirm '{camp_name}' [WARN]")
                pbar.update(1)
                remaining -= 1
                time.sleep(60)  # Increased delay to avoid rate-limiting