from configparser import RawConfigParser
from typing import Optional, Any
import json

class Config:
    def __init__(self, config_path: str = "./settings.conf"):
        self.config = RawConfigParser()
        self.config.read(config_path)
        self.config_path = config_path
        # all expected config values

        # Setup
        self.require_auth = self._getbool("setup", "require_auth")
        self.reset_default_user = self._getbool("setup", "reset_default_user")
        self.erase_database_on_reset = self._getbool("setup", "erase_database_on_reset")

        # General
        self.use_https = self._getbool("general", "use_https")
        self.restart_required = self._getbool("general", "restart_required")
        self.jwt_expire_time = self._get("general", "jwt_expire_time")
        self.secret_session_token = self._get("general", "secret_session_token")

        # Database
        self.database_url = self._get("database", "database_url")
        self.database_name = self._get("database", "database_name")
        self.database_creds = self._get("database", "database_creds")
        self.database_type = self._get("database", "database_type")
            
        # AI
        self.model_type = self._get("ai", "model_type").lower()
        self.modal_name = self._get("ai", "modal_name").lower()
        self.endpoint_url = self._get("ai", "endpoint_url")
        self.endpoint_port = self._getint("ai", "endpoint_port")
        self.openai_api_key = self._get("ai", "OPENAI_API_KEY")
        self.prompt_presets_path = self._get("ai", "prompt_presets_path")


    def _get(self, section: str, key: str, fallback: str = None) -> str:
        return self.config.get(section, key, fallback=fallback)

    def _getint(self, section: str, key: str, fallback: int = None) -> int:
        return self.config.getint(section, key, fallback=fallback)

    def _getfloat(self, section: str, key: str, fallback: float = None) -> float:
        return self.config.getfloat(section, key, fallback=fallback)

    def _getbool(self, section: str, key: str, fallback: bool = None) -> bool:
        return self.config.getboolean(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)

    def save(self):
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)

    def export_as_dict(self) -> dict:
        """Exports config as a Python dictionary."""
        return {section: dict(self.config.items(section)) for section in self.config.sections()}

    @property
    def database_full_url(self) -> str:
        """get a sqlalc compatible db URI based on the config."""
        db_type = self.database_type.lower()

        if db_type == "postgres":
            return f"postgresql://{self.database_creds}@{self.database_url}/{self.database_name}"
        elif db_type in ("mysql", "mariadb"):
            return f"mysql+pymysql://{self.database_creds}@{self.database_url}/{self.database_name}"
        elif db_type == "sqlite":
            return f"sqlite:///{self.database_url}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")
        
    @property
    def is_async(self) -> bool:
        """see if the current driver is async."""
        return any(proto in self.database_full_url for proto in ["+asyncpg", "+aiomysql", "+aiosqlite"])