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
        completedAt { year month day }
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

# --- Board Definitions ---
COLUMNS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
# Standard back row setup
BACK_ROW_PIECES = ['Rook', 'Knight', 'Bishop', 'Queen', 'King', 'Bishop', 'Knight', 'Rook']

def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        print("\n[Success] Results copied to clipboard.")
    except Exception as e:
        print(f"\n[Error] Clipboard failed: {e}")

def get_persistent_input():
    print("--- AniList Chess Challenge Solver ---")
    username = input("Enter Username: ").strip()
    while True:
        date_str = input("Enter Start Date cutoff (YYYY-MM-DD): ").strip()
        try:
            cutoff_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            return username, cutoff_date
        except ValueError:
            print("Invalid format. Use YYYY-MM-DD.")

def format_date(date_dict):
    if not date_dict['year'] or not date_dict['month'] or not date_dict['day']:
        return "????-??-??"
    return f"{date_dict['year']}-{date_dict['month']:02d}-{date_dict['day']:02d}"

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
    """
    Checks specific piece type requirements. 
    Returns (Boolean, Language_Used_String)
    """
    title_eng = media['title']['english'] or ""
    title_rom = media['title']['romaji'] or ""
    
    item = item.lower()
    
    if item == "pawn":
        # Episodes must contain only '1' or '2'
        ep_count = media['episodes']
        if ep_count and all(c in '12' for c in str(ep_count)): 
            return True, "N/A"
            
    elif item == "rook":
        # Title must have >= 2 'o's
        if title_eng.lower().count('o') >= 2: return True, "English"
        elif title_rom.lower().count('o') >= 2: return True, "Romaji"
        
    elif item == "knight":
        # Title must have 'l'
        if 'l' in title_eng.lower(): return True, "English"
        elif 'l' in title_rom.lower(): return True, "Romaji"
        
    elif item == "bishop":
        # Source must be MANGA
        if (media.get('source') or "").upper() == "MANGA": 
            return True, "N/A"
            
    elif item in ["king", "queen"]:
        return True, "N/A"
        
    return False, None

def get_candidates(anime_list, cutoff_date, letter, number, item):
    """
    Returns a list of anime entries that match the basic requirements for a specific board square.
    """
    candidates = []
    
    for entry in anime_list:
        media = entry['media']
        s = entry['startedAt']

        # Date Check
        if not (s['year'] and s['month'] and s['day']): continue
        if datetime.date(s['year'], s['month'], s['day']) <= cutoff_date: continue
        
        # Runtime Check
        total_runtime = (media['episodes'] or 0) * (media['duration'] or 0)
        if total_runtime < 60: continue
        
        # Row Check (ID contains number)
        if str(number) not in str(media['id']): continue

        # Column Check (Tag starts with letter)
        # We need to capture the specific tag used
        valid_tag = next((t['name'] for t in media['tags'] if t['name'] and t['name'][0].lower() == letter.lower()), None)
        if not valid_tag: continue

        # Piece Type Check
        passed, lang_info = check_item_requirements(item, media)
        if passed:
            candidates.append({
                'id': media['id'],
                'title': media['title']['english'] or media['title']['romaji'],
                'url': media['siteUrl'],
                'start_date': format_date(entry['startedAt']),
                'finish_date': format_date(entry['completedAt']),
                'tag': valid_tag,
                'genres': set(media['genres'] or []),
                'lang_info': lang_info,
                'type': item
            })
    return candidates

def generate_output_structure():
    """
    Creates the list of 32 slots in the specific order requested (1-32).
    Maps them to their "Opposite" partner index for genre checking.
    """
    # 01-08: White Pawns (Row 2, a-h)  <--> 17-24: Black Pawns (Row 7, a-h)
    # 09-16: White Pieces (Row 1, a-h) <--> 25-32: Black Pieces (Row 8, a-h)
    
    slots = {}
    
    # 1. White Pawns (1-8)
    for i, col in enumerate(COLUMNS):
        idx = i + 1
        slots[idx] = {
            'number': idx, 'color': 'White', 'type': 'Pawn', 
            'col': col, 'row': 2, 'opposite_idx': idx + 16
        }
        
    # 2. White Back Row (9-16)
    for i, col in enumerate(COLUMNS):
        idx = i + 9
        slots[idx] = {
            'number': idx, 'color': 'White', 'type': BACK_ROW_PIECES[i], 
            'col': col, 'row': 1, 'opposite_idx': idx + 16
        }

    # 3. Black Pawns (17-24)
    for i, col in enumerate(COLUMNS):
        idx = i + 17
        slots[idx] = {
            'number': idx, 'color': 'Black', 'type': 'Pawn', 
            'col': col, 'row': 7, 'opposite_idx': idx - 16
        }

    # 4. Black Back Row (25-32)
    for i, col in enumerate(COLUMNS):
        idx = i + 25
        slots[idx] = {
            'number': idx, 'color': 'Black', 'type': BACK_ROW_PIECES[i], 
            'col': col, 'row': 8, 'opposite_idx': idx - 16
        }
        
    return slots

def solve_board(collection, cutoff_date):
    target_list = next((l for l in collection['lists'] if l['name'].lower() == "completed"), None)
    if not target_list:
        print("Could not find 'Completed' list.")
        return {}

    anime_entries = target_list['entries']
    slots = generate_output_structure()
    
    # We solve by iterating through the 16 "White" slots (1-16).
    # For each White slot, we identify its paired Black slot (via opposite_idx).
    # We solve them together to ensure genre exclusion.
    
    final_allocation = {} # key: slot_index (1-32), value: anime_dict or None
    used_ids = set()

    print(f"Solving pieces...")

    # Iterate through the first 16 pieces (White side), which controls the pairing
    for i in range(1, 17):
        w_slot = slots[i]
        b_slot = slots[w_slot['opposite_idx']]
        
        # Get Candidates
        w_candidates = get_candidates(anime_entries, cutoff_date, w_slot['col'], w_slot['row'], w_slot['type'])
        b_candidates = get_candidates(anime_entries, cutoff_date, b_slot['col'], b_slot['row'], b_slot['type'])
        
        # Optimization: Sort by genre count (heuristic)
        w_candidates.sort(key=lambda x: len(x['genres']))
        b_candidates.sort(key=lambda x: len(x['genres']))
        
        selected_w = None
        selected_b = None
        found_pair = False
        
        # Find valid pair
        for w in w_candidates:
            if w['id'] in used_ids: continue
            
            for b in b_candidates:
                if b['id'] in used_ids: continue
                if w['id'] == b['id']: continue
                
                # CRITICAL: Genre Exclusion
                if w['genres'].isdisjoint(b['genres']):
                    selected_w = w
                    selected_b = b
                    found_pair = True
                    break
            
            if found_pair: break
            
        if found_pair:
            final_allocation[w_slot['number']] = selected_w
            final_allocation[b_slot['number']] = selected_b
            used_ids.add(selected_w['id'])
            used_ids.add(selected_b['id'])
        else:
            final_allocation[w_slot['number']] = None
            final_allocation[b_slot['number']] = None

    return slots, final_allocation

def main():
    username, cutoff_date = get_persistent_input()
    print(f"Fetching data for {username}...")
    collection = fetch_data(username)

    slots_def, allocation = solve_board(collection, cutoff_date)

    # --- Generate Output ---
    output_lines = []
    
    for i in range(1, 33):
        slot = slots_def[i]
        anime = allocation.get(i)
        
        # Header: e.g. "01) [O] __White Pawn a2__"
        header = f"{i:02d}) [O] __{slot['color']} {slot['type']} {slot['col']}{slot['row']}__"
        output_lines.append(header)
        
        if anime:
            # Title Link
            output_lines.append(f"[{anime['title']}]({anime['url']})")
            
            # Dates
            output_lines.append(f"Start: {anime['start_date']} Finish: {anime['finish_date']}")
            
            # Details: Tag, Language, Genres
            # Construct genre string
            genre_str = ", ".join(list(anime['genres']))
            
            # Construct language part
            lang_str = ""
            if anime['lang_info'] and anime['lang_info'] != "N/A":
                lang_str = f"{anime['lang_info']}"
                detail_line = f"Tag: {anime['tag']} / Language: {lang_str} / Genres: {genre_str}"
            elif anime['lang_info'] == "N/A":
                 # Based on request: "whether the title that fulfills is English or romaji"
                 # If N/A (like Bishop/Pawn), we don't strictly need it, but let's keep it clean
                 detail_line = f"Tag: {anime['tag']} / Genres: {genre_str}"

            output_lines.append(detail_line)
        else:
            output_lines.append("Requirements not fulfilled")
            
        output_lines.append("") # Empty line between entries

    final_text = "\n".join(output_lines)
    print("\n" + "="*20 + " RESULTS " + "="*20 + "\n")
    print(final_text)
    copy_to_clipboard(final_text)

if __name__ == "__main__":
    main()