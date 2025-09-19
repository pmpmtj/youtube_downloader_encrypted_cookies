"""
Application configuration module.

"""

import logging


# Initialize logger for this module
logger = logging.getLogger("app_config")

# Application configuration for Youtube downloader
APP_CONFIG = {
    "audio": {
        "save_to_mp3": "True",
        "remove_original": "False"
    }
}

