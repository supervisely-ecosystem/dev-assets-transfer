import os
from collections import defaultdict

import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(__file__)
TMP_DIR = os.path.join(ABSOLUTE_PATH, "tmp")

# Path to the .env file, if the app is started from the team files.
ENV_FILE = os.path.join(ABSOLUTE_PATH, "target.env")

os.makedirs(TMP_DIR, exist_ok=True)

INSTANCES = {
    "Assets": "https://assets.supervisely.com/",
    "App": "https://app.supervise.ly/",
    "Dev": "https://dev.supervise.ly/",
}

# Indices of the fields in the image metadata to avoid hardcoding.
INDICES = {"images_ids": 0, "image_names": 1, "image_metas": 13}

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
source_api: sly.Api = sly.Api.from_env()

TEAM_ID = sly.io.env.team_id()
WORKSPACE_ID = sly.io.env.workspace_id()

# Default settings for uploading primitives to Assets.
DEFAULT_TEAM_NAME = "primitives"
DEFAULT_TAG_NAME = "inference"
DEFAULT_ANNOTATION_TYPES = ["bitmap"]

# Path to the JSON file which is generated after comparsion of the teams is finished.
DIFFERENCES_JSON = os.path.join(TMP_DIR, "team_differences.json")
ERROR_JSON = os.path.join(TMP_DIR, "error.json")

BATCH_SIZE = 100
GEOMETRIES = ["bitmap", "polygon", "polyline", "rectangle"]


class State:
    """Class for storing global variables across the app in one place."""

    def __init__(self):
        # Address of the target instance.
        self.instance = None
        self.target_team_name = None
        self.target_api_key = None
        # API object for the target instance, icludes API key and instance address.
        self.target_api = None
        # If the app was SUCCESSFULLY launched from the TeamFiles.
        self.from_team_files = False
        # False if the cancel button was clicked, True otherwise.
        self.continue_comparsion = True
        # False if the cancel button was clicked, True otherwise.
        self.continue_upload = True

        self.normalize_image_metadata = True

        # Counters for GUI widgets.
        self.annotated_images = 0
        self.tagged_images = 0
        self.uploaded_annotated_images = 0
        self.uploaded_tagged_images = 0

        # Default settings for uploading primitives to Assets.
        self.default_settings = True

        # Determines if the images should be filtered by annotation types or by tag names.
        # If both are False, all images will be uploaded.
        self.filter_by_annotation_type = True
        self.filter_by_tag_name = True

        # Tag name for filtering images.
        self.tag_name = ""

        # Annotation types for filtering images.
        self.annotation_types = []

        self.error_report = defaultdict(list)

    def reset_counters(self):
        """Resets counters for GUI widgets."""
        self.annotated_images = 0
        self.tagged_images = 0
        self.uploaded_annotated_images = 0
        self.uploaded_tagged_images = 0

        self.error_report.clear()


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
