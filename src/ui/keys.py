import requests
import supervisely as sly

from supervisely.app.widgets import Input, Card, Button, Container, Text

import src.globals as g
import src.ui.team as team

key_input = Input(type="password")

check_key_button = Button("Check connection")

# Message which is shown if the API key was loaded from the team files.
file_loaded_info = Text(
    text="The API key was loaded from the team files.", status="info"
)
file_loaded_info.hide()

# Message which is shown after the connection check.
check_result = Text()
check_result.hide()

# Main card with all keys widgets.
card = Card(
    "1️⃣ Target API key",
    "Please, enter your Target API key.",
    content=Container(
        widgets=[key_input, check_key_button, file_loaded_info, check_result],
        direction="vertical",
    ),
)


@check_key_button.click
def connect_to_target():
    """Checks the connection to the Target API with the global API key."""
    check_result.hide()

    global target_api_key
    if not target_api_key:
        target_api_key = key_input.get_value()

    try:
        global target_api
        target_api = sly.Api(
            server_address=g.TARGET_SERVER_ADDRESS, token=target_api_key
        )
        global target_team_id
        target_api.team.get_info_by_name(g.TARGET_TEAM_NAME)
        sly.logger.info("The connection to the Target API was successful.")

    except (ValueError, requests.exceptions.HTTPError):
        target_api_key = None
        sly.logger.warning("The connection to the Target API failed.")
        check_result.text = "The connection to the Target API failed, check the key."
        check_result.status = "error"
        check_result.show()
        return

    check_result.text = "The connection to the Target API was successful."
    check_result.status = "success"
    check_result.show()

    # Disabling fields for entering API key if the connection was successful.
    key_input.disable()
    check_key_button.hide()
    team.card.unlock()


global target_api_key
target_api_key = g.key_from_file()
if target_api_key:
    # If the API key was loaded from the team files, launching the connection check.
    check_key_button.click(connect_to_target())
    key_input.hide()
    file_loaded_info.show()
