import requests
import re

# Configuration
USERNAME = "AWC"
API_URL = "https://graphql.anilist.co"

def get_custom_lists_names(username):
    """Fetches the names of all custom lists for the specified user."""
    query = '''
    query ($name: String) {
        User(name: $name) {
            mediaListOptions {
                animeList {
                    customLists
                }
            }
        }
    }
    '''
    variables = {'name': username}

    try:
        response = requests.post(API_URL, json={'query': query, 'variables': variables})
        data = response.json()
        
        if 'errors' in data:
            print(f"Error: User '{username}' not found.")
            return []
            
        return data['data']['User']['mediaListOptions']['animeList']['customLists']
    except Exception as e:
        print(f"Connection error: {e}")
        return []

def get_anime_id_from_link(link):
    """Extracts the Anime ID from a standard AniList URL."""
    if not link:
        return None
    match = re.search(r'/anime/(\d+)', link)
    if match:
        return int(match.group(1))
    return None

def get_media_entry(username, anime_id):
    """Fetches the list entry for a specific anime."""
    query = '''
    query ($userName: String, $mediaId: Int) {
        MediaList(userName: $userName, mediaId: $mediaId) {
            status
            customLists
            media {
                title {
                    romaji
                }
            }
        }
    }
    '''
    variables = {
        'userName': username,
        'mediaId': anime_id
    }

    response = requests.post(API_URL, json={'query': query, 'variables': variables})
    data = response.json()
    
    # Returns None if the anime is not in ANY list
    return data.get('data', {}).get('MediaList')

def main():
    print(f"--- Fetching Available Custom Lists for user '{USERNAME}' ---")
    available_lists = get_custom_lists_names(USERNAME)

    if available_lists:
        print("\nAvailable Custom Lists:")
        for name in available_lists:
            print(f"- {name}")
    else:
        print("No custom lists found or user not found.")

    print("\n" + "="*50)
    print("Type nothing and press Enter at the 'Anime Link' prompt to EXIT.")
    print("="*50 + "\n")

    while True:
        # 1. Ask for Anime Link (Exit condition)
        anime_link = input("Enter Anime Link: ").strip()
        
        if not anime_link:
            print("Exiting program. Goodbye!")
            break

        anime_id = get_anime_id_from_link(anime_link)
        if not anime_id:
            print("❌ Error: Invalid AniList link. Please try again.\n")
            continue

        # 2. Ask for List Name
        print(f"Which list? (Press Enter for ALL lists)")
        target_list = input("List Name: ").strip()

        # 3. Fetch Data
        entry = get_media_entry(USERNAME, anime_id)

        if not entry:
            print(f"❌ Result: This anime is not in ANY of {USERNAME}'s lists.\n")
            continue
        
        anime_title = entry['media']['title']['romaji']
        status = entry['status'] # e.g., COMPLETED, CURRENT, PLANNING
        user_custom_lists = entry.get('customLists') or {} # JSON object

        print(f"\n--- Results for: {anime_title} ---")

        # Logic for "Check All"
        if not target_list or target_list.lower() == "all":
            found_any = False
            
            # Print Standard Status
            print(f"• Standard Status: {status}")
            
            # Print Custom Lists
            active_customs = [key for key, val in user_custom_lists.items() if val is True]
            
            if active_customs:
                for lst in active_customs:
                    print(f"• Found in Custom List: {lst}")
                    found_any = True
            else:
                print("• Not found in any Custom Lists.")
        
        # Logic for Specific List
        else:
            # Check custom lists
            if target_list in user_custom_lists and user_custom_lists[target_list] is True:
                 print(f"✅ YES! It is in the custom list '{target_list}'.")
            # Also check if the user typed "Planning" or "Completed" (Standard lists)
            elif target_list.upper() == status:
                 print(f"✅ YES! It is in the standard list '{status}'.")
            else:
                 print(f"❌ NO. It is NOT in the list '{target_list}'.")
        
        print("-" * 30 + "\n")

if __name__ == "__main__":
    main()