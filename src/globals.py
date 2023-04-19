import os

import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(__file__)
TMP_DIR = os.path.join(ABSOLUTE_PATH, "tmp")

# Directory where temporary downloaded images will be stored.
IMAGES_DIR = os.path.join(TMP_DIR, "images")

# Path to the .env file, if the app is started from the team files.
ENV_FILE = os.path.join(ABSOLUTE_PATH, "target.env")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

INSTANCES = {
    "Assets": "https://assets.supervise.ly/",
    "App": "https://app.supervise.ly/",
    "Dev": "https://dev.supervise.ly/",
}

# Indices of the fields in the image metadata to avoid hardcoding.
INDICES = {"images_ids": 0, "image_names": 1, "image_metas": 13}

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
source_api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()

# Name of the target team name, which will be shown in the input widget by default.
# Impacts only on the default value in widget, not on the actual team name.
TARGET_TEAM_NAME = "primitives"

# Path to the JSON file which is generated after comparsion of the teams is finished.
DIFFERENCES_JSON = os.path.join(TMP_DIR, "team_differences.json")

# Tag name, which is using for sorting images in the project.
TAG = "inference"
BATCH_SIZE = 100


class State:
    """Class for storing global variables across the app in one place."""

    def __init__(self):
        self.instance = None
        self.target_team_name = None
        self.target_api_key = None
        self.target_api = None
        self.from_team_files = False
        self.continue_comparsion = True
        self.continue_upload = True
        self.normalize_image_metadata = True
        self.annotated_images = 0
        self.tagged_images = 0
        self.uploaded_annotated_images = 0
        self.uploaded_tagged_images = 0

    def reset_counters(self):
        self.annotated_images = 0
        self.tagged_images = 0
        self.uploaded_annotated_images = 0
        self.uploaded_tagged_images = 0


STATE = State()


def key_from_file():
    """Tries to load Target API key and the instance address from the team files."""
    try:
        # Get target.env from the team files.
        INPUT_FILE = sly.env.file(True)
        source_api.file.download(TEAM_ID, INPUT_FILE, ENV_FILE)
        sly.logger.info(f"Target API key file was downloaded to {ENV_FILE}.")

        # Read Target API key from the file.
        load_dotenv(ENV_FILE)
        STATE.target_api_key = os.environ["TARGET_API_TOKEN"]
        STATE.instance = os.environ["TARGET_SERVER_ADDRESS"]

        sly.logger.info("Target API key and instance were loaded from the team files.")
    except Exception:
        sly.logger.info(
            "No file with Target API key was provided, starting in input mode."
        )
