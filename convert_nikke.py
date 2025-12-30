import os
import io
import base64
import requests
import datetime
import random
import json
from PIL import Image

# File to store history for daily progress/animation
HISTORY_FILE = "stats_history.json"

def generate_serrated_path(width, height, tooth_size=6):
    cmds = []
    x, y = 0, 0
    cmds.append(f"M {x},{y}")
    tooth_w = tooth_size
    tooth_h = tooth_size / 2
    
    # Top
    while x < width:
        next_x = x + tooth_w/2
        if next_x > width: next_x = width
        cmds.append(f"L {next_x},{tooth_h}")
        x = next_x
        if x >= width: break
        next_x = x + tooth_w/2
        if next_x > width: next_x = width
        cmds.append(f"L {next_x},{0}")
        x = next_x
    cmds.append(f"L {width},{0}")
    
    # Right
    while y < height:
        next_y = y + tooth_w/2
        if next_y > height: next_y = height
        cmds.append(f"L {width-tooth_h},{next_y}")
        y = next_y
        if y >= height: break
        next_y = y + tooth_w/2
        if next_y > height: next_y = height
        cmds.append(f"L {width},{next_y}")
        y = next_y
    cmds.append(f"L {width},{height}")

    # Bottom
    while x > 0:
        next_x = x - tooth_w/2
        if next_x < 0: next_x = 0
        cmds.append(f"L {next_x},{height-tooth_h}")
        x = next_x
        if x <= 0: break
        next_x = x - tooth_w/2
        if next_x < 0: next_x = 0
        cmds.append(f"L {next_x},{height}")
        x = next_x
    cmds.append(f"L {0},{height}")

    # Left
    while y > 0:
        next_y = y - tooth_w/2
        if next_y < 0: next_y = 0
        cmds.append(f"L {tooth_h},{next_y}")
        y = next_y
        if y <= 0: break
        next_y = y - tooth_w/2
        if next_y < 0: next_y = 0
        cmds.append(f"L {0},{next_y}")
        y = next_y
    cmds.append("Z")
    return " ".join(cmds)

def fetch_github_data(token, username):
    headers = {"Authorization": f"Bearer {token}"}
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes { stargazers { totalCount } }
        }
        issues(first: 1) { totalCount }
        pullRequests(first: 1) { totalCount }
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"login": username}},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print("GraphQL Errors:", data["errors"])
                return None
            return data["data"]["user"]
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fetch Error: {e}")
        return None

def calculate_streak(weeks):
    days = []
    for week in weeks:
        days.extend(week["contributionDays"])
    days.sort(key=lambda x: x["date"])
    
    current_streak = 0
    best_streak = 0
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    temp_streak = 0
    for day in reversed(days):
        if day["contributionCount"] > 0:
            temp_streak += 1
        else:
            if day["date"] == today: 
                continue 
            break
            
    current_streak = temp_streak
    
    temp_best = 0
    max_best = 0
    for day in days:
        if day["contributionCount"] > 0:
            temp_best += 1
        else:
            max_best = max(max_best, temp_best)
            temp_best = 0
    max_best = max(max_best, temp_best)
    
    return current_streak, max_best

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def convert_gif_to_svg_base64(input_path, output_path, target_width=480, skip_frames=2, quality=70, crop_bottom=36):
    print(f"Opening {input_path}...")
    img = Image.open(input_path)
    w, h = img.size
    print(f"Cropping bottom {crop_bottom} pixels to remove logos...")
    new_h = h - crop_bottom
    aspect = new_h / w
    target_height = int(target_width * aspect)
    print(f"Resizing crop ({w}x{new_h}) to ({target_width}, {target_height})...")
    
    frames = []
    try:
        while True:
            current_frame = img.copy().convert("RGB")
            cropped = current_frame.crop((0, 0, w, new_h))
            resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
            frames.append(resized)
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    
    frames = frames[::skip_frames]
    total_frames = len(frames)
    
    # ------------------------------------------------------------------
    # DATA & STATS MAPPING
    # ------------------------------------------------------------------
    github_token = os.environ.get("GITHUB_TOKEN")
    
    current_stats = { # Default/Fallback
        "commits": 567, "repos": 22, "stars": 45, "followers": 28,
        "prs": 12, "issues": 3, "streak_curr": 4, "streak_best": 8, "heatmap": []
    }
    
    if github_token:
        print("GITHUB_TOKEN found. Fetching real stats...")
        api_user = os.environ.get("GITHUB_USER", "GabrielBaiano")
        data = fetch_github_data(github_token, api_user)
        if data:
            total_commits = data["contributionsCollection"]["contributionCalendar"]["totalContributions"]
            total_repos = data["repositories"]["totalCount"]
            followers = data["followers"]["totalCount"]
            total_stars = sum(node["stargazers"]["totalCount"] for node in data["repositories"]["nodes"])
            weeks = data["contributionsCollection"]["contributionCalendar"]["weeks"]
            curr_streak, best_streak = calculate_streak(weeks)
            
            all_days = []
            for w in weeks: all_days.extend(w["contributionDays"])
            recent_days = all_days[-84:] if len(all_days) >= 84 else all_days
            heatmap = [d["contributionCount"] for d in recent_days]

            current_stats = {
                "commits": total_commits, "repos": total_repos, "stars": total_stars, "followers": followers,
                "prs": data["pullRequests"]["totalCount"], "issues": data["issues"]["totalCount"],
                "streak_curr": curr_streak, "streak_best": best_streak, "heatmap": heatmap
            }

    history_stats = load_history()
    if not history_stats:
        print("No history found. Init from current (skipping animation).")
        history_stats = current_stats.copy()

    # Calculate Derived Scores
    def get_level(s):
        # Level = Sum of all attributes (indices 3-8 mappings)
        return s["prs"] + s["issues"] + s["stars"] + s["followers"] + s["streak_curr"] + s["streak_best"]

    def get_echoes_score(s):
        # Base calculation for "Echoes" (Score)
        return s["commits"] + (s["stars"]*10) + (s["prs"]*5) + (s["issues"]*2) + (s["followers"]*5) + (s["repos"]*5)

    cur_lvl = get_level(current_stats)
    old_lvl = get_level(history_stats)
    
    # Logic: Spending Echoes
    # We want to show: Old Echoes (Higher) -> New Echoes (Lower)
    # The "New Echoes" is the current calculated score.
    # The "Old Echoes" should be Current Score + Cost of Levels gained.
    # Level Delta
    lvl_delta = cur_lvl - old_lvl
    # Arbitrary cost per level
    cost_per_level = 1500 
    
    curr_echoes = get_echoes_score(current_stats) # Final value (after spend)
    hist_echoes = curr_echoes + (lvl_delta * cost_per_level) if lvl_delta > 0 else get_echoes_score(history_stats) 
    # If no level up, just use history score. If level up, simulate we had MORE before.

    # Define Rows (Order matches SVG layout)
    # Indices: 0=Lvl, 1=Echoes, 2=Insight, 3=Vit, 4=End, 5=Str, 6=Skl, 7=Blt, 8=Arc
    stat_rows = [
        {"id": "level", "label": "Level", "old": old_lvl, "new": cur_lvl, "icon": "moon"},
        {"id": "echoes", "label": "Blood Echoes", "old": hist_echoes, "new": curr_echoes, "icon": "rune"},
        {"id": "insight", "label": "Insight (Commits)", "old": history_stats["commits"], "new": current_stats["commits"], "icon": "eye"}, # Insight is Commits now
        {"id": "vitality", "label": "Vitality (PRs)", "old": history_stats["prs"], "new": current_stats["prs"], "icon": "vitality"},
        {"id": "endurance", "label": "Endurance (Issues)", "old": history_stats["issues"], "new": current_stats["issues"], "icon": "endurance"},
        {"id": "strength", "label": "Strength (Stars)", "old": history_stats["stars"], "new": current_stats["stars"], "icon": "strength"},
        {"id": "skill", "label": "Skill (Flwrs)", "old": history_stats["followers"], "new": current_stats["followers"], "icon": "skill"},
        {"id": "bloodtinge", "label": "Bloodtinge (Strk)", "old": history_stats["streak_curr"], "new": current_stats["streak_curr"], "icon": "bloodtinge"},
        {"id": "arcane", "label": "Arcane (Best)", "old": history_stats["streak_best"], "new": current_stats["streak_best"], "icon": "arcane"},
    ]
    
    changed_indices = []
    for i, row in enumerate(stat_rows):
        # Restriction: Only animate attributes (Vitality -> Arcane, indices 3-8)
        # Level(0), Echoes(1), Insight(2) update silently (handled by global swap).
        if (row["new"] > row["old"]) and (i >= 3):
            changed_indices.append(i)

    # ------------------------------------------------------------------
    # LAYOUT CONSTANTS (Needed for both CSS calc and SVG drawing)
    # ------------------------------------------------------------------
    menu_w = 400
    menu_h = target_height - 60
    menu_x = target_width - menu_w - 30
    menu_y = 30
    inset = 15
    inner_w = menu_w - (inset*2)
    inner_h = menu_h - (inset*2)
    
    # Calculate Y positions for every row
    y_map = {}
    curr_draw_y = 70 # Top of first row
    y_map[0] = curr_draw_y; curr_draw_y += 29
    y_map[1] = curr_draw_y; curr_draw_y += 29
    y_map[2] = curr_draw_y; curr_draw_y += 29
    curr_draw_y += 25 # Gap
    y_map[3] = curr_draw_y; curr_draw_y += 29
    y_map[4] = curr_draw_y; curr_draw_y += 29
    y_map[5] = curr_draw_y; curr_draw_y += 29
    y_map[6] = curr_draw_y; curr_draw_y += 29
    y_map[7] = curr_draw_y; curr_draw_y += 29
    y_map[8] = curr_draw_y; curr_draw_y += 29
    
    confirm_text_y = inner_h - 15
    confirm_rect_y = confirm_text_y - 20 # Center rect approx

    # ------------------------------------------------------------------
    # ANIMATION TIMING & CSS
    # ------------------------------------------------------------------
    step_duration = 2.0
    initial_delay = 1.0
    move_to_confirm_duration = 1.0
    confirm_press_duration = 0.5
    final_hold = 2.0
    total_anim_time = initial_delay + (len(changed_indices) * step_duration) + move_to_confirm_duration + confirm_press_duration + final_hold
    if len(changed_indices) == 0: total_anim_time = 0

    css = ""
    if total_anim_time > 0:
        css = "<style>\n"
        t = initial_delay
        
        # 1. Cursor Animation
        cursor_kf = [f"0% {{ opacity: 0; transform: translate(0, 0); }}"]
        cursor_kf.append(f"{(t/total_anim_time)*100 - 0.1:.2f}% {{ opacity: 0; }}")
        
        # Calculate Global Swap Time (Percent)
        # Calculate Global Swap Time (Percent)
        # Sequence: Initial -> [Move -> Land -> Hold] -> ... -> MoveToConfirm -> Press -> Swap -> Hold
        move_duration = 0.25
        hold_duration = 0.8 
        step_duration = move_duration + hold_duration
        
        time_at_swap = initial_delay + (len(changed_indices) * step_duration) + move_to_confirm_duration + confirm_press_duration
        swap_p = (time_at_swap / total_anim_time) * 100
        
        # Track previous Y for cursor movement interpolation
        prev_y = y_map[changed_indices[0]] - 18 if changed_indices else 0
        
        for idx_i, idx in enumerate(changed_indices):
            target_y = y_map[idx] - 18
            
            # Times
            t_start_move = t
            t_land = t + move_duration
            t_leave = t + step_duration
            
            p_start_move = (t_start_move / total_anim_time) * 100
            p_land = (t_land / total_anim_time) * 100
            p_leave = (t_leave / total_anim_time) * 100
            
            # Cursor Keyframes
            if idx_i == 0:
                cursor_kf.append(f"{p_start_move:.2f}% {{ opacity: 0; transform: translate(0, {target_y}px); }}")
                cursor_kf.append(f"{p_land:.2f}% {{ opacity: 1; transform: translate(0, {target_y}px); }}")
            else:
                cursor_kf.append(f"{p_start_move:.2f}% {{ opacity: 1; transform: translate(0, {prev_y}px); }}")
                cursor_kf.append(f"{p_land:.2f}% {{ opacity: 1; transform: translate(0, {target_y}px); }}")
            
            cursor_kf.append(f"{p_leave:.2f}% {{ opacity: 1; transform: translate(0, {target_y}px); }}")
            
            prev_y = target_y
            t = t_leave
            
            # Row Upgrade Flash - Appear AFTER land
            uid = f"upg-{idx}"
            old_vid = f"val-old-{idx}"
            
            # Upgrade Overlay: Hidden -> Visible at land -> Hidden at swap
            row_kf = [
                f"0% {{ opacity: 0; }}",
                f"{p_land:.2f}% {{ opacity: 0; }}",
                f"{p_land + 0.1:.2f}% {{ opacity: 1; }}",
                f"{swap_p:.2f}% {{ opacity: 1; }}",       
                f"{swap_p+0.1:.2f}% {{ opacity: 0; }}",
                f"100% {{ opacity: 0; }}"
            ]
            
            # Old Value: Visible -> Hidden at land -> Hidden forever (swapped out globally anyway)
            # We want to hide it while UPG is visible to avoid clash
            old_val_kf = [
                f"0% {{ opacity: 1; }}",
                f"{p_land:.2f}% {{ opacity: 1; }}",
                f"{p_land + 0.1:.2f}% {{ opacity: 0; }}", # Hide when UPG appears
                f"100% {{ opacity: 0; }}" # Stay hidden
            ]
            
            css += f"#{uid} {{ animation: anim-{uid} {total_anim_time}s linear forwards; }}\n"
            css += f"@keyframes anim-{uid} {{ {' '.join(row_kf)} }}\n"
            
            # We need to override the class animation? 
            # ID selector is more specific, so this should work if we add the animation property.
            css += f"#{old_vid} {{ animation: anim-{old_vid} {total_anim_time}s linear forwards; }}\n"
            css += f"@keyframes anim-{old_vid} {{ {' '.join(old_val_kf)} }}\n"
            
        # Move to Confirm
        start_p = (t/total_anim_time)*100
        t += move_to_confirm_duration
        end_p = (t/total_anim_time)*100
        cursor_kf.append(f"{start_p:.2f}% {{ opacity: 1; transform: translate(0, {prev_y}px); }}")
        cursor_kf.append(f"{end_p:.2f}% {{ opacity: 1; transform: translate(0, {confirm_rect_y}px); }}")
        
        # Press Confirm
        c_start = end_p
        t += confirm_press_duration
        final_p = (t/total_anim_time)*100
        
        # Use simple global swap variables for the text classes
        css += f"@keyframes swap-out {{ 0% {{ opacity: 1; }} {swap_p:.2f}% {{ opacity: 1; }} {swap_p+0.1:.2f}% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}\n"
        css += f"@keyframes swap-in {{ 0% {{ opacity: 0; }} {swap_p:.2f}% {{ opacity: 0; }} {swap_p+0.1:.2f}% {{ opacity: 1; }} 100% {{ opacity: 1; }} }}\n"
        css += f".val-initial {{ animation: swap-out {total_anim_time}s linear forwards; }}\n"
        css += f".val-final {{ animation: swap-in {total_anim_time}s linear forwards; }}\n"
        
        cursor_kf.append(f"100% {{ opacity: 1; transform: translate(0, {confirm_rect_y}px); }}")
        css += f"@keyframes anim-cursor {{ {' '.join(cursor_kf)} }}\n"
        css += f"#cursor {{ animation: anim-cursor {total_anim_time}s linear forwards; }}\n"
        css += "</style>"

    # ------------------------------------------------------------------
    # SVG CONSTRUCTION
    # ------------------------------------------------------------------
    svg_content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {target_width} {target_height}" width="{target_width}" height="{target_height}">',
        '<defs>',
        '  <filter id="noise" x="0%" y="0%" width="100%" height="100%">',
        '    <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/>',
        '    <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.1 0"/>',
        '    <feComposite operator="in" in2="SourceGraphic" result="monoNoise"/>',
        '    <feBlend in="SourceGraphic" in2="monoNoise" mode="multiply" />',
        '  </filter>',
        '  <linearGradient id="borderGradient" x1="0%" y1="0%" x2="100%" y2="0%">',
        '      <stop offset="0%" stop-color="#555" />',
        '      <stop offset="50%" stop-color="#888" />',
        '      <stop offset="100%" stop-color="#555" />',
        '  </linearGradient>',
        '</defs>',
        '<style>',
        f'  .frame {{ display: none; animation: play {total_frames * 0.1:.2f}s step-end infinite; }}',
        f'  @keyframes toggle {{ 0% {{ opacity: 1; }} {100/total_frames:.2f}% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}',
        f'  .anim {{ opacity: 0; animation: toggle {total_frames * 0.15:.2f}s steps(1) infinite; }}'
    ]
    
    # Add frame delays
    for i in range(total_frames):
        delay = i * 0.15
        svg_content.append(f'  #f{i} {{ animation-delay: {delay:.3f}s; }}')
        
    svg_content.append('</style>')
    
    if css: svg_content.append(css)
    
    # Frames
    print("Encoding frames...")
    for i, frame in enumerate(frames):
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=quality, optimize=True)
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        svg_content.append(f'<image id="f{i}" class="anim" href="data:image/jpeg;base64,{img_str}" x="0" y="0" width="{target_width}" height="{target_height}" />')

    # Menu
    serrated_path = generate_serrated_path(menu_w, menu_h, tooth_size=12)
    svg_content.append(f'<g transform="translate({menu_x}, {menu_y})">')
    # Backgrounds
    svg_content.append(f'<path d="{serrated_path}" fill="#0a0a0a" opacity="0.85" />')
    svg_content.append(f'<path d="{serrated_path}" fill="#111111" filter="url(#noise)" opacity="0.6"/>')
    svg_content.append(f'<path d="{serrated_path}" fill="none" stroke="#333" stroke-width="2" />')
    
    svg_content.append(f'<g transform="translate({inset}, {inset})">')
    svg_content.append(f'<rect x="0" y="0" width="{inner_w}" height="{inner_h}" fill="none" stroke="url(#borderGradient)" stroke-width="3"/>')
    svg_content.append(f'<rect x="6" y="6" width="{inner_w-12}" height="{inner_h-12}" fill="none" stroke="#333" stroke-width="1"/>')
    
    # Styles
    font_stack = "'Times New Roman', 'Georgia', serif"
    c_gold = "#ccb486"; c_white = "#e0e0e0"; c_blue = "#6688aa"; c_blue_bg = "#3b4b6b"
    style_label = f'font-family: {font_stack}; font-weight: 400; fill: {c_gold}; font-size: 18px; text-shadow: 1px 1px 2px #000000; letter-spacing: 0.5px;'
    style_value = f'font-family: {font_stack}; font-weight: 400; fill: {c_white}; font-size: 18px; text-shadow: 1px 1px 2px #000000;'
    style_value_blue = f'font-family: {font_stack}; font-weight: 700; fill: {c_blue}; font-size: 18px; text-shadow: 1px 1px 2px #000000;'
    
    svg_content.append(f'<text x="20" y="30" style="font-family: {font_stack}; font-size: 24px; fill: {c_white}; font-weight: 400; opacity: 0.9;">Gabriel</text>')
    
    y = 45
    svg_content.append(f'<g transform="translate(0, {y})">')
    svg_content.append(f'<line x1="10" y1="0" x2="{inner_w-10}" y2="0" stroke="#555" stroke-width="1" />')
    svg_content.append(f'<line x1="10" y1="4" x2="{inner_w-10}" y2="4" stroke="#555" stroke-width="1" />')
    svg_content.append(f'<path d="M {inner_w/2-30},2 Q {inner_w/2},10 {inner_w/2+30},2" stroke="#777" fill="none" />')
    svg_content.append(f'<path d="M {inner_w/2-30},2 Q {inner_w/2},-6 {inner_w/2+30},2" stroke="#777" fill="none" />')
    svg_content.append('</g>')
    y += 25
    
    # Cursor
    if total_anim_time > 0:
        svg_content.append(f'<rect id="cursor" x="10" y="0" width="{inner_w-20}" height="28" fill="{c_blue_bg}" stroke="#7b8ba1" stroke-width="1.5" opacity="0" />')

    icons = {
        "moon": "M 10,2 A 8,8 0 1,1 10,18 A 6,6 0 1,0 10,2 Z",
        "rune": "M 10,2 L 10,18 M 6,6 L 14,6 M 6,12 L 14,14 M 10,18 L 6,16 M 10,18 L 14,16",
        "eye": "M 2,10 Q 10,0 18,10 Q 10,20 2,10 Z M 10,10 A 3,3 0 1,0 10,10.1",
        "vitality": "M 10,18 L 4,12 A 4,4 0 0,1 10,6 A 4,4 0 0,1 16,12 Z",
        "endurance": "M 10,2 Q 16,10 10,18 Q 4,10 10,2 Z",
        "strength": "M 2,10 A 4,4 0 0,1 6,6 L 14,4 L 16,8 L 12,10 L 16,14 L 10,18 L 2,10 Z",
        "skill": "M 8,2 L 6,10 L 2,10 L 4,12 L 2,16 L 8,12 L 12,18 L 14,8 L 8,2 Z",
        "bloodtinge": "M 10,10 m -6,0 a 6,6 0 1,0 12,0 a 6,6 0 1,0 -12,0 M 10,2 L 10,18 M 2,10 L 18,10 M 4,4 L 16,16 M 4,16 L 16,4",
        "arcane": "M 10,2 L 12,8 L 18,8 L 13,12 L 15,18 L 10,14 L 5,18 L 7,12 L 2,8 L 8,8 Z"
    }
    
    def draw_row(svg, y_pos, row_idx, row_data):
        icon = row_data["icon"]; label = row_data["label"]
        val_old = row_data["old"]; val_new = row_data["new"]
        
        svg.append(f'<rect x="15" y="{y_pos-14}" width="22" height="22" fill="#2a2822" stroke="#5a5540" stroke-width="1"/>')
        path = icons.get(icon, "")
        if path:
            fill = "#000"
            if icon in ["vitality", "rune", "bloodtinge"]: fill = "#8b0000"
            if icon == "endurance": fill = "#2e8b57"
            if icon == "eye": fill = "#4080a0"
            svg.append(f'<path d="{path}" transform="translate({15}, {y_pos-14}) scale(1.1)" fill="{fill}" stroke="none" />')
            
        svg.append(f'<text x="45" y="{y_pos+2}" style="{style_label}">{label}</text>')
        
        # Values logic
        # Values logic
        # 1. Old (Initial)
        svg.append(f'<text id="val-old-{row_idx}" class="val-initial" x="{inner_w-20}" y="{y_pos+2}" text-anchor="end" style="{style_value}">{val_old}</text>')
        # 2. New (Final)
        svg.append(f'<text class="val-final" x="{inner_w-20}" y="{y_pos+2}" text-anchor="end" style="{style_value}" opacity="0">{val_new}</text>')
        
        # 3. Upgrade Overlay (Only in animation)
        if (total_anim_time > 0) and (val_new > val_old) and (row_idx >= 3):
            delta = val_new - val_old
            uid = f"upg-{row_idx}"
            svg.append(f'<g id="{uid}" opacity="0">')
            # Removed opaque mask rect to let cursor/row BG show through
            # Left: + Delta (Blue)
            svg.append(f'<text x="{inner_w-105}" y="{y_pos+2}" text-anchor="end" style="{style_value_blue}">+ {delta}</text>')
            # Middle: > (White)
            svg.append(f'<text x="{inner_w-75}" y="{y_pos+2}" text-anchor="end" style="{style_value}">&gt;</text>')
            # Right: New Value (Blue)
            svg.append(f'<text x="{inner_w-20}" y="{y_pos+2}" text-anchor="end" style="{style_value_blue}">{val_new}</text>')
            svg.append('</g>')

        svg.append(f'<line x1="10" y1="{y_pos+14}" x2="{inner_w-10}" y2="{y_pos+14}" stroke="#2a2a2a" stroke-width="1" />')

    # Draw Text Rows
    draw_row(svg_content, y, 0, stat_rows[0]); y += 29
    draw_row(svg_content, y, 1, stat_rows[1]); y += 29
    draw_row(svg_content, y, 2, stat_rows[2]); y += 29
    y += 5; svg_content.append(f'<line x1="10" y1="{y}" x2="{inner_w-10}" y2="{y}" stroke="#555" stroke-width="1" />')
    y += 4; svg_content.append(f'<path d="M {inner_w/2-20},{y} Q {inner_w/2},{y+5} {inner_w/2+20},{y}" stroke="#777" fill="none" />')
    y += 16
    draw_row(svg_content, y, 3, stat_rows[3]); y += 29
    draw_row(svg_content, y, 4, stat_rows[4]); y += 29
    draw_row(svg_content, y, 5, stat_rows[5]); y += 29
    draw_row(svg_content, y, 6, stat_rows[6]); y += 29
    draw_row(svg_content, y, 7, stat_rows[7]); y += 29
    draw_row(svg_content, y, 8, stat_rows[8]); y += 29
    
    y += 8
    svg_content.append(f'<line x1="10" y1="{y}" x2="{inner_w-10}" y2="{y}" stroke="#555" stroke-width="1" />')
    svg_content.append(f'<line x1="10" y1="{y+4}" x2="{inner_w-10}" y2="{y+4}" stroke="#555" stroke-width="1" />')
    
    svg_content.append(f'<text id="confirm-btn" x="{inner_w/2}" y="{confirm_text_y}" text-anchor="middle" style="{style_label} font-size: 18px; fill: #aaa;">Confirm</text>')

    svg_content.append('</g></g>') # Close inner and menu groups
    
    # Border
    svg_content.append(f'<rect x="2" y="2" width="{target_width-4}" height="{target_height-4}" fill="none" stroke="#0d0d10" stroke-width="4" />')
    svg_content.append(f'<rect x="2" y="2" width="{target_width-4}" height="{target_height-4}" fill="none" stroke="{c_gold}" stroke-width="2" rx="4" />')
    svg_content.append(f'<circle cx="4" cy="4" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="{target_width-4}" cy="4" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="4" cy="{target_height-4}" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="{target_width-4}" cy="{target_height-4}" r="3" fill="{c_gold}" />')

    svg_content.append('</svg>')

    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_content))
    print(f"Done! SVG saved to {output_path}")
    
    save_history(current_stats)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Convert GIF to Animated SVG with GitHub Stats Overlay')
    parser.add_argument('--input', default='input_nikke.webp', help='Input GIF/WebP file path')
    parser.add_argument('--output', default='nikke.svg', help='Output SVG file path')
    parser.add_argument('--width', type=int, default=1000, help='Target width in pixels')
    parser.add_argument('--skip', type=int, default=1, help='Frame skip count (higher = fewer frames)')
    parser.add_argument('--quality', type=int, default=100, help='JPEG Quality (1-100)')
    parser.add_argument('--crop_bottom', type=int, default=0, help='Pixels to crop from bottom')
    args = parser.parse_args()
    convert_gif_to_svg_base64(args.input, args.output, target_width=args.width, skip_frames=args.skip, quality=args.quality, crop_bottom=args.crop_bottom)
