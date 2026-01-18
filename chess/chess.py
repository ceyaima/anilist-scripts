import requests
import datetime
import sys
import pyperclip

# --- Constants ---
ANILIST_API_URL = 'https://graphql.anilist.co'

QUERY = '''
query ($username: String) {
  MediaListCollection(userName: $username, type: ANIME) {
    lists {
      name
      entries {
        startedAt { year month day }
        media {
          id
          title { english romaji }
          siteUrl
          episodes
          duration
          genres
          tags { name }
          source
        }
      }
    }
  }
}
'''

def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        print("\n[Success] Results copied to clipboard.")
    except Exception as e:
        print(f"\n[Error] Clipboard failed: {e}")

def get_persistent_input():
    print("--- AniList Filter CLI ---")
    username = input("Enter Username: ").strip()
    while True:
        date_str = input("Enter Start Date cutoff (YYYY-MM-DD): ").strip()
        try:
            cutoff_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            return username, cutoff_date
        except ValueError:
            print("Invalid format. Use YYYY-MM-DD.")

def get_loop_input():
    print("\n" + "="*30)
    letter = input("Enter Letter (Leave empty to exit): ").strip()
    if not letter:
        return None, None, None

    while True:
        number = input("Enter Number: ").strip()
        if number.isdigit(): break
        print("Please enter a valid digit.")

    item_options = ["pawn", "rook", "knight", "bishop", "king", "queen"]
    print(f"Options: {', '.join(item_options)}")
    while True:
        item = input("Enter Item: ").strip().lower()
        if item in item_options: break
        print("Invalid choice.")

    return letter, number, item

def fetch_data(username):
    variables = {'username': username}
    try:
        response = requests.post(ANILIST_API_URL, json={'query': QUERY, 'variables': variables})
        data = response.json()
        if 'errors' in data:
            print("API Error:", data['errors'][0]['message'])
            sys.exit(1)
        return data['data']['MediaListCollection']
    except Exception as e:
        print(f"Network error: {e}")
        sys.exit(1)

def check_item_requirements(item, media):
    title_eng = media['title']['english'] or ""
    title_rom = media['title']['romaji'] or ""
    
    if item == "pawn":
        ep_count = media['episodes']
        if ep_count and all(c in '12' for c in str(ep_count)): return True, None
    elif item == "rook":
        if title_eng.lower().count('o') >= 2:
            return True, "English"
        elif title_rom.lower().count('o') >= 2:
            return True, "Romaji"
    elif item == "knight":
        if 'l' in title_eng.lower():
            return True, "English"
        elif 'l' in title_rom.lower():
            return True, "Romaji"
    elif item == "bishop":
        if (media.get('source') or "").upper() == "MANGA": return True, None
    elif item in ["king", "queen"]:
        return True, None
    return False, None

def process_list(collection, cutoff_date, letter, number, item):
    results = []
    target_list = next((l for l in collection['lists'] if l['name'].lower() == "completed"), None)
    
    if not target_list:
        print("Could not find 'Completed' list.")
        return []

    for entry in target_list['entries']:
        media = entry['media']
        s = entry['startedAt']

        if not (s['year'] and s['month'] and s['day']): continue
        if datetime.date(s['year'], s['month'], s['day']) <= cutoff_date: continue
        if (media['episodes'] or 0) * (media['duration'] or 0) < 60: continue
        if number not in str(media['id']): continue

        valid_tag = next((t['name'] for t in media['tags'] if t['name'] and t['name'][0].lower() == letter.lower()), None)
        if not valid_tag: continue

        passed, info = check_item_requirements(item, media)
        if passed:
            results.append({
                'title': media['title']['english'] or media['title']['romaji'],
                'url': media['siteUrl'],
                'tag': valid_tag,
                'genres': media['genres'],
                'item_info': info
            })
    return results

def main():
    # 1. Get username and date once
    username, cutoff_date = get_persistent_input()
    print(f"Fetching data for {username}...")
    collection = fetch_data(username)

    # 2. Enter the loop
    while True:
        letter, number, item = get_loop_input()
        if letter is None: 
            print("Exiting...")
            break
        
        matches = process_list(collection, cutoff_date, letter, number, item)
        
        output_buffer = [f"--- Found {len(matches)} matches for '{item}' ({letter}/{number}) ---\n"]
        
        if not matches:
            output_buffer.append("No matches found.")
        else:
            for m in matches:
                res_str = (f"{m['url']}"
                           f" Tag: {m['tag']}")
                if m['item_info']: res_str += f" Title: {m['item_info']}"
                output_buffer.append(res_str + "\n")

        final_text = "".join(output_buffer)
        print("\n" + final_text)
        copy_to_clipboard(final_text)

if __name__ == "__main__":
    main()