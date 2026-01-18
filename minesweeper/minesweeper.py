import requests
import datetime
import os
import random

# --- CONFIG ---
USERNAME = "croixph"
MIN_DATE = datetime.date(2025, 7, 13)
MIN_MINUTES = 60
OUTPUT_FILENAME = "minesweeper_output.txt"

# txt files
TXT_FILES = {
    "A2": "community/A2.txt", "B4": "community/B4.txt", "C4": "community/C4.txt",
    "D2": "community/D2.txt", "E4": "community/E4.txt", "F1": "community/F1.txt", "community/G3": "G3.txt"
}

# --- DATA RETRIEVAL ---

def load_id_list(filename):
    ids = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line.isdigit():
                        ids.add(int(clean_line))
        except Exception as e:
            print(f"Warning: Could not read {filename}: {e}")
    return ids

id_sets = {key: load_id_list(filename) for key, filename in TXT_FILES.items()}

def get_anilist_data(username):
    url = 'https://graphql.anilist.co'
    query = '''
    query ($userName: String) {
      MediaListCollection(userName: $userName, type: ANIME, forceSingleCompletedList: true) {
        lists {
          name
          entries {
            repeat
            startedAt { year month day }
            completedAt { year month day }
            media {
              id
              siteUrl
              title { english romaji }
              episodes
              duration
              season
              seasonYear
              startDate { year }
              genres
              tags { name category }
              source
              format
              popularity
              meanScore
              characters(role: MAIN) { pageInfo { total } }
            }
          }
        }
      }
    }
    '''
    variables = {'userName': username}
    response = requests.post(url, json={'query': query, 'variables': variables})
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    return response.json()

def check_title(media, condition_func):
    english = media['title'].get('english')
    romaji = media['title'].get('romaji')
    if english and condition_func(english): return True
    if romaji and condition_func(romaji): return True
    return False

def format_date_obj(date_dict):
    if not (date_dict['year'] and date_dict['month'] and date_dict['day']):
        return "????-??-??"
    return f"{date_dict['year']}-{date_dict['month']:02d}-{date_dict['day']:02d}"

