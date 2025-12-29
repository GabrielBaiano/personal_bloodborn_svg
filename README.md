# Bloodborne GitHub Stats (Animated SVG) 🩸

An automated, animated SVG widget for your GitHub Profile, styled with the dark, gothic aesthetic of **Bloodborne**.

![Bloodborne Stats Preview](bloodborne_animated_hq.svg)

## 🕯️ Overview

This project generates a high-quality, animated SVG that displays your GitHub statistics (Commits, Pull Requests, Stars, Followers, and Contribution Heatmap) overlaid on a looped background from Bloodborne.

**Features:**
- **Dynamic Stats:** Fetches real-time data from GitHub's GraphQL API.
- **Animated Background:** A smooth, high-quality looped animation (34 frames, optimized).
- **Bloodborne Theme:** Custom serif typography, gold/dark color palette, and ornamental borders.
- **Performance Optimized:** Uses Base64 JPEG embeddings and CSS opacity animation for a file size under ~2.5MB.

## ⚔️ Usage

To add this to your GitHub Profile `README.md`, simply use the following image link (replace `GabrielBaiano` with your username if you forked this):

```markdown
![Bloodborne Stats](https://github.com/GabrielBaiano/personal_bloodborn_svg/blob/main/bloodborne_animated_hq.svg)
```

## ⚙️ How it Works

This repository uses **GitHub Actions** to automatically update the stats every day.

1.  **Frequency**: Runs daily at midnight UTC via `.github/workflows/update_stats.yml`.
2.  **Process**:
    - Sets up a Python environment.
    - Runs `convert_gif_to_svg.py` with your `GITHUB_TOKEN`.
    - Fetches your latest stats (Commits, Stars, Heatmap, etc.).
    - Regenerates the `bloodborne_animated_hq.svg` file.
    - Commits the updated SVG back to the repository.

### Manual Generation (Local)

If you want to run the script locally:

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install Pillow requests
    ```
3.  Set your GitHub Token (optional, for real stats):
    ```bash
    # Windows PowerShell
    $env:GITHUB_TOKEN="your_token_here"
    ```
4.  Run the script:
    ```bash
    python convert_gif_to_svg.py
    ```

## 📜 Credits

- **Game Art**: FromSoftware (Bloodborne).
- **Concept & Code**: Built with a custom Python script that converts GIF frames to optimized SVG layers.

---
*"We are born of the blood, made men by the blood, undone by the blood."*
