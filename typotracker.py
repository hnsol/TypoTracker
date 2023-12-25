from pynput import keyboard
import yaml
import os
import time
import threading
import datetime
import subprocess

# Default configuration values
DEFAULT_CONFIG = {
    "log_file_path": "~/typotracker_log.txt",
    "keyboard_name": "standard keyboard",
    "trigger_key": {
        "ctrl": False,
        "shift": True,
        "alt": False,
        "cmd": True,
        "key": ';'
    },
    "notification_type": "None",
    "debug_mode": False,
    "timer_delay": 0,
    "max_size": 1000,
    "additional_window_size": 12
}

def load_config(config_file_path):
    try:
        with open(config_file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Configuration file '{config_file_path}' not found. Using default settings.")
        return DEFAULT_CONFIG
    except yaml.YAMLError as error:
        print(f"Error reading '{config_file_path}': {error}")
        return DEFAULT_CONFIG
    except Exception as error:
        print(f"Unexpected error occurred: {error}")
        return DEFAULT_CONFIG

# Read config file
config_file_path = 'ttconfig.yaml'
config = load_config(config_file_path)

# Set configuration values
LOG_FILE_PATH = config.get('log_file_path', DEFAULT_CONFIG["log_file_path"])
LOG_FILE_PATH = os.path.expanduser(LOG_FILE_PATH)
TRIGGER_KEY_CONFIG = config.get('trigger_key', DEFAULT_CONFIG["trigger_key"])
NOTIFICATION_TYPE = config.get('notification_type', DEFAULT_CONFIG["notification_type"])
DEBUG_MODE = config.get('debug_mode', DEFAULT_CONFIG["debug_mode"])
TIMER_DELAY = config.get('timer_delay', DEFAULT_CONFIG["timer_delay"])
MAX_SIZE = config.get('max_size', DEFAULT_CONFIG["max_size"])
ADDITIONAL_WINDOW_SIZE = config.get('additional_window_size', DEFAULT_CONFIG["additional_window_size"])


# Set keyboard name
default_keyboard_name = config.get('keyboard_name', DEFAULT_CONFIG["keyboard_name"])
KEYBOARD_NAME = input(f"Enter keyboard name ({default_keyboard_name}): ") or default_keyboard_name


if DEBUG_MODE:
    print(f"[DEBUG] config loaded: {config}")


# Function to confirm keybind
def is_trigger_key_pressed(pressed_keys, trigger_key_config):
    ctrl = trigger_key_config.get("ctrl", False)
    shift = trigger_key_config.get("shift", False)
    alt = trigger_key_config.get("alt", False)
    cmd = trigger_key_config.get("cmd", False)
    key = trigger_key_config.get("key", None)

    trigger_key = trigger_key_config.get("key", None)
    if trigger_key is not None and trigger_key not in pressed_keys:
        return False

    return ((keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys) == ctrl and
            (keyboard.Key.shift in pressed_keys) == shift and
            (keyboard.Key.alt in pressed_keys) == alt and
            (keyboard.Key.cmd in pressed_keys) == cmd)


def send_notification(title, message):
    if NOTIFICATION_TYPE == 'macOS':
        # for macOS notifications
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
    elif NOTIFICATION_TYPE == 'Windows':
        # for Windows notifications (for future extension)
        pass
    elif NOTIFICATION_TYPE == 'Linux':
        # for Linux notifications (for future extension)
        pass
    # no notifications when other cases
    

# Function to extract context from key logs
def extract_last_context(key_log, additional_window_size=ADDITIONAL_WINDOW_SIZE):
    fire_count = 0
    i = len(key_log) - 1
    while i >= 0:
        if key_log[i] == '🔥':
            fire_count += 1
            i -= 1
        else:
            if fire_count >= 2:
                start = max(0, i - fire_count * 2 - additional_window_size)
                end = min(i + fire_count * 2 + additional_window_size, len(key_log))
                context = key_log[start:end]
                return context
            fire_count = 0
            i -= 1
    return None


# TypingLogger class to monitor and log keystrokes
class TypingLogger:
    def __init__(self, debug=False):
        self.recording = True
        self.last_key_time = 0
        self.key_log = []
        self.ctrl_pressed = False
        self.debug = debug
        self.timer_active = False
        self.timer_delay = TIMER_DELAY
        self.trigger_key_config = TRIGGER_KEY_CONFIG
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.pressed_keys = set()

    def on_press(self, key):
        if self.debug:
            try:
                print(f"[DEBUG] Key pressed: {key.char}")
            except AttributeError:
                print(f"[DEBUG] Special key pressed: {key}")

        try:
            self.pressed_keys.add(key.char)
        except AttributeError:
            self.pressed_keys.add(key)

        if is_trigger_key_pressed(self.pressed_keys, self.trigger_key_config):

            if not self.timer_active:
                self.timer_active = True
                threading.Timer(self.timer_delay, self.process_log).start()
                if self.debug:
                    print(f"[DEBUG] Timer activated for processing log...")
            return

        if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            self.ctrl_pressed = True
        elif self.ctrl_pressed:
            if hasattr(key, 'char'):
                if key.char == 'h':
                    self.key_log.append('🔥')
                else:
                    self.key_log.append(f'Ctrl+{key.char}')
            else:
                key_name = str(key).replace('Key.', '(Key.') + ')'
                self.key_log.append(f'Ctrl+{key_name}')
        elif key == keyboard.Key.backspace:
            self.key_log.append('🔥')
        else:
            try:
                self.key_log.append(key.char)
            except AttributeError:
                key_name = str(key).replace('Key.', '(Key.') + ')'
                self.key_log.append(key_name)

        if len(self.key_log) > MAX_SIZE:
            self.key_log = self.key_log[len(self.key_log) // 2:]
        
        if self.debug:
            print(f"[DEBUG] Current key log size: {len(self.key_log)} | Contents: {self.key_log}")

    def on_release(self, key):
        if self.debug:
            try:
                print(f"[DEBUG] Key released: {key.char}")
            except AttributeError:
                print(f"[DEBUG] Special key released: {key}")

        # Properly handle special and regular key
        try:
            self.pressed_keys.discard(key.char)
        except AttributeError:
            self.pressed_keys.discard(key)

        # Update the state of the Ctrl key
        if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            self.ctrl_pressed = False
            if self.debug:
                print(f"[DEBUG] Ctrl key released")

    def process_log(self):
        context = extract_last_context(self.key_log)
        if context:
            timestamp = (datetime.datetime.now() - datetime.timedelta(seconds=self.timer_delay)).strftime("%Y-%m-%d %H:%M:%S")
            log_data = f"({timestamp}) ({KEYBOARD_NAME}): {''.join(context)}\n"
            with open(LOG_FILE_PATH, 'a', encoding='utf-8') as file:
                file.write(log_data)
            if self.debug:
                print(f"[DEBUG] Logged data: {log_data}")
            
            # send notification
            send_notification("TypoTracker", f"Log saved: {log_data}")
        else:
            if self.debug:
                print("[DEBUG] No relevant context for logging.")
        
        self.reset_log()
        self.timer_active = False

    def reset_log(self):
        self.key_log = []
        if self.debug:
            print("[DEBUG] Logger state reset")

    def start(self):
        self.listener.start()

def main():
    print("Script started")
    logger = TypingLogger(debug=DEBUG_MODE)
    logger.start()
    logger.listener.join()

if __name__ == "__main__":
    main()
    print("Script stopped")
