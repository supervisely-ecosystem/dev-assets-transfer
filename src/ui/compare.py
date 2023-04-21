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
    Field,
)

import src.globals as g
import src.ui.update as update

# Message, that will shown if any error occurs.
warning_message = Text(status="warning")
warning_message.hide()

# Team selector.
team_select = SelectTeam(default_id=g.TEAM_ID)

# Field with input for target team name.
target_team_input = Input(
    g.DEFAULT_TEAM_NAME, minlength=1, placeholder="Enter target team name"
)
target_team_field = Field(
    target_team_input,
    "Target team name",
    "Enter the name of the team in the target instance to which the data will be uploaded.",
)
target_team_field.hide()

# Flexbox with all buttons.
load_button = Button("Compare data")
cancel_button = Button("Cancel", button_type="danger", icon="zmdi zmdi-close-circle-o")
change_button = Button("Change source", icon="zmdi zmdi-swap-vertical-circle")
refresh_button = Button("Refresh", icon="zmdi zmdi-refresh-alt", button_type="success")
cancel_button.hide()
change_button.hide()
refresh_button.hide()
buttons_flexbox = Flexbox([load_button, cancel_button, change_button, refresh_button])

# Progress bar for comparsion status.
compare_progress = Progress()

card = Card(
    title="3️⃣ Compare data",
    description="Select the source team, enter the target team name and launch the comparison.",
    content=Container(
        [
            team_select,
            target_team_field,
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
    """Handle click on load button. Starts comparsion with specified parameters."""
    g.STATE.continue_comparsion = True

    warning_message.hide()

    # Reading team ID and target team name from the widgets.
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
        # If comparsion finished successfully.
        update.card.unlock()
        load_button.hide()
        cancel_button.hide()
        refresh_button.show()
        update.upload_button.show()
    else:
        # If comparsion was canceled.
        update.difference_text.hide()
        update.card.lock()
        compare_progress.hide()

        warning_message.text = "The comparison was canceled."
        warning_message.show()

    change_button.show()
    load_button.text = "Compare data"


@refresh_button.click
def refresh_data():
    """Handle click on refresh button. Starts comparsion again with the same parameters."""
    refresh_button.hide()
    change_button.hide()

    load_button.show()

    load_button.loading = True
    load_data()
    load_button.loading = False


@change_button.click
def change_source():
    """Handle click on change source button. Allows to change source team for starting comparsion again."""
    warning_message.hide()
    refresh_button.hide()
    change_button.hide()

    load_button.show()

    team_select.enable()
    target_team_input.enable()

    update.card.lock()


@cancel_button.click
def cancel_process():
    """Cancel the process of comparsion."""
    g.STATE.continue_comparsion = False
    cancel_button.hide()
