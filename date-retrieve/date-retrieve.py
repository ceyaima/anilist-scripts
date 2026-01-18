import re
import requests

# Configuration
username = "croixph"
symbols = ["☑", "☒", "✱"]
input_path = r"C:\\Users\\candi\Downloads\\awc challenge wip\\change.txt"
output_path = r"C:\\Users\\candi\Downloads\\awc challenge wip\\changed.txt"
when_empty = "2024-01-14"

def fetch_user_list(username):
    """Fetches the entire user list once and organizes it into dictionaries."""
    url = "https://graphql.anilist.co"
    query = """
    query ($username: String) {
      MediaListCollection(userName: $username, type: ANIME) {
        lists {
          entries {
            media {
              id
              title {
                romaji
                english
              }
            }
            startedAt { year month day }
            completedAt { year month day }
          }
        }
      }
    }
    """
    response = requests.post(url, json={"query": query, "variables": {"username": username}})
    
    id_map = {}
    title_map = {}

    if response.status_code == 200:
        data = response.json()
        lists = data.get("data", {}).get("MediaListCollection", {}).get("lists", [])
        
        for user_list in lists:
            for entry in user_list.get("entries", []):
                media = entry["media"]
                entry_id = media["id"]
                
                # Format dates
                start = entry["startedAt"]
                end = entry["completedAt"]
                
                start_date = f"{start['year']}-{start['month']:02}-{start['day']:02}" if start.get('year') else None
                end_date = f"{end['year']}-{end['month']:02}-{end['day']:02}" if end.get('year') else None
                
                date_info = {"start": start_date, "end": end_date}
                
                # Store by ID
                id_map[entry_id] = date_info
                
                # Store by Titles (lowercase for easier matching)
                if media["title"]["romaji"]:
                    title_map[media["title"]["romaji"].lower()] = date_info
                if media["title"]["english"]:
                    title_map[media["title"]["english"].lower()] = date_info
                    
        return id_map, title_map
    else:
        print(f"Error fetching data: {response.text}")
        return {}, {}

def get_dates_from_cache(anime_input, id_map, title_map):
    """Looks up dates in the local cache instead of requesting the API."""
    # Check if input is a URL to extract ID
    if "anilist.co/anime/" in anime_input:
        try:
            anime_id = int(anime_input.split("/anime/")[1].split("/")[0])
            if anime_id in id_map:
                return id_map[anime_id]["start"], id_map[anime_id]["end"]
        except (IndexError, ValueError):
            pass

    # Otherwise, treat as title
    lookup_title = anime_input.strip().lower()
    if lookup_title in title_map:
        return title_map[lookup_title]["start"], title_map[lookup_title]["end"]
    
    return None, None

# --- Main Logic ---

print(f"Fetching AniList data for {username}...")
id_cache, title_cache = fetch_user_list(username)

if not id_cache:
    print("Could not retrieve user data. Check username or internet connection.")
    exit()

pattern = r"^(Start:\s+)(\S+)(\s+Finish:\s+)(\S+)(.*)$"

with open(input_path, "r", encoding="utf-8") as file, open(output_path, "w", encoding="utf-8") as new_file:
    for a in file:
        # Process lines that start with the task indicator (e.g., "02)" or "03)").
        if a != "\n" and len(a) > 2 and a[2] == ")":
            save = a
            # Determine blank date based on list import symbol
            blank_date = "2024-01-14" if save[4] == symbols[-1] else "YYYY-MM-DD"
            
            anime_line = file.readline()
            
            # Extract title/URL from line
            if anime_line.startswith("["):
                # Format: [Title](URL) - we extract the title inside brackets
                current_anime = anime_line[1:anime_line.find("]")]
            else:
                current_anime = anime_line.strip()
            
            print(f"Checking: {current_anime}")
            
            # Lookup in local cache
            start_date, end_date = get_dates_from_cache(current_anime, id_cache, title_cache)
            
            # Fallbacks
            if not start_date: 
                # If start date is missing in AniList but end date exists, use default
                start_date = when_empty if end_date else blank_date
            if not end_date: 
                end_date = "YYYY-MM-DD"

            # Change the symbol if completed
            if save[4] == symbols[1] and end_date != "YYYY-MM-DD":
                save = save[:4] + symbols[0] + save[5:]
            
            new_file.write(save)
            new_file.write(anime_line)
            
            # Process the Start/Finish line
            old_line = file.readline()
            match = re.match(pattern, old_line.rstrip("\n"))
            trailing_text = match.group(5) if match else ""
            
            new_line = f"Start: {start_date} Finish: {end_date}{trailing_text}\n"
            new_file.write(new_line)
            
            # Write the trailing blank line
            new_file.write(file.readline())
        else:
            new_file.write(a)

print("File processed successfully.")
input("Press Enter to close...")