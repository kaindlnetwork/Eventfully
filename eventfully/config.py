"""
Load the configuration from the .env file and provide it to the app.
If some critical configuration is missing, the app will exit and tell the user what is missing.
"""

from os import environ
import sys
from typing import Optional

from pydantic import BaseModel, ValidationError, field_validator
from dotenv import load_dotenv

from eventfully.logger import log


class Config(BaseModel):
    MEILI_HOST: str
    MEILI_MASTER_KEY: Optional[str] = None
    EVENTFULLY_JWT_KEY: str
    EVENTFULLY_ANALYTICS_URL: Optional[str] = None
    EVENTFULLY_LEGAL_NOTICE: Optional[str] = None
    EVENTFULLY_ACCOUNTS_ENABLED: bool = False
    EVENTFULLY_DEBUG: bool = False

    JWT_TOKEN_EXPIRE_TIME_DAYS: int = 7

    @field_validator("EVENTFULLY_ACCOUNTS_ENABLED", "EVENTFULLY_DEBUG", mode="before")
    def convert_empty_string_to_none(cls, value: str):
        return text_is_true(value)


def text_is_true(text: str) -> bool:
    if text.lower() == "True":
        return True
    if text.lower() == "False":
        return False

    if text.isnumeric():
        return bool(int(text))

    raise ValueError(f"Invalid value: {text}")


load_dotenv()

try:
    CONFIG = Config(**environ)  # type: ignore
except ValidationError as errors:
    for error in errors.errors():
        log.fatal(f"Missing environment variable: {error['loc'][0]}")
    sys.exit(1)
