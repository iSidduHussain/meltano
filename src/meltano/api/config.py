import os
import logging
import datetime

from meltano.core.project import Project
from meltano.core.project_settings_service import (
    ProjectSettingsService,
    SettingValueSource,
)
from meltano.core.utils import truthy
from meltano.api.headers import *

# Flask
# -----------------
THREADS_PER_PAGE = 1
PROFILE = truthy(os.getenv("FLASK_PROFILE"))


# Meltano
# -----------------
MELTANO_UI_URL = os.getenv("MELTANO_UI_URL", "/")

API_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
TEMP_FOLDER = os.path.join(API_ROOT_DIR, "static/tmp")
PROJECT_ROOT_DIR = os.path.dirname(API_ROOT_DIR)

# Flask-SQLAlchemy
# -----------------
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Security
# -----------------

SECURITY_PASSWORD_HASH = "bcrypt"
SECURITY_REGISTERABLE = False
SECURITY_CHANGEABLE = True
SECURITY_RECOVERABLE = False
SECURITY_CONFIRMABLE = False
SECURITY_URL_PREFIX = "/auth"
SECURITY_USER_IDENTITY_ATTRIBUTES = ("username", "email")
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False

SECURITY_MSG_USERNAME_NOT_PROVIDED = ("You must provide a username.", "error")
SECURITY_MSG_USERNAME_INVALID = (
    "Username must be at least 6 characters long.",
    "error",
)
SECURITY_MSG_USERNAME_ALREADY_TAKEN = ("This username is already taken.", "error")

# Flask-RESTful
# -----------------

RESTFUL_JSON = {}

# Flask-Executor
# -----------------

EXECUTOR_PROPAGATE_EXCEPTIONS = True


# Flask-CORS
# -----------------

CORS_EXPOSE_HEADERS = [VERSION_HEADER]
CORS_ALLOW_HEADERS = ["CONTENT-TYPE", JSON_SCHEME_HEADER]


class ProjectSettings(object):
    settings_map = {
        "SERVER_NAME": "ui.server_name",
        "SECRET_KEY": "ui.secret_key",
        # Flask-Security
        "SECURITY_PASSWORD_SALT": "ui.password_salt",
        # Flask-SQLAlchemy
        "SQLALCHEMY_DATABASE_URI": "database_uri",
        # Flask-Authlib
        "GITLAB_CLIENT_ID": "oauth.gitlab.client_id",
        "GITLAB_CLIENT_SECRET": "oauth.gitlab.client_secret",
        # Flask-Mail
        "MAIL_SERVER": "mail.server",
        "MAIL_PORT": "mail.port",
        "MAIL_DEFAULT_SENDER": "mail.default_sender",
        "MAIL_USE_TLS": "mail.use_tls",
        "MAIL_USERNAME": "mail.username",
        "MAIL_PASSWORD": "mail.password",
        "MAIL_DEBUG": "mail.debug",
    }

    def __init__(self, project: Project):
        self.settings_service = ProjectSettingsService(project)

    def as_dict(self):
        return {
            config_key: self.settings_service.get(setting_name)
            for config_key, setting_name in self.settings_map.items()
        }


class Production(object):
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


def ensure_secure_setup(settings_service: ProjectSettingsService):
    secure_settings = ["ui.server_name", "ui.secret_key", "ui.password_salt"]

    facts = []
    env_vars = []
    for setting_name in secure_settings:
        setting_def = settings_service.find_setting(setting_name)
        env_var = settings_service.setting_env(setting_def)

        value, source = settings_service.get_with_source(setting_name)
        if value is None:
            facts.append(f"\t- '{setting_name}': setting is unset.")
            env_vars.append(f"\t- {env_var}")
        elif source is SettingValueSource.DEFAULT:
            facts.append(f"\t- '{setting_name}': setting has default test value.")
            env_vars.append(f"\t- {env_var}")

    if facts:
        facts_msg = "\n".join(facts)
        variable_names = "\n".join(env_vars)
        logging.warning(
            "The following settings are insecure and should be regenerated:\n"
            f"{facts_msg}\n\n"
            "Use `meltano ui setup` command to generate new secrets, or set them via environment variables:\n"
            f"{variable_names}"
        )
