import pyautogui
import pydirectinput
import time
import os
import random
import sys
import keyboard

# Optimize pydirectinput for maximum speed
pydirectinput.PAUSE = 0

# Monster images folder
MONSTERS_FOLDER = 'monsters'

# Detection confidence (0.0 to 1.0), how similar the image needs to be
CONFIDENCE = 0.78  # Higher = more precise matching

def random_sleep(min_time, max_time):
    """Sleep for a random duration (anti-bot detection)."""
    time.sleep(random.uniform(min_time, max_time))

def human_like_move(x, y):
    """Slight mouse movement - visible but fast."""
    offset_x = x + random.randint(-3, 3)
    offset_y = y + random.randint(-3, 3)
    pyautogui.moveTo(offset_x, offset_y, duration=0.08)  # Slight animation

def human_like_click():
    """MAXIMUM SPEED - Instant click."""
    pydirectinput.click()

def human_like_press(key):
    """Press key using multiple methods for better compatibility."""
    print(f"{key}", end=" ", flush=True)  # Show on same line
    try:
        # Method 1: Try pydirectinput (best for games)
        pydirectinput.press(key)
        time.sleep(0.01)
    except:
        # Method 2: Fallback to keyboard library
        try:
            keyboard.press_and_release(key)
            time.sleep(0.01)
        except:
            pass

def get_monster_images():
    """Returns paths to all image files in the 'monsters' folder."""
    valid_extensions = ('.png', '.jpg', '.jpeg')
    images = []
    
    if not os.path.exists(MONSTERS_FOLDER):
        os.makedirs(MONSTERS_FOLDER)
        print(f"WARNING: '{MONSTERS_FOLDER}' folder was created.")
        return images
        
    for filename in os.listdir(MONSTERS_FOLDER):
        if filename.lower().endswith(valid_extensions):
            images.append(os.path.join(MONSTERS_FOLDER, filename))
            
    return images

def find_any_monster(images):
    """Finds the closest monster to screen center from the given image list."""
    screen_width, screen_height = pyautogui.size()
    screen_center_x = screen_width // 2
    screen_center_y = screen_height // 2
    
    all_found_mobs = []  # List of (distance, center_point, mob_name)
    
    # Check all monster types
    for img_path in images:
        try:
            # Find all matches for this monster type
            locations = list(pyautogui.locateAllOnScreen(img_path, confidence=CONFIDENCE, grayscale=False))
            
            if locations:
                mob_name = os.path.basename(img_path)
                # Add all found instances to list with their distance from screen center
                for loc in locations:
                    center = pyautogui.center(loc)
                    # Calculate distance from screen center (Euclidean distance)
                    distance = ((center.x - screen_center_x) ** 2 + (center.y - screen_center_y) ** 2) ** 0.5
                    all_found_mobs.append((distance, center, mob_name))
        except pyautogui.ImageNotFoundException:
            continue
        except Exception as e:
            print(f"Error searching image: {e}")
            continue
    
    # If any mobs found, return the closest one
    if all_found_mobs:
        # Sort by distance (closest first)
        all_found_mobs.sort(key=lambda x: x[0])
        closest_distance, closest_center, closest_name = all_found_mobs[0]
        return closest_center, closest_name
    
    return None, None 

def main():
    print("Automatic monster hunting bot (ANTI-BAN & MULTI-TARGET VERSION).")
    print("------------------------------------------------------------------")
    
    monster_images = get_monster_images()
    
    if not monster_images:
        print(f"ERROR: No images found in '{MONSTERS_FOLDER}' folder!")
        input("\nPress Enter to exit...")
        sys.exit()
    
    print(f"Search list contains {len(monster_images)} different monster images:")
    for img in monster_images:
        print(f"- {os.path.basename(img)}")
        
    print("\nStarting bot... Press and hold 'Q' to stop.")
    print("Please switch to game window within 5 seconds...\n")
    
    time.sleep(5)
    print("Bot Started Running!")

    while True:
        if keyboard.is_pressed('q'):
            print("Bot stopped by user.")
            sys.exit()
            
        try:
            location, found_name = find_any_monster(monster_images)
            if location is not None:
                print(f"\n[{found_name}] ", end="", flush=True)
                
                # MAXIMUM SPEED
                human_like_move(location.x, location.y)
                human_like_click()
                time.sleep(0.05)  # Minimum wait
                
                # FAST SKILLS
                for skill in ['1', '2', '3', '4']:
                    human_like_press(skill)
                    time.sleep(0.15)  # Minimum skill interval
                
                time.sleep(0.2)  # Minimal wait for next mob 
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