def retrieve_qualified_anime():
    try:
        data = get_anilist_data(USERNAME)
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return {}

    collection = data['data']['MediaListCollection']['lists']
    completed_list = next((l for l in collection if l['name'] == "Completed"), None)
    
    if not completed_list:
        print("No 'Completed' list found.")
        return {}

    qualified_anime = {} 
    print(f"Scanning 'Completed' list for {USERNAME}...")
    skipped_rewatch_count = 0

    for entry in completed_list['entries']:
        media = entry['media']
        start_date = entry['startedAt']
        
        # check for rewatches
        if entry['repeat'] and entry['repeat'] > 0:
            skipped_rewatch_count += 1
            continue

        # check start date
        if not (start_date['year'] and start_date['month'] and start_date['day']):
            continue 
        entry_date = datetime.date(start_date['year'], start_date['month'], start_date['day'])
        if entry_date < MIN_DATE:
            continue

        # check runtime
        episodes = media['episodes'] or 0
        duration = media['duration'] or 0
        total_runtime = episodes * duration
        if total_runtime < MIN_MINUTES:
            continue

        # --- REQUIREMENTS ---
        reqs_met = set()
        
        mid = media['id']
        mid_str = str(mid)
        score = media['meanScore'] if media['meanScore'] is not None else 0
        pop = media['popularity'] if media['popularity'] is not None else 0
        start_year = media['startDate']['year']
        genres = media['genres'] or []
        tags = [t['name'] for t in media['tags']]
        fmt = media['format']
        season = media['season']
        source = media['source']
        main_chars = media['characters']['pageInfo']['total'] or 0

        # A
        if '1' in mid_str or '9' in mid_str: reqs_met.add("A1")
        if mid in id_sets['A2']: reqs_met.add("A2")
        if main_chars >= 4: reqs_met.add("A3")
        if start_year and 2010 <= start_year <= 2019: reqs_met.add("A4")
        if "Action" in genres or "Mystery" in genres: reqs_met.add("A5")
        if source in ["LIGHT_NOVEL", "VISUAL_NOVEL"]: reqs_met.add("A6")
        if pop < 45000: reqs_met.add("A7")

        # B
        def check_b1(t): return 'M' <= t[0].upper() <= 'Z'
        if check_title(media, check_b1): reqs_met.add("B1")
        if season == "WINTER": reqs_met.add("B2")
        if "Video Game" in tags or "School" in tags: reqs_met.add("B3")
        if mid in id_sets['B4']: reqs_met.add("B4")
        if 0 < score <= 69: reqs_met.add("B5")
        if season == "SPRING": reqs_met.add("B6")
        if any(g in genres for g in ["Adventure", "Thriller", "Psychological"]): reqs_met.add("B7")

        # C
        if "Fantasy" in genres or "Music" in genres: reqs_met.add("C1")
        if "Shounen" in tags or "Josei" in tags: reqs_met.add("C2")
        if fmt in ["MOVIE", "TV_SHORT"]: reqs_met.add("C3")
        if mid in id_sets['C4']: reqs_met.add("C4")
        if "Female Protagonist" in tags: reqs_met.add("C5")
        if fmt in ["TV", "SPECIAL"]: reqs_met.add("C6")
        if '2' in mid_str or '8' in mid_str: reqs_met.add("C7")

        # D
        if start_year and start_year <= 1999: reqs_met.add("D1")
        if mid in id_sets['D2']: reqs_met.add("D2")
        if "Sci-Fi" in genres or "Sports" in genres: reqs_met.add("D3")
        def check_d4(t): return any(c in t.upper() for c in ['M', 'I', 'N', 'E'])
        if check_title(media, check_d4): reqs_met.add("D4")
        if source in ["MANGA", "VIDEO_GAME"]: reqs_met.add("D5")
        if "War" in tags or "Ensemble Cast" in tags: reqs_met.add("D6")
        if start_year and start_year >= 2020: reqs_met.add("D7")

        # E
        if any(d in mid_str for d in ['4', '5', '6']): reqs_met.add("E1")
        if source in ["ORIGINAL", "OTHER"]: reqs_met.add("E2")
        if "Male Protagonist" in tags: reqs_met.add("E3")
        if mid in id_sets['E4']: reqs_met.add("E4")
        if "Shoujo" in tags or "Seinen" in tags: reqs_met.add("E5")
        if "Comedy" in genres or "Mecha" in genres: reqs_met.add("E6")
        if 45000 <= pop <= 75000: reqs_met.add("E7")

        # F
        if mid in id_sets['F1']: reqs_met.add("F1")
        if season == "SUMMER": reqs_met.add("F2")
        if score >= 70: reqs_met.add("F3")
        if "Romance" in genres or "Ecchi" in genres: reqs_met.add("F4")
        if "Drama" in genres or "Horror" in genres: reqs_met.add("F5")
        if season == "FALL": reqs_met.add("F6")
        def check_f7(t): return 'A' <= t[0].upper() <= 'L'
        if check_title(media, check_f7): reqs_met.add("F7")

        # G
        if pop > 75000: reqs_met.add("G1")
        if "Slice of Life" in genres or "Mahou Shoujo" in genres: reqs_met.add("G2")
        if mid in id_sets['G3']: reqs_met.add("G3")
        if start_year and 2000 <= start_year <= 2009: reqs_met.add("G4")
        if main_chars <= 3: reqs_met.add("G5")
        if fmt in ["OVA", "ONA"]: reqs_met.add("G6")
        if '3' in mid_str or '7' in mid_str: reqs_met.add("G7")

        # store
        qualified_anime[mid] = {
            'id': mid,
            'title': media['title']['english'] or media['title']['romaji'],
            'url': media['siteUrl'],
            'start_date': format_date_obj(entry['startedAt']),
            'finish_date': format_date_obj(entry['completedAt']),
            'reqs': reqs_met
        }

    if skipped_rewatch_count > 0:
        print(f"Skipped {skipped_rewatch_count} rewatch entries.")
        
    return qualified_anime

# --- SOLVING ---

def get_neighbors(coord, cols, rows):
    c_idx = cols.index(coord[0])
    r_idx = int(coord[1]) - 1
    neighs = []
    for dc in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if dc == 0 and dr == 0: continue
            nc = c_idx + dc
            nr = r_idx + dr
            if 0 <= nc < 7 and 0 <= nr < 7:
                neighs.append(cols[nc] + str(nr + 1))
    return neighs

def solve_board(anime_db):
    if not anime_db:
        return None, None, False

    rows = [str(i) for i in range(1, 8)]
    cols = list("ABCDEFG")
    all_coords = [c + r for r in rows for c in cols]
    neighbors_map = {coord: get_neighbors(coord, cols, rows) for coord in all_coords}
    anime_reqs = {aid: data['reqs'] for aid, data in anime_db.items()}

    coord_counts = {coord: 0 for coord in all_coords}
    for reqs in anime_reqs.values():
        for r in reqs:
            if r in coord_counts: coord_counts[r] += 1
    
    total_animes = len(anime_reqs)
    
    # track best possible board
    best_grid = None
    best_score = -1 
    is_perfect = False

    max_attempts = 3000
    print(f"Generating Minesweeper grid (Max attempts: {max_attempts})...")
    
    for attempt in range(max_attempts):
        mines = set()

        for coord in all_coords:
            freq = coord_counts[coord]
            prob = (freq / total_animes) * 0.85
            if random.random() < prob:
                mines.add(coord)
        
        # --- construction attempt ---
        current_grid = {}
        used_anime_ids = set()
        
        # assign mines
        for m in mines:
            current_grid[m] = 'MINE'
            
        # assign numbers
        numbers_coords = [c for c in all_coords if c not in mines]
        random.shuffle(numbers_coords) 
        
        structural_failure = False
        filled_count = 0
        total_number_cells = len(numbers_coords)
        
        for coord in numbers_coords:
            my_neighbors = neighbors_map[coord]
            my_mine_neighbors = [n for n in my_neighbors if n in mines]
            num_mines = len(my_mine_neighbors)
            
            # a number cell must be adjacent to at least 1 mine
            if num_mines == 0:
                structural_failure = True
                break
            
            # find unique anime
            valid_anime_ids = []
            for aid, reqs in anime_reqs.items():
                if aid in used_anime_ids: continue
                if all(m in reqs for m in my_mine_neighbors):
                    valid_anime_ids.append(aid)
            
            if valid_anime_ids:
                chosen_id = random.choice(valid_anime_ids)
                used_anime_ids.add(chosen_id)
                current_grid[coord] = {
                    'type': 'NUM',
                    'val': num_mines,
                    'anime_id': chosen_id,
                    'mine_neighbors': sorted(my_mine_neighbors),
                    'filled': True
                }
                filled_count += 1
            else:
                current_grid[coord] = {
                    'type': 'NUM',
                    'val': num_mines,
                    'anime_id': None,
                    'filled': False
                }
        
        if structural_failure:
            continue
            
        all_mines_valid = True
        for m in mines:
            m_neighbors = neighbors_map[m]
            if not any(n in current_grid and current_grid[n] != 'MINE' for n in m_neighbors):
                all_mines_valid = False
                break
        
        if not all_mines_valid:
            continue
            
        # --- assess score ---
        if filled_count > best_score:
            best_score = filled_count
            best_grid = current_grid
            
        if filled_count == total_number_cells:
            is_perfect = True
            break

    return best_grid, neighbors_map, is_perfect

