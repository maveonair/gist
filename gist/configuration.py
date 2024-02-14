from enum import Enum

from pydantic_settings import BaseSettings


class Environment(str, Enum):
    development = "development"
    testing = "testing"
    production = "production"


class Configuration(BaseSettings):
    github_token: str = ""
    environment: Environment = Environment.production
    db_url: str = "sqlite:///./gist.db"

    def is_production(self):
        return self.environment == Environment.production

    class Config:
        env_file = ".env"
