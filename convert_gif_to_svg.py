import os
import io
import base64
import requests
import datetime
from PIL import Image

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
    # Flatten days
    days = []
    for week in weeks:
        days.extend(week["contributionDays"])
    
    # Sort by date just in case
    days.sort(key=lambda x: x["date"])
    
    current_streak = 0
    best_streak = 0
    # Simple logic for now (checking consecutive days with count > 0 from end)
    
    # Check current streak (working backwards from today)
    # Note: Calendar usually goes up to today or end of week.
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    temp_streak = 0
    # Iterate backwards
    for day in reversed(days):
        if day["contributionCount"] > 0:
            temp_streak += 1
        else:
            # If it's today and 0, streak might not be broken if we committed just now? 
            # Usually GitHub updates slowly. Assuming 0 breaks streak unless it's strictly 'today' and we ignore it?
            # Let's keep simple: 0 breaks streak.
            if day["date"] == today: 
                continue # Give a grace period for 'today' if empty? Or just break.
            break
            
    current_streak = temp_streak
    
    # Best streak (greedy scan)
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

def convert_gif_to_svg_base64(input_path, output_path, target_width=480, skip_frames=2, quality=70):
    print(f"Opening {input_path}...")
    img = Image.open(input_path)
    
    # Crop logic to remove AI watermarks (usually at bottom)
    # Original is 640x360. Watermarks are typically in the last 30-40px.
    # We will crop the bottom 36 pixels (10% of 360).
    crop_pixels = 36
    w, h = img.size
    print(f"Cropping bottom {crop_pixels} pixels to remove logos...")
    
    # Calculate new dimensions for info
    new_h = h - crop_pixels
    
    # Calculate aspect ratio of cropped image
    aspect = new_h / w
    target_height = int(target_width * aspect)
    
    print(f"Resizing crop ({w}x{new_h}) to ({target_width}, {target_height})...")
    print(f"Skipping every {skip_frames-1} frames...")
    print(f"JPEG Quality: {quality}")

    frames = []
    try:
        while True:
            current_frame = img.copy().convert("RGB")
            # Crop: (left, top, right, bottom)
            cropped = current_frame.crop((0, 0, w, new_h))
            
            # Resize - Use LANCZOS for high quality downscaling now (not nearest neighbor)
            resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
            frames.append(resized)
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    
    # Subsample frames
    frames = frames[::skip_frames]
    total_frames = len(frames)
    print(f"Total processed frames: {total_frames}")

    # Start building SVG
    svg_content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {target_width} {target_height}" width="{target_width}" height="{target_height}">',
        '<style>',
        f'  .frame {{ display: none; animation: play {total_frames * 0.1:.2f}s step-end infinite; }}', # step-end is easier for frames?
    ]
    
    # CSS Animation Logic
    # We use opacity because 'display' animation can be flaky in some renderers.
    # We use steps(1) to ensure strict on/off switching without fading.
    
    percent_visible = 100 / total_frames
    duration = total_frames * 0.15 # 150ms per frame to compensate for fewer frames (smoother)
    
    # Keyframes:
    # 0% -> Visible (Opacity 1)
    # [percent]% -> Hidden (Opacity 0)
    # 100% -> Hidden
    svg_content.append(f'  @keyframes toggle {{')
    svg_content.append(f'    0% {{ opacity: 1; }}')
    svg_content.append(f'    {percent_visible:.2f}% {{ opacity: 0; }}')
    svg_content.append(f'    100% {{ opacity: 0; }}')
    svg_content.append('  }')
    
    # Class style
    # Default opacity 0.
    # Animation creates the "pulse" of visibility.
    svg_content.append(f'  .anim {{ opacity: 0; animation: toggle {duration:.2f}s steps(1) infinite; }}')
    
    # Generate delays
    # We need to offset each frame so they play in sequence.
    # delay = i * timeframe.
    for i in range(total_frames):
        delay = i * (duration / total_frames)
        svg_content.append(f'  #f{i} {{ animation-delay: {delay:.3f}s; }}')
        
    svg_content.append('</style>')

    print("Encoding frames to Base64...")
    for i, frame in enumerate(frames):
        # Save frame to buffer as JPEG
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=quality, optimize=True)
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Determine size of this frame in KB
        # size_kb = len(img_str) / 1024
        # print(f"Frame {i}: {size_kb:.1f}KB")

        svg_content.append(f'<image id="f{i}" class="anim" href="data:image/jpeg;base64,{img_str}" x="0" y="0" width="{target_width}" height="{target_height}" />')

    # Add GitHub Stats Overlay
    # Fetch Data if Token available
    github_token = os.environ.get("GITHUB_TOKEN")
    # Default/Fallback Data
    stats_data = {
        "commits": "567",
        "prs": "12",
        "issues": "3",
        "repos": "22",
        "stars": "45",
        "followers": "28",
        "streak_curr": "4 days",
        "streak_best": "8 days",
        "heatmap": [] # Empty will use random gen
    }
    
    if github_token:
        print("GITHUB_TOKEN found. Fetching real stats...")
        # Default user GabrielBaiano based on path, can be env var too
        api_user = os.environ.get("GITHUB_USER", "GabrielBaiano")
        data = fetch_github_data(github_token, api_user)
        
        if data:
            print("Stats fetched successfully!")
            total_commits = data["contributionsCollection"]["contributionCalendar"]["totalContributions"]
            total_repos = data["repositories"]["totalCount"]
            followers = data["followers"]["totalCount"]
            total_stars = sum(node["stargazers"]["totalCount"] for node in data["repositories"]["nodes"])
            
            # Streaks
            weeks = data["contributionsCollection"]["contributionCalendar"]["weeks"]
            curr, best = calculate_streak(weeks)
            
            # Heatmap Data (Last 4 weeks approx)
            # Flatten days from last 4 weeks?
            # We need 21 cols x 4 rows = 84 days?
            # Calendar weeks usually give last year. We take the last few weeks.
            # We need 4 rows (days 0-3?) No, GitHub heatmap is 7 days vertically.
            # Our design is 4 rows x 21 cols.
            # We will map the last 84 days activity to our grid.
            
            all_days = []
            for w in weeks:
                all_days.extend(w["contributionDays"])
            
            # Take last 84 days
            recent_days = all_days[-84:] if len(all_days) >= 84 else all_days
            stats_data["heatmap"] = [d["contributionCount"] for d in recent_days]
            
            stats_data["commits"] = str(total_commits)
            stats_data["repos"] = str(total_repos)
            stats_data["stars"] = str(total_stars)
            stats_data["followers"] = str(followers)
            stats_data["streak_curr"] = f"{curr} days"
            stats_data["streak_best"] = f"{best} days"
            
            # PRs and Issues are "Total Count" from first 1? No, query returns totalCount directly
            # Note: The query asked for first:1 but got totalCount wrapper.
            stats_data["issues"] = str(data["issues"]["totalCount"])
            stats_data["prs"] = str(data["pullRequests"]["totalCount"])
            
        else:
            print("Failed to fetch data. Using fallback.")
            
    # Overlay Container Group - Centered vertically
    # Height of content increased to approx 310px. SVG Height 405px.
    # Top margin should be approx (405 - 310) / 2 = 47.5 -> ~48px.
    # Moved further left: target_width - 280 (was 260)
    svg_content.append(f'<g transform="translate({target_width - 280}, 48)">')
    
    
    # Colors (Bloodborne Theme)
    c_gold = "#d4af37" # Pale gold
    c_white = "#e0e0e0" # Off-white
    c_grey = "#a0a0a0" # Warm grey
    c_green = "#577a57" # Dull green for stats
    
    # Styles - Bloodborne Aesthetic (Serif, Elegant, Gothic)
    # Using Web-safe serif fonts to ensure it renders on GitHub
    font_stack = "'Times New Roman', 'Georgia', serif"
    
    style_text = f'font-family: {font_stack}; font-weight: 700; fill: {c_gold}; text-shadow: 2px 2px 4px #000000; letter-spacing: 1px;'
    style_label = f'font-family: {font_stack}; font-weight: 400; fill: {c_grey}; font-size: 13px; text-shadow: 1px 1px 2px #000000; letter-spacing: 0.5px;'
    style_value = f'font-family: {font_stack}; font-weight: 700; fill: {c_white}; font-size: 15px; text-shadow: 1px 1px 2px #000000;'
    
    # Title
    svg_content.append(f'<text x="0" y="0" style="{style_text} font-size: 20px;">Gabriel\'s Stats</text>')
    
    # Divider - Ornate Style
    # A line with a diamond in the middle. Width increased to 240.
    svg_content.append(f'<line x1="0" y1="10" x2="240" y2="10" stroke="{c_gold}" stroke-width="1" opacity="0.6" />')
    # Diamond shape in center (x=120)
    svg_content.append(f'<rect x="116" y="6" width="8" height="8" transform="rotate(45 120 10)" fill="{c_gold}" />')
    
    # Stats Items
    stats_groups = [
        ("GitHub Activity", [
            ("Total Commits", stats_data["commits"]),
            ("Pull Requests", stats_data["prs"]),
            ("Issues Opened", stats_data["issues"]),
            ("Contributed to", f'{stats_data["repos"]} repos')
        ]),
        ("Community", [
            ("Stars Earned", stats_data["stars"]),
            ("Followers", stats_data["followers"])
        ]),
        ("Streaks", [
            ("Current Streak", stats_data["streak_curr"]),
            ("Best Streak", stats_data["streak_best"])
        ])
    ]
    
    y_pos = 25
    
    # Render Groups - Compacted spacing
    for group_name, items in stats_groups:
        # Group Header
        svg_content.append(f'<text x="5" y="{y_pos}" style="{style_label} font-weight: 600; fill: #c9d1d9;">{group_name}</text>')
        y_pos += 16 # Was 20
        
        for label, value in items:
            # Estimate text width to draw the connecting line (Leader Line)
            # Approx 7px per char for 12px font
            label_width = len(label) * 7
            value_width = len(value) * 7
            
            line_start = 10 + label_width + 10 # Padding
            line_end = 230 - value_width - 10 # Padding (End moved to 230)
            
            # Draw thin line
            if line_end > line_start:
                svg_content.append(f'<line x1="{line_start}" y1="{y_pos-4}" x2="{line_end}" y2="{y_pos-4}" stroke="#30363d" stroke-width="1" stroke-dasharray="2 2" opacity="0.5" />')
            
            svg_content.append(f'<text x="10" y="{y_pos}" style="{style_label}">{label}</text>')
            svg_content.append(f'<text x="230" y="{y_pos}" text-anchor="end" style="{style_value}">{value}</text>')
            y_pos += 16 # Was 20
        y_pos += 4 # Spacer (Was 10)

    # Languages Section
    svg_content.append(f'<text x="5" y="{y_pos}" style="{style_label} font-weight: 600; fill: #c9d1d9;">Top Languages</text>')
    y_pos += 8 # Was 10
    
    # Language Bar
    bar_width = 225 # Extended width
    h_bar = 6 # Slightly thinner
    
    parts = [
        ("#f1e05a", 0.40), # JS
        ("#e34c26", 0.25), # HTML
        ("#563d7c", 0.15), # CSS
        ("#3178c6", 0.15), # TS
        ("#3572a5", 0.05)  # Python
    ]
    
    current_x = 5
    for color, percent in parts:
        w_seg = bar_width * percent
        svg_content.append(f'<rect x="{current_x}" y="{y_pos}" width="{w_seg}" height="{h_bar}" fill="{color}" />')
        current_x += w_seg
    
    y_pos += h_bar + 12
    
    # Language Labels (Mini legend)
    legend_style = 'font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif; font-weight: 400; fill: #8b949e; font-size: 10px;'
    svg_content.append(f'<circle cx="10" cy="{y_pos-3}" r="3" fill="#f1e05a" /><text x="16" y="{y_pos}" style="{legend_style}">JavaScript</text>')
    svg_content.append(f'<circle cx="70" cy="{y_pos-3}" r="3" fill="#e34c26" /><text x="76" y="{y_pos}" style="{legend_style}">HTML</text>')
    svg_content.append(f'<circle cx="115" cy="{y_pos-3}" r="3" fill="#563d7c" /><text x="121" y="{y_pos}" style="{legend_style}">CSS</text>')
    
    # Heatmap Section
    y_pos += 18
    svg_content.append(f'<text x="5" y="{y_pos}" style="{style_label} font-weight: 600; fill: #c9d1d9;">Contributions (Last 30 Days)</text>')
    y_pos += 8
    
    # Heatmap Grid
    box_size = 9 # Larger boxes (was 8)
    gap = 2
    start_x = 5
    
    import random
    heatmap_colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    # Weights for random: mostly empty or low, some high
    weights = [0.4, 0.3, 0.15, 0.1, 0.05]
    
    # Predictable "random" for consistent output
    rng = random.Random(42)
    
    # If we have real data, normalize it for colors
    real_data_iter = iter(stats_data["heatmap"]) if stats_data["heatmap"] else None
    
    for row in range(4): # 4 rows
        for col in range(21): # 21 cols (Fits perfectly in 240px width)
            color = "#161b22"
            
            if real_data_iter:
                try:
                    count = next(real_data_iter)
                    # Map count to color
                    if count == 0: color = "#161b22"
                    elif count <= 2: color = "#0e4429"
                    elif count <= 5: color = "#006d32"
                    elif count <= 10: color = "#26a641"
                    else: color = "#39d353"
                except StopIteration:
                    pass # Ran out of real data
            else:
                 color = rng.choices(heatmap_colors, weights=weights)[0]

            
            rect_x = start_x + col * (box_size + gap)
            rect_y = y_pos + row * (box_size + gap)
            
            svg_content.append(f'<rect x="{rect_x}" y="{rect_y}" width="{box_size}" height="{box_size}" rx="2" fill="{color}" />')

    svg_content.append('</g>')

    # Global Frame/Border (Bloodborne Style)
    # Inner border (Dark)
    svg_content.append(f'<rect x="2" y="2" width="{target_width-4}" height="{target_height-4}" fill="none" stroke="#0d0d10" stroke-width="4" />')
    # Outer border (Gold)
    svg_content.append(f'<rect x="2" y="2" width="{target_width-4}" height="{target_height-4}" fill="none" stroke="{c_gold}" stroke-width="2" rx="4" />')
    # Ornate corners (Gold circles)
    svg_content.append(f'<circle cx="4" cy="4" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="{target_width-4}" cy="4" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="4" cy="{target_height-4}" r="3" fill="{c_gold}" />')
    svg_content.append(f'<circle cx="{target_width-4}" cy="{target_height-4}" r="3" fill="{c_gold}" />')

    svg_content.append('</svg>')
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_content))
    
    # Check size
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done! SVG saved to {output_path}")
    print(f"Total Size: {file_size:.2f} MB")

if __name__ == "__main__":
    # Settings optimized for GitHub (Target < 10MB, ideally < 5MB)
    # 800px (Upscaled for better resolution)
    # 33 frames (skip=3, ~30fps feel)
    # Quality 80 (High)
    convert_gif_to_svg_base64('input.gif', 'bloodborne_animated_hq.svg', target_width=800, skip_frames=3, quality=80)