# --- GENERATE OUTPUT ---

def get_cell_val(grid, coord):
    cell = grid.get(coord)
    if not cell: return "?"
    if cell == 'MINE': return "X"
    if isinstance(cell, dict):
        if cell.get('filled', False):
            return str(cell['val'])
        else:
            return "?"
    return "?"

def print_terminal_board(grid_assignments):
    """Prints the board nicely to the terminal using two spaces."""
    cols = list("ABCDEFG")
    print("\n   " + "  ".join(cols))
    print("-" * 25)
    
    fill_count = 0
    total_nums = 0
    
    for r in range(1, 8):
        row_str = [str(r)]
        for c in cols:
            coord = f"{c}{r}"
            val = get_cell_val(grid_assignments, coord)

            cell = grid_assignments.get(coord)
            if cell != 'MINE' and isinstance(cell, dict):
                total_nums += 1
                if cell.get('filled'):
                    fill_count += 1
            
            row_str.append(val)
        
        print("  ".join(row_str))
    
    print("-" * 25)
    print(f"Board Status: {fill_count}/{total_nums} number cells filled.\n")

def generate_markdown_board(grid):
    header = "__`-` `|       A       B       C       D       E       F       G`__"
    lines = [header]
    
    for r in range(1, 8):
        line = f"__`{r}`__ `|"
        for c in "ABCDEFG":
            coord = f"{c}{r}"
            val = get_cell_val(grid, coord)
            line += f"       {val}"
        line += "`"
        lines.append(line)
    
    return "\n".join(lines)

def generate_file_output(grid_assignments, anime_db):
    output_lines = []
    
    # add board
    output_lines.append(generate_markdown_board(grid_assignments))
    output_lines.append("\n") # Spacer
    
    # add entries
    sorted_coords = sorted(grid_assignments.keys(), key=lambda x: (x[0], x[1]))
    
    for coord in sorted_coords:
        cell_data = grid_assignments[coord]
        
        if cell_data == 'MINE':
            continue
        
        if not cell_data.get('filled', False):
            continue
            
        count = cell_data['val']
        anime = anime_db[cell_data['anime_id']]
        mine_neighbors = cell_data['mine_neighbors']
        
        mine_str_parts = []
        for i, mine_coord in enumerate(mine_neighbors, 1):
            mine_str_parts.append(f"// Mine {i}: {mine_coord}")
        mine_str_full = " ".join(mine_str_parts)
        
        entry_text = (
            f"{coord}) ☑ __{count} Mine(s)__\n"
            f"{anime['url']}\n"
            f"Start: {anime['start_date']} Finish: {anime['finish_date']} {mine_str_full}\n"
        )
        output_lines.append(entry_text)
        
    return "\n".join(output_lines)

# --- MAIN CODE ---

def main():
    print(f"--- Minesweeper Generator (Min Date: {MIN_DATE}) ---")
    
    # retrieve data
    anime_db = retrieve_qualified_anime()
    if not anime_db:
        print("No qualified anime found. Exiting.")
        return
    print(f"Found {len(anime_db)} unique anime qualifying for basic requirements.")

    # solve board
    grid, neighbors, is_perfect = solve_board(anime_db)
    
    if not grid:
        print("Could not generate even a partial valid board structure.")
        return

    if is_perfect:
        print("\nSUCCESS: Found a perfect board configuration!")
    else:
        print("\nPARTIAL SUCCESS: Could not fill all cells with unique anime.")
        print("Displaying best partial match found:")

    # print board
    print_terminal_board(grid)

    # generate file
    final_text = generate_file_output(grid, anime_db)
    
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"Successfully wrote results to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()