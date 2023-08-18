import requests
import supervisely as sly

from supervisely.app.widgets import (
    Input,
    Card,
    Button,
    Container,
    Text,
    Select,
    Field,
)

import src.globals as g
import src.ui.compare as compare
import src.ui.update as update

# Instance selector.
instance_select = Select(
    items=[Select.Item(value, label) for label, value in g.INSTANCES.items()],
    placeholder="Select target instance",
)

custom_instance_adress_input = Input(placeholder="Enter custom instance address")
custom_instance_adress_field = Field(
    title="Enter instance address",
    description="For example: https://app.supervise.ly/",
    content=custom_instance_adress_input,
)
custom_instance_adress_field.hide()

# Input widget for the API key, characters will be hidden.
key_input = Input(type="password")

# Flexbox for all buttons.
check_key_button = Button("Check connection")
change_instance_button = Button(
    "Change instance", icon="zmdi zmdi-swap-vertical-circle"
)
change_instance_button.hide()

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
            custom_instance_adress_field,
            key_input,
            check_key_button,
            file_loaded_info,
            check_result,
        ],
        direction="vertical",
    ),
    content_top_right=change_instance_button,
    collapsable=True,
)


@check_key_button.click
def connect_to_target():
    """Checks the connection to the selected instance with specified API key."""
    check_result.hide()

    if not g.STATE.target_api_key:
        # Reading the API key from the input widget, if it was not loaded from the team files.
        g.STATE.target_api_key = key_input.get_value()

    if not g.STATE.instance:
        # Reading the instance address from the select widget, if it was not loaded from the team files.
        selected_instance = instance_select.get_value()
        if selected_instance == "Custom":
            g.STATE.instance = custom_instance_adress_input.get_value()
        else:
            g.STATE.instance = instance_select.get_value()

    try:
        g.STATE.target_api = sly.Api(
            server_address=g.STATE.instance,
            token=g.STATE.target_api_key,
            ignore_task_id=True,
        )
        g.STATE.target_api.team.get_info_by_name(g.DEFAULT_TEAM_NAME)
        sly.logger.info("The connection to the Target API was successful.")

    except (ValueError, requests.exceptions.HTTPError):
        g.STATE.target_api_key = None
        sly.logger.warning("The connection to the Target API failed.")
        check_result.text = "The connection to the Target API failed, check the key."
        check_result.status = "error"
        check_result.show()
        return

    if g.STATE.from_team_files:
        # If the app was started from the team files, making changes in the GUI state.
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
    # instance_select.disable()
    # key_input.disable()
    card.lock()

    check_key_button.hide()
    compare.card.unlock()


@change_instance_button.click
def change_instance():
    """Handles the change instance button click event."""
    card.unlock()
    # instance_select.enable()
    # key_input.enable()
    check_key_button.show()
    update.card.lock()
    update.card.lock()
    change_instance_button.hide()


g.key_from_file()
# Trying to load the API key and instance address from the team files.
if g.STATE.target_api_key and g.STATE.instance:
    g.STATE.from_team_files = True
    connect_to_target()
    file_loaded_info.show()


@instance_select.value_changed
def instance_chaned(instance):
    print(instance)
    if instance == "Custom":
        custom_instance_adress_field.show()
    else:
        custom_instance_adress_field.hide()
