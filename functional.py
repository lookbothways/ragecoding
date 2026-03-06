import tkinter as tk
from pynput import mouse, keyboard
import time
import math
import random
import string
import threading

# --- CONFIGURATION ---
TIME_LIMIT = 60  # Bumped to 60 seconds so you can play with the dropdown
is_running = True

# --- THE SOTA MODEL RANKINGS ---
# Best (2.0) to Worst (20.0)
AI_MODELS = {
    "Claude 3.7 Sonnet": 2.0,
    "OpenAI o3-mini": 4.0,
    "GPT-4.5": 6.0,
    "DeepSeek R1": 8.0,
    "Gemini 1.5 Pro": 10.0,
    "Llama 3.3 70B": 12.0,
    "Grok 3": 14.0,
    "Mistral Large": 16.0,
    "Claude 2.1": 18.0,
    "GPT-3.5 Turbo": 20.0
}

# --- STATE VARIABLES ---
current_multiplier = 10.0  # Default starting value
last_mouse_pos = None
is_shoving = False
injected_keys = []
current_modifiers = {'ctrl': False}

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()


def get_amount():
    """Wave from 0.1 to 1.0 driving the underlying 'rage' cycle"""
    return (math.sin(time.time() * 2) + 1) / 2 * 0.9 + 0.1


def stop_app():
    global is_running
    if not is_running: return
    is_running = False
    print("Gracefully exiting...")
    try:
        root.quit()
        root.destroy()
    except Exception:
        pass


def inject_wrong_char(original_char):
    time.sleep(0.02)
    keyboard_controller.press(keyboard.Key.backspace)
    keyboard_controller.release(keyboard.Key.backspace)

    wrong = random.choice(string.ascii_lowercase)
    if original_char.isupper(): wrong = wrong.upper()

    injected_keys.append(wrong)
    keyboard_controller.tap(wrong)


def on_press(key):
    if not is_running: return False

    if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        current_modifiers['ctrl'] = True

    try:
        c = key.char
        if c is None: return

        # Ctrl + S Graceful Exit
        if current_modifiers['ctrl'] and c in ('s', 'S', '\x13'):
            root.after(0, stop_app)
            return

        if c in injected_keys:
            injected_keys.remove(c)
            return

        if not current_modifiers['ctrl'] and c.isalpha() and c in string.ascii_letters:
            amount = get_amount()

            # FEATURE 1: Keyboard uses exactly HALF the multiplier of the mouse!
            kb_multiplier = current_multiplier / 2.0
            typo_chance = min(0.95, 0.15 * amount * kb_multiplier)

            if random.random() < typo_chance:
                threading.Thread(target=inject_wrong_char, args=(c,)).start()

    except AttributeError:
        pass


def on_release(key):
    if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        current_modifiers['ctrl'] = False


def shove_mouse(jx, jy):
    global is_shoving
    is_shoving = True
    time.sleep(0.01)
    mouse_controller.move(int(jx), int(jy))
    time.sleep(0.05)
    is_shoving = False


def on_move(x, y):
    global last_mouse_pos
    if not is_running: return False

    if is_shoving:
        last_mouse_pos = (x, y)
        return

    if last_mouse_pos is not None:
        dx = x - last_mouse_pos[0]
        dy = y - last_mouse_pos[1]
        distance = math.hypot(dx, dy)

        if distance > 2.0:
            amount = get_amount()

            # FEATURE 1: Mouse uses the FULL multiplier
            base_jitter = 2.0 * amount * current_multiplier
            intensity = min(150.0, distance * amount * current_multiplier)

            low_bound = min(base_jitter, intensity)
            high_bound = max(base_jitter, intensity) + 1.0

            jx = random.uniform(low_bound, high_bound) * random.choice([-1, 1])
            jy = random.uniform(low_bound, high_bound) * random.choice([-1, 1])

            threading.Thread(target=shove_mouse, args=(jx, jy)).start()

    last_mouse_pos = (x, y)


# --- GUI SETUP ---
root = tk.Tk()
root.title("Rage")
root.overrideredirect(True)
root.attributes("-topmost", True)

# Expand window to fit the button and the dropdown side-by-side
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
pos_x = int(screen_width * 0.2)
pos_y = int(screen_height * 0.8)
root.geometry(f"220x60+{pos_x}+{pos_y}")

# Main container frame
main_frame = tk.Frame(root, bg="gray20")
main_frame.pack(fill="both", expand=True, padx=2, pady=2)

# Left Side: The Big Red Stop Button
btn = tk.Button(main_frame, text="STOP", bg="red", fg="white",
                font=("Arial", 12, "bold"), command=stop_app)
btn.pack(side="left", fill="y", ipadx=5)

# Right Side: The Dropdown Area
right_frame = tk.Frame(main_frame, bg="gray20")
right_frame.pack(side="right", fill="both", expand=True)

lbl = tk.Label(right_frame, text="Current model", font=("Arial", 8, "bold"),
               bg="gray20", fg="white")
lbl.pack(side="top", pady=(2, 0))

# Dropdown setup
selected_model = tk.StringVar(value="Gemini 1.5 Pro")  # Starts at 10.0 (Medium Rage)


def on_model_change(*args):
    global current_multiplier
    current_multiplier = AI_MODELS[selected_model.get()]
    print(f"Model swapped to {selected_model.get()}! Multiplier: {current_multiplier}")


selected_model.trace_add("write", on_model_change)

dropdown = tk.OptionMenu(right_frame, selected_model, *AI_MODELS.keys())
dropdown.config(font=("Arial", 8), width=15)
dropdown.pack(side="bottom", fill="x", padx=2, pady=(0, 2))

# --- STARTUP ---
ml = mouse.Listener(on_move=on_move)
kl = keyboard.Listener(on_press=on_press, on_release=on_release)
ml.start()
kl.start()

root.after(TIME_LIMIT * 1000, stop_app)
root.mainloop()

ml.stop()
kl.stop()