import os
import json

SETTINGS_PATH = os.path.join(os.getenv("LOCALAPPDATA") or os.path.expanduser("~"), "PiniX", "settings.json")

class Settings:
    def __init__(self):
        # Default settings mimicking the original gsettings schema
        self.config = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "http-referer": "",
            "providers": ["Free-TV:::url:::https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8::::::"]
        }
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                try:
                    loaded = json.load(f)
                    self.config.update(loaded)
                except Exception as e:
                    print("Error loading settings:", e)
        else:
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get_string(self, key):
        return str(self.config.get(key, ""))
        
    def get_strv(self, key):
        return self.config.get(key, [])

    def set_string(self, key, value):
        self.config[key] = value
        self.save()

    def set_strv(self, key, value):
        self.config[key] = list(value)
        self.save()
