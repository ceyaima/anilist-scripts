import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
USER_NAME = "AWC"
CUSTOM_LISTS = ["Cherry Blossoms", "Shapeshifting"]
OUTPUT_FILE = "G3.txt"
API_URL = 'https://graphql.anilist.co'
# ---------------------

def log(message):
    """Helper to print messages with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_anilist_ids(username, target_custom_lists):
    # GraphQL Query
    query = '''
    query ($username: String, $type: MediaType) {
      MediaListCollection(userName: $username, type: $type) {
        lists {
          name
          entries {
            media {
              id
              title {
                english
                romaji
              }
            }
          }
        }
      }
    }
    '''

    media_types = ["ANIME", "MANGA"]
    found_ids = []
    
    # Convert targets to a set for faster lookup
    targets = set(target_custom_lists)

    log(f"Starting ID fetch for user: '{username}'")
    log(f"Looking for lists: {targets}")

    for m_type in media_types:
        log("-" * 40)
        log(f"Preparing to fetch media type: {m_type}")
        
        variables = {
            'username': username,
            'type': m_type
        }

        try:
            log(f"Sending POST request to {API_URL}...")
            start_time = time.time()
            
            # Added timeout=30 seconds. If it hangs here, it's a network/firewall issue.
            response = requests.post(
                API_URL, 
                json={'query': query, 'variables': variables},
                timeout=30 
            )
            
            elapsed = time.time() - start_time
            log(f"Response received in {elapsed:.2f} seconds.")
            log(f"HTTP Status Code: {response.status_code}")

            if response.status_code != 200:
                if response.status_code == 404:
                    log(f"User has no {m_type} lists (404). Moving on.")
                    continue
                else:
                    log(f"CRITICAL ERROR: API returned status {response.status_code}")
                    log(f"Response body: {response.text}")
                    continue

            log("Parsing JSON response...")
            data = response.json()

            if 'errors' in data:
                log(f"API returned internal errors: {data['errors'][0]['message']}")
                continue

            # Navigate JSON safely
            collection = data.get('data', {}).get('MediaListCollection', {})
            
            if collection is None:
                 log("MediaListCollection is None. User might be private or blocked.")
                 continue

            lists = collection.get('lists', [])

            if not lists:
                log(f"No lists found in {m_type} collection.")
                continue
            
            log(f"Found {len(lists)} total lists in {m_type} category.")

            # Loop through every list found to debug
            for lst in lists:
                list_name = lst['name']
                entries_count = len(lst['entries'])
                
                # Verbose: Print every list name we see so we know what's there
                if list_name in targets:
                    log(f"  >>> MATCH FOUND: '{list_name}' with {entries_count} entries.")
                    
                    for entry in lst['entries']:
                        media_id = entry['media']['id']
                        title = entry['media']['title']['english'] or entry['media']['title']['romaji']
                        
                        if media_id not in found_ids:
                            found_ids.append(media_id)
                            # Uncomment the next line if you want to see every single title printed
                            # log(f"      - Added ID: {media_id} ({title})")
                        else:
                            pass
                            # log(f"      - Duplicate ID skipped: {media_id}")
                else:
                    log(f"  --- Skipping list: '{list_name}'")

        except requests.exceptions.Timeout:
            log("ERROR: The request timed out. The server took too long to respond.")
        except requests.exceptions.ConnectionError:
            log("ERROR: Connection error. Check your internet connection.")
        except Exception as e:
            log(f"ERROR: An unexpected error occurred: {e}")
            # Identify where the error happened
            import traceback
            traceback.print_exc()

    return found_ids

def save_to_txt(ids, filename):
    log("-" * 40)
    log(f"Preparing to save {len(ids)} IDs to file '{filename}'...")
    try:
        with open(filename, 'w') as f:
            for media_id in ids:
                f.write(f"{media_id}\n")
        log("File save successful.")
    except IOError as e:
        log(f"Error saving file: {e}")

if __name__ == "__main__":
    try:
        # 1. Get the IDs
        ids = get_anilist_ids(USER_NAME, CUSTOM_LISTS)

        # 2. Save to text file
        if ids:
            save_to_txt(ids, OUTPUT_FILE)
            log("Done.")
        else:
            log("Process finished, but no IDs were found in the specified lists.")
            
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")