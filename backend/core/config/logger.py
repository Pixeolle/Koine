from enum import Enum

from pydantic import BaseModel


class LoggerLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    ERROR = 'ERROR'
    EXCEPTION = 'EXCEPTION'
    CRITICAL = 'CRITICAL'

class LoggerSettings(BaseModel):
    level: LoggerLevel
