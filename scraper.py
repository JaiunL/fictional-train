import requests
from bs4 import BeautifulSoup
import os
import sys

# --- Configuration ---
URL = "https://police.ac.kr/police/police/master/76/boardList.do?mdex=police124"
MEMORY_FILE = "latest_post_id.txt"
KEYWORD = "청람"  # <--- CHANGE THIS to your desired keyword (e.g., "Announcement", "Result")

def send_discord_alert(post_id, title, link):
    """Sends a notification to Discord via Webhook."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("⚠️ Discord Webhook URL not found in environment variables.")
        return

    payload = {
        "content": f"🚨 **Keyword Match Found!** ('{KEYWORD}')",
        "embeds": [{
            "title": title,
            "url": link,
            "color": 5763719,  # Green color
            "fields": [
                {"name": "Post ID", "value": str(post_id), "inline": True}
            ],
            "footer": {"text": "Police Academy Bot"}
        }]
    }

    try:
        resp = requests.post(webhook_url, json=payload)
        resp.raise_for_status()
        print("✅ Discord notification sent.")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

def get_latest_post():
    """Scrapes the latest post data."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_row = soup.select_one("table.type_1 tbody tr")
        
        if not latest_row:
            print("Error: Table row not found.")
            return None

        columns = latest_row.find_all("td")
        post_id = int(columns[0].get_text(strip=True))
        
        title_tag = columns[1].find("a")
        title = title_tag.get_text(strip=True)
        link = "https://police.ac.kr" + title_tag['href']
        
        return post_id, title, link

    except Exception as e:
        print(f"Scraping Error: {e}")
        sys.exit(1)

def main():
    # 1. Fetch the latest online post
    latest_data = get_latest_post()
    if not latest_data:
        return

    current_id, current_title, current_link = latest_data
    print(f"Latest Online: [{current_id}] {current_title}")

    # 2. Check Local Memory
    if not os.path.exists(MEMORY_FILE):
        # First run: Just save the ID to memory, don't spam alerts
        print("First run detected. Initializing memory.")
        with open(MEMORY_FILE, "w") as f:
            f.write(str(current_id))
        return

    with open(MEMORY_FILE, "r") as f:
        try:
            last_seen_id = int(f.read().strip())
        except ValueError:
            last_seen_id = 0

    # 3. Logic: Is it new? -> Does it have keyword?
    if current_id > last_seen_id:
        print(f"New post detected! ({last_seen_id} -> {current_id})")
        
        # KEYWORD CHECK
        if KEYWORD in current_title:
            print(f"✅ Keyword '{KEYWORD}' found in title. Sending alert...")
            send_discord_alert(current_id, current_title, current_link)
        else:
            print(f"❌ Keyword '{KEYWORD}' NOT found. Skipping alert.")
        
        # Update Memory (We update it even if no keyword, so we don't check this post again)
        with open(MEMORY_FILE, "w") as f:
            f.write(str(current_id))
    else:
        print("No new updates.")

if __name__ == "__main__":
    main()
