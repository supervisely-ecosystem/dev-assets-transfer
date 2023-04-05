import supervisely as sly

from supervisely.app.widgets import Container, Card, SelectTeam, Button, Text, Flexbox

import src.globals as g
import src.ui.update as update

warning_message = Text(status="warning")
warning_message.hide()

# Field with team selector.
team_select = SelectTeam(default_id=g.TEAM_ID)

load_button = Button("Compare data")
change_button = Button(
    "Change source", icon="zmdi zmdi-swap-vertical-circle", button_type="warning"
)
change_button.hide()

buttons_flexbox = Flexbox([load_button, change_button, update.upload_button])

card = Card(
    title="2️⃣ Compare and update",
    description="Select the source team, compare instances and update the data.",
    content=Container(
        [
            team_select,
            buttons_flexbox,
            warning_message,
        ],
        direction="vertical",
    ),
    lock_message="Enter the Target API key and check the connection on step 1️⃣.",
)
card.lock()


@load_button.click
def load_data():
    warning_message.hide()
    load_button.text = "Loading..."

    source_team_id = team_select.get_selected_id()
    if not source_team_id:
        warning_message.text = "Team is not selected."
        warning_message.show()
        return
    sly.logger.debug(f"Team level is selected. Team ID: {source_team_id}.")
    team_select.disable()

    update.card.unlock()

    update.team_difference(source_team_id)

    load_button.text = "Load data"
    load_button.hide()
    change_button.show()


@change_button.click
def change_source():
    warning_message.hide()
    load_button.show()
    team_select.enable()
    change_button.hide()
    update.card.lock()
