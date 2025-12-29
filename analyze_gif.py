import os
import glob
import shutil

# Get absolute path
cwd = os.getcwd()
gifs = glob.glob("*.gif")

if not gifs:
    print("No GIF found.")
    exit(1)

original_name = gifs[0]
if original_name == "input.gif":
    print("Already named input.gif")
    target_path = os.path.join(cwd, "input.gif")
else:
    # Construct absolute paths with long path prefix
    original_path = os.path.join(cwd, original_name)
    target_path = os.path.join(cwd, "input.gif")
    
    long_original = "\\\\?\\" + original_path
    long_target = "\\\\?\\" + target_path
    
    print(f"Renaming with long path support...")
    try:
        os.rename(long_original, long_target)
        print("Renamed successfully.")
    except Exception as e:
        print(f"Failed to rename: {e}")
        # If fail, try to open original with long path
        target_path = long_original

print(f"Analyzing...")

try:
    from PIL import Image
    # For Pillow, we might need normal paths or open file object
    with open(target_path, 'rb') as f:
        img = Image.open(f)
        print(f"Format: {img.format}")
        print(f"Size: {img.size}")
        print(f"Mode: {img.mode}")
        print(f"Frames: {getattr(img, 'n_frames', 1)}")
    
except Exception as e:
    print(f"Error: {e}")
