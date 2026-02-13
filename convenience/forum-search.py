import requests
import re
import time
import sys

# AniList GraphQL API URL
URL = 'https://graphql.anilist.co'

def get_thread_id_from_url(url):
    """Extracts the thread ID from a standard AniList forum URL."""
    match = re.search(r'forum/thread/(\d+)', url)
    if match:
        return int(match.group(1))
    else:
        print("Error: Could not extract Thread ID from the provided URL.")
        sys.exit(1)

def make_api_request(query, variables):
    """Helper function to send requests to AniList API."""
    response = requests.post(URL, json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit hit. Waiting 60 seconds...")
        time.sleep(60)
        return make_api_request(query, variables)
    else:
        print(f"API Error {response.status_code}: {response.text}")
        sys.exit(1)

def get_thread_media_ids(thread_id, media_type):
    """
    Fetches comments and maps found media IDs to the ID of the comment 
    where they first appeared.
    """
    print(f"Fetching replies for Thread ID: {thread_id}...")
    
    # Added 'id' to the query to get the Comment ID
    query = '''
    query ($threadId: Int, $page: Int) {
        Page(page: $page, perPage: 50) {
            pageInfo {
                hasNextPage
            }
            threadComments(threadId: $threadId) {
                id
                comment
            }
        }
    }
    '''
    
    # Dictionary to store { media_id : comment_id }
    found_media_map = {}
    page = 1
    type_str = media_type.lower() 
    regex_pattern = fr'anilist\.co/{type_str}/(\d+)'

    while True:
        variables = {'threadId': thread_id, 'page': page}
        data = make_api_request(query, variables)
        
        if not data.get('data') or not data['data'].get('Page'):
            break

        comments = data['data']['Page']['threadComments']
        
        for item in comments:
            comment_id = item['id']
            text_content = item.get('comment', '')
            
            # Find all media links in this specific comment
            matches = re.findall(regex_pattern, text_content)
            
            for m in matches:
                media_id = int(m)
                # Only save if we haven't seen this media ID yet (to capture the first match)
                if media_id not in found_media_map:
                    found_media_map[media_id] = comment_id

        if not data['data']['Page']['pageInfo']['hasNextPage']:
            break
            
        page += 1
        time.sleep(0.5)

    print(f"Found {len(found_media_map)} unique {type_str} links in the thread.")
    return found_media_map

def get_user_media_list(username, media_type):
    """
    Fetches the user's entire list for the specified type.
    """
    print(f"Fetching {media_type} list for user: {username}...")
    
    query = '''
    query ($userName: String, $type: MediaType) {
        MediaListCollection(userName: $userName, type: $type) {
            lists {
                entries {
                    media {
                        id
                        title {
                            romaji
                            english
                        }
                        siteUrl
                    }
                }
            }
        }
    }
    '''
    
    variables = {'userName': username, 'type': media_type.upper()}
    data = make_api_request(query, variables)
    
    user_list_map = {}
    collection = data.get('data', {}).get('MediaListCollection', {})
    
    if not collection:
        print(f"Error: User '{username}' not found, list is private, or type is incorrect.")
        sys.exit(1)
        
    for list_category in collection.get('lists', []):
        for entry in list_category.get('entries', []):
            media = entry['media']
            user_list_map[media['id']] = media
            
    print(f"User has {len(user_list_map)} entries in their {media_type} list.")
    return user_list_map

def main():
    print("--- AniList Forum Thread Matcher ---")
    
    username = input("Enter AniList Username: ").strip()
    media_type = input("Enter Type (anime/manga): ").strip().upper()
    thread_url = input("Enter Forum Thread Link: ").strip()

    if media_type not in ['ANIME', 'MANGA']:
        print("Invalid type. Please enter 'anime' or 'manga'.")
        return

    thread_id = get_thread_id_from_url(thread_url)
    
    # This now returns a dictionary {media_id: comment_id}
    mentioned_map = get_thread_media_ids(thread_id, media_type)

    if not mentioned_map:
        print("No media links found in that thread.")
        return

    user_list = get_user_media_list(username, media_type)

    print("\n--- MATCHING RESULTS ---")
    print(f"The following {media_type.lower()}s mentioned in the thread are in {username}'s list:\n")
    
    matches_found = False
    
    # Iterate through the found media map
    for mid, comment_id in mentioned_map.items():
        if mid in user_list:
            matches_found = True
            media = user_list[mid]
            title = media['title']['english'] or media['title']['romaji']
            
            # Construct the direct link to the comment
            comment_link = f"https://anilist.co/forum/thread/{thread_id}/comment/{comment_id}"
            
            print(f"- {title}")
            print(f"  Media Link: {media['siteUrl']}")
            print(f"  Found in Reply ID: {comment_id}")
            print(f"  Reply Link: {comment_link}")
            print("-" * 30)
    
    if not matches_found:
        print("None. No overlaps found between the thread mentions and the user's list.")

if __name__ == "__main__":
    main()