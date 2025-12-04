import os
import json
import subprocess
import time

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
BASE_URL = "https://e621.net/posts.json"
OUTPUT_DIR = "nsfw_test_set"

def fetch_posts(tags, limit):
    url = f"{BASE_URL}?tags={tags}&limit={limit}"
    print(f"Fetching posts for tags: {tags}")
    cmd = [
        "curl", "-s", "-A", USER_AGENT, url
    ]
    try:
        output = subprocess.check_output(cmd)
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching posts: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Output was: {output}")
        return None

def download_image(url, filepath):
    if os.path.exists(filepath):
        print(f"File already exists: {filepath}")
        return

    print(f"Downloading {url} to {filepath}")
    cmd = [
        "curl", "-s", "-A", USER_AGENT, "-o", filepath, url
    ]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading image: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    categories = {
        "safe": "rating:safe",
        "explicit": "rating:explicit"
    }

    for category, tag in categories.items():
        category_dir = os.path.join(OUTPUT_DIR, category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)

        data = fetch_posts(tag, 50)
        if not data or "posts" not in data:
            print(f"No posts found for {category}")
            continue

        for post in data["posts"]:
            file_url = post.get("file", {}).get("url")
            if not file_url:
                continue
            
            ext = post.get("file", {}).get("ext", "jpg")
            post_id = post.get("id")
            filename = f"{post_id}.{ext}"
            filepath = os.path.join(category_dir, filename)

            download_image(file_url, filepath)
            time.sleep(1) # Be nice to the API

if __name__ == "__main__":
    main()
