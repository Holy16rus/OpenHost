import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class UserbotStatus:
    ON = "on"
    OFF = "off"


class Database:
    def __init__(self):
        db_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(db_dir, "config.json")
        self.data = self.load_data()

    def load_data(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки config.json: {e}")
        return {"BotToken": None, "owner_id": None, "trusted_users": [], "pending_requests": [], "userbots": {}}

    def save_data(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения config.json: {e}")

    def get_token(self) -> Optional[str]:
        return self.data.get("BotToken")

    def set_token(self, token: str):
        self.data["BotToken"] = token
        self.save_data()

    def get_owner_id(self) -> Optional[int]:
        return self.data.get("owner_id")

    def set_owner(self, user_id: int) -> bool:
        if self.get_owner_id() is None:
            self.data["owner_id"] = user_id
            if user_id not in self.data["trusted_users"]:
                self.data["trusted_users"].append(user_id)
            self.save_data()
            return True
        return False

    def is_owner(self, user_id: int) -> bool:
        return self.get_owner_id() == user_id

    def is_trusted(self, user_id: int) -> bool:
        return user_id in self.data.get("trusted_users", [])

    def add_trusted_user(self, user_id: int):
        if user_id not in self.data["trusted_users"]:
            self.data["trusted_users"].append(user_id)
            self.save_data()

    def remove_trusted_user(self, user_id: int):
        if user_id in self.data["trusted_users"]:
            self.data["trusted_users"].remove(user_id)
            self.save_data()

    def has_pending_request(self, user_id: int) -> bool:
        return user_id in self.data.get("pending_requests", [])

    def add_pending_request(self, user_id: int):
        if user_id not in self.data.setdefault("pending_requests", []):
            self.data["pending_requests"].append(user_id)
            self.save_data()

    def clear_pending_request(self, user_id: int):
        pending = self.data.get("pending_requests", [])
        if user_id in pending:
            pending.remove(user_id)
            self.save_data()

    def add_userbot(self, name: str, user_id: int, created_by: str) -> bool:
        userbots = self.data.setdefault("userbots", {})
        if name in userbots:
            return False

        userbots[name] = {
            "name": name,
            "user_id": user_id,
            "created_by": created_by,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "status": UserbotStatus.OFF,
            "path": "",
            "local_port": None,
            "registration_url": ""
        }
        self.save_data()
        return True

    def get_user_userbots(self, user_id: int) -> List[dict]:
        userbots = self.data.get("userbots", {})
        return [ub for ub in userbots.values() if ub["user_id"] == user_id]

    def get_all_userbots(self) -> List[dict]:
        return list(self.data.get("userbots", {}).values())

    def get_userbot(self, name: str) -> Optional[dict]:
        return self.data.get("userbots", {}).get(name)

    def update_userbot_path(self, name: str, path: str) -> bool:
        userbots = self.data.get("userbots", {})
        if name in userbots:
            userbots[name]["path"] = path
            self.save_data()
            return True
        return False

    def update_userbot_status(self, name: str, status: str) -> bool:
        userbots = self.data.get("userbots", {})
        if name in userbots:
            userbots[name]["status"] = status
            self.save_data()
            return True
        return False

    def update_userbot_registration(self, name: str, port: int, url: str) -> bool:
        userbots = self.data.get("userbots", {})
        if name in userbots:
            userbots[name]["local_port"] = port
            userbots[name]["registration_url"] = url
            self.save_data()
            return True
        return False

    def delete_userbot(self, name: str) -> bool:
        userbots = self.data.get("userbots", {})
        if name in userbots:
            del userbots[name]
            self.save_data()
            return True
        return False


db = Database()
