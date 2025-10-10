import os
from collections.abc import Callable
from enum import StrEnum

import pytz  # type: ignore
from dotenv import load_dotenv


#  Singleton utils
class _Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# load .env variables if exists
load_dotenv()


# Enum for env mode
class MODE(StrEnum):
    DEV = "dev"
    PROD = "prod"

    @classmethod
    def has_member_key(cls, key):
        return key in cls.__members__


# utils to cast str env variables as int or float
def parse_environ(key: str, parse_method: Callable[[str], int | float], default: int | float):
    if key is None:
        raise ValueError(f"Key {key} is None")
    try:
        return parse_method(os.environ.get(key))  # type: ignore
    except Exception:
        return default


class Config(metaclass=_Singleton):
    # type sage configuration specification with default values coming from env variables or defaults
    data_path: str = os.environ.get("DATA_PATH", ".")
    user_hdd_max: float
    mode: MODE = os.environ.get("MODE", str(MODE.DEV))  # type: ignore
    secret_key: str = os.environ.get("SECRET_KEY", "Q__zz0ew00R_YSwCFl-6VgS9dPbfDtFDnzHfd57t0EY=")
    database_url: str
    root_password: str | None = os.environ.get("ROOT_PASSWORD", None)
    # orchestrator
    jwt_algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    max_loaded_projects: int
    n_workers_gpu: int
    n_workers_cpu: int
    update_timeout: int
    mail_server_port: int
    timezone: pytz.BaseTzInfo
    mail_available: bool = False
    default_user: str = "root"
    train_file: str = "train.parquet"
    test_file: str = "test.parquet"
    valid_file: str = "valid.parquet"
    features_file: str = "features.parquet"
    data_all: str = "data_all.parquet"
    file_models: str = "bert_models.csv"
    default_scheme: str = "default"
    mail_server: str | None = os.environ.get("MAIL_SERVER", None)

    mail_account: str | None = os.environ.get("MAIL_ACCOUNT", None)
    mail_password: str | None = os.environ.get("MAIL_PASSWORD", None)

    def __init__(self):
        # for variables which needs cast or other treatment we do that work in the constructor
        self.mode = (
            os.environ.get("MODE")
            if os.environ.get("MODE") is not None and MODE.has_member_key(os.environ.get("MODE"))
            else "dev"
        )
        self.user_hdd_max = parse_environ("ACTIVETIGGER_USER_HDD_MAX", float, 30.0)
        self.max_loaded_projects = parse_environ("MAX_LOADED_PROJECTS", int, 30)
        self.n_workers_gpu = parse_environ("N_WORKERS_GPU", int, 1)
        self.n_workers_cpu = parse_environ("N_WORKERS_CPU", int, 5)
        self.update_timeout = parse_environ("UPDATE_TIMEOUT", int, 1)
        self.database_url = os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(self.data_path, 'projects', 'activetigger.db')}",
        )
        self.model_path = os.environ.get("MODEL_PATH", os.path.join(self.data_path, "models"))
        self.timezone = pytz.timezone("Europe/Paris")
        if self.mail_server and self.mail_account and self.mail_password:
            self.mail_available = True
        self.mail_server_port = parse_environ("MAIL_SERVER_PORT", int, 465)


# the configuration is safe to share as it's a singleton (initialized only once)
config = Config()
