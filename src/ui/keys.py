import requests
import supervisely as sly

from supervisely.app.widgets import (
    Input,
    Card,
    Button,
    Container,
    Text,
    Select,
    Flexbox,
)

import src.globals as g
import src.ui.team as team
import src.ui.update as update

instance_select = Select(
    items=[Select.Item(value, label) for label, value in g.INSTANCES.items()],
    placeholder="Select target instance",
)

key_input = Input(type="password")

check_key_button = Button("Check connection")
change_instance_button = Button(
    "Change instance", icon="zmdi zmdi-swap-vertical-circle"
)
change_instance_button.hide()
buttons_flexbox = Flexbox([check_key_button, change_instance_button])

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
    "1️⃣ Instance",
    "Select the instance to which the data will be uploaded and enter the API key.",
    content=Container(
        widgets=[
            instance_select,
            key_input,
            buttons_flexbox,
            file_loaded_info,
            check_result,
        ],
        direction="vertical",
    ),
)


@check_key_button.click
def connect_to_target():
    """Checks the connection to the Target API with the specified API key."""
    check_result.hide()

    if not g.STATE.target_api_key:
        g.STATE.target_api_key = key_input.get_value()

    if not g.STATE.instance:
        g.STATE.instance = instance_select.get_value()

    try:
        g.STATE.target_api = sly.Api(
            server_address=g.STATE.instance,
            token=g.STATE.target_api_key,
            ignore_task_id=True,
        )
        global target_team_id
        g.STATE.target_api.team.get_info_by_name(g.TARGET_TEAM_NAME)
        sly.logger.info("The connection to the Target API was successful.")

    except (ValueError, requests.exceptions.HTTPError):
        g.STATE.target_api_key = None
        sly.logger.warning("The connection to the Target API failed.")
        check_result.text = "The connection to the Target API failed, check the key."
        check_result.status = "error"
        check_result.show()
        return

    if g.STATE.from_team_files:
        key_input.set_value(g.STATE.target_api_key)
        instance_select.hide()
        change_instance_button.hide()
        key_input.disable()
        instance_select.disable()
    else:
        change_instance_button.show()

    check_result.text = f"Successfully connected to: {g.STATE.instance}."
    check_result.status = "success"
    check_result.show()

    # Disabling fields for entering API key if the connection was successful.
    instance_select.disable()
    key_input.disable()
    check_key_button.hide()
    team.card.unlock()


@change_instance_button.click
def change_instance():
    instance_select.enable()
    key_input.enable()
    check_key_button.show()
    team.card.lock()
    update.card.lock()
    change_instance_button.hide()


g.key_from_file()
if g.STATE.target_api_key and g.STATE.instance:
    g.STATE.from_team_files = True
    connect_to_target()
    file_loaded_info.show()
