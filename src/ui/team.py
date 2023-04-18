import supervisely as sly

from supervisely.app.widgets import (
    Container,
    Card,
    SelectTeam,
    Button,
    Text,
    Flexbox,
    Input,
    Progress,
)

import src.globals as g
import src.ui.update as update

warning_message = Text(status="warning")
warning_message.hide()

# Field with team selector.
team_select = SelectTeam(default_id=g.TEAM_ID)

target_team_input = Input(
    value=g.TARGET_TEAM_NAME, minlength=1, placeholder="Enter target team name"
)

load_button = Button("Compare data")
cancel_button = Button("Cancel", button_type="danger", icon="zmdi zmdi-close-circle-o")
change_button = Button("Change source", icon="zmdi zmdi-swap-vertical-circle")
cancel_button.hide()
change_button.hide()

refresh_button = Button("Refresh", icon="zmdi zmdi-refresh-alt", button_type="success")
refresh_button.hide()

buttons_flexbox = Flexbox([load_button, cancel_button, change_button, refresh_button])

compare_progress = Progress()

card = Card(
    title="2️⃣ Compare data",
    description="Select the source team, enter the target team name and lanuch the comparison.",
    content=Container(
        [
            team_select,
            target_team_input,
            buttons_flexbox,
            warning_message,
            compare_progress,
            update.comparsion_texts,
        ],
        direction="vertical",
    ),
    lock_message="Enter the Target API key and check the connection on step 1️⃣.",
)
card.lock()


@load_button.click
def load_data():
    g.STATE.continue_comparsion = True

    warning_message.hide()

    source_team_id = team_select.get_selected_id()
    g.STATE.target_team_name = target_team_input.get_value()

    if not g.STATE.target_team_name:
        warning_message.text = "Target team name is not specified."
        warning_message.show()
        return

    sly.logger.debug(f"Team with ID {source_team_id} is selected.")
    load_button.text = "Comparing..."
    team_select.disable()
    target_team_input.disable()
    change_button.hide()

    cancel_button.show()
    update.upload_button.hide()

    update.team_difference(source_team_id)

    if g.STATE.continue_comparsion:
        update.card.unlock()
        load_button.hide()
        cancel_button.hide()
        refresh_button.show()
        update.upload_button.show()
    else:
        update.difference_text.hide()
        update.card.lock()
        compare_progress.hide()

        warning_message.text = "The comparison was canceled."
        warning_message.show()

    change_button.show()
    load_button.text = "Compare data"


@refresh_button.click
def refresh_data():
    refresh_button.hide()
    change_button.hide()
    load_button.show()
    load_button.loading = True
    load_data()
    load_button.loading = False


@change_button.click
def change_source():
    warning_message.hide()
    refresh_button.hide()
    load_button.show()
    team_select.enable()
    target_team_input.enable()
    change_button.hide()
    update.card.lock()


@cancel_button.click
def cancel_process():
    g.STATE.continue_comparsion = False
    cancel_button.hide()
