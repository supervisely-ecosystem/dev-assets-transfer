import os

from typing import Optional

import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(__file__)
TMP_DIR = os.path.join(ABSOLUTE_PATH, "tmp")
IMAGES_DIR = os.path.join(TMP_DIR, "images")
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

INDICES = {"images_ids": 0, "image_names": 1, "image_metas": 13}

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
source_api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()

TARGET_SERVER_ADDRESS = "localhost"
TARGET_TEAM_NAME = "Assets2"

LEVELS = ["team", "workspace", "project", "image"]
TAG = "inference"
BATCH_SIZE = 10


def key_from_file() -> Optional[str]:
    """Tries to load Target API key from the team files.
    Returns:
        Optional[str]: returns Target API key if it was loaded successfully, None otherwise.
    """
    try:
        # Get target.env from the team files.
        INPUT_FILE = sly.env.file(True)
        source_api.file.download(TEAM_ID, INPUT_FILE, "target.env")

        # Read Target API key from the file.
        load_dotenv("target.env")
        TARGET_API_KEY = os.environ["TARGET_API_KEY"]

        sly.logger.info("Target API key was loaded from the team files.")
        return TARGET_API_KEY
    except Exception:
        sly.logger.info(
            "No file with Target API key was provided, starting in input mode."
        )
