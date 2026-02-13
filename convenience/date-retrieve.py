import re
import requests
import sys

try:
    import pyperclip
except ImportError:
    print("Error: 'pyperclip' module not found. Please run: pip install pyperclip")
    sys.exit(1)

# config
username = "croixph"
symbols = ["☑", "☒", "✱"]
when_empty = "2024-01-14"

def fetch_user_list(username):
    """Fetches both ANIME and MANGA lists and organizes them into dictionaries."""
    url = "https://graphql.anilist.co"
    query = """
    query ($username: String, $type: MediaType) {
      MediaListCollection(userName: $username, type: $type) {
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
    
    id_map = {}
    title_map = {}

    for media_type in ["ANIME", "MANGA"]:
        print(f"Fetching {media_type} list...")
        response = requests.post(url, json={
            "query": query, 
            "variables": {"username": username, "type": media_type}
        })
        
        if response.status_code == 200:
            data = response.json()
            lists = data.get("data", {}).get("MediaListCollection", {}).get("lists", [])
            
            for user_list in lists:
                for entry in user_list.get("entries", []):
                    media = entry["media"]
                    entry_id = media["id"]
                    unique_id_key = f"{media_type.lower()}_{entry_id}"

                    start = entry["startedAt"]
                    end = entry["completedAt"]
                    
                    start_date = f"{start['year']}-{start['month']:02}-{start['day']:02}" if start.get('year') else None
                    end_date = f"{end['year']}-{end['month']:02}-{end['day']:02}" if end.get('year') else None
                    
                    date_info = {"start": start_date, "end": end_date}
                    
                    id_map[unique_id_key] = date_info
                    
                    if media["title"]["romaji"]:
                        title_map[media["title"]["romaji"].lower()] = date_info
                    if media["title"]["english"]:
                        title_map[media["title"]["english"].lower()] = date_info
        else:
            print(f"Error fetching {media_type} data: {response.text}")

    return id_map, title_map

def get_dates_from_cache(lookup_input, id_map, title_map):
    if "anilist.co/anime/" in lookup_input:
        try:
            anime_id = lookup_input.split("/anime/")[1].split("/")[0]
            key = f"anime_{anime_id}"
            if key in id_map:
                return id_map[key]["start"], id_map[key]["end"]
        except (IndexError, ValueError):
            pass

    if "anilist.co/manga/" in lookup_input:
        try:
            manga_id = lookup_input.split("/manga/")[1].split("/")[0]
            key = f"manga_{manga_id}"
            if key in id_map:
                return id_map[key]["start"], id_map[key]["end"]
        except (IndexError, ValueError):
            pass

    clean_title = lookup_input.strip().lower()
    if clean_title in title_map:
        return title_map[clean_title]["start"], title_map[clean_title]["end"]
    
    return None, None

def fetch_comment_body(comment_url):
    try:
        # extract id
        comment_id = comment_url.strip().split("comment/")[1].split("/")[0]
    except IndexError:
        print("Error: Invalid URL format. Must contain '/comment/ID'")
        return None

    query = """
    query ($id: Int) {
        ThreadComment(id: $id) {
            comment
        }
    }
    """
    
    print(f"Fetching forum comment {comment_id}...")
    response = requests.post("https://graphql.anilist.co", json={
        "query": query,
        "variables": {"id": int(comment_id)}
    })

    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("ThreadComment", {})[0].get("comment",{})
    else:
        print(f"Error fetching comment: {response.text}")
        return None

# input
target_url = input("Enter AniList Forum Comment URL: ").strip()
if not target_url:
    print("No URL provided.")
    sys.exit()

raw_text = fetch_comment_body(target_url)
if not raw_text:
    sys.exit()

# fetch
print(f"Fetching AniList data for {username}...")
id_cache, title_cache = fetch_user_list(username)

if not id_cache:
    print("Could not retrieve user data. Check username or internet connection.")
    sys.exit()

# process
print("Processing dates...")
output_buffer = []

# creates iterator to simulate file reading (to use next())
# keepends=True to preserve newline characters
lines_iter = iter(raw_text.splitlines(keepends=True))
pattern = r"^(Start:\s+)(\S+)(\s+Finish:\s+)(\S+)(.*)$"

while True:
    try:
        a = next(lines_iter)
    except StopIteration:
        break

    # check if requirement
    if a != "\n" and len(a) > 2 and a[2] == ")":
        save = a
        # list import
        is_empty_symbol = (len(save) > 4 and save[4] == symbols[-1])
        blank_date = "2024-01-14" if is_empty_symbol else "YYYY-MM-DD"
        
        try:
            anime_line = next(lines_iter)
        except StopIteration:
            output_buffer.append(save)
            break
        
        lookup_val = anime_line.strip()
        if anime_line.startswith("[") and "anilist.co" in anime_line:
            try:
                url_part = anime_line.split("](")[1]
                lookup_val = url_part.split(")")[0]
            except IndexError:
                pass 
        elif anime_line.startswith("["):
            lookup_val = anime_line[1:anime_line.find("]")]
        
        start_date, end_date = get_dates_from_cache(lookup_val, id_cache, title_cache)
        
        # fallbacks
        if not start_date: 
            start_date = when_empty if end_date else blank_date
        if not end_date: 
            end_date = "YYYY-MM-DD"

        # change ☒
        if len(save) > 4 and save[4] == symbols[1] and end_date != "YYYY-MM-DD":
            save = save[:4] + symbols[0] + save[5:]
        
        output_buffer.append(save)
        output_buffer.append(anime_line)
        
        # process start/finish
        try:
            old_line = next(lines_iter)
            match = re.match(pattern, old_line.rstrip("\n"))
            trailing_text = match.group(5) if match else ""
            
            new_line = f"Start: {start_date} Finish: {end_date}{trailing_text}\n"
            output_buffer.append(new_line)
            
            # \n
            output_buffer.append(next(lines_iter))
        except StopIteration:
            break
    else:
        output_buffer.append(a)

# output
final_output = "".join(output_buffer)

print("\n--- PROCESSED TEXT ---\n")
print(final_output)
print("\n----------------------")

try:
    pyperclip.copy(final_output)
    print(">> Successfully copied to clipboard!")
except Exception as e:
    print(f">> Failed to copy to clipboard: {e}")

input("Press Enter to close...")