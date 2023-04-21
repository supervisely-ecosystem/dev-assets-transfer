from supervisely.app.widgets import Card, Field, Checkbox, Container, Select, Input

import src.globals as g
import src.ui.compare as compare

# Field with checkbox for using default settings.
default_settings_checkbox = Checkbox(content="Use default settings", checked=True)
default_settings_field = Field(
    title="Uploading primitives to Assets",
    description=(
        "The images will be filtered according to the Assets instance requirements "
        "and metadata of the images will be normalized."
    ),
    content=default_settings_checkbox,
)

# Field with checkbox for normalize image metadata.
normalize_metadata_checkbox = Checkbox(content="Normalize metadata")
normalize_metadata_field = Field(
    title="Normalize image metadata",
    description=(
        "If checked images metadata will be normalized to three fields: URL, License and Author."
    ),
    content=normalize_metadata_checkbox,
)
normalize_metadata_field.hide()

# Field with widgets for filtering images (by annotation types or by tag names).
annotated_images_checkbox = Checkbox(content="Filter by annotation type")
annotation_type_select = Select(
    items=[Select.Item(geometry) for geometry in g.GEOMETRIES],
    multiple=True,
    placeholder="Select annotation types",
)
annotation_type_select.hide()

tagged_images_checkbox = Checkbox(content="Filter by tag name")
tag_name_input = Input(minlength=1, placeholder="Enter tag name")
tag_name_input.hide()

# Field with widgets for filtering images.
filter_settings_field = Field(
    title="Filter images",
    description="Images can be filtered by annotation types or by tag names.",
    content=Container(
        [
            annotated_images_checkbox,
            annotation_type_select,
            tagged_images_checkbox,
            tag_name_input,
        ]
    ),
)
filter_settings_field.hide()

card = Card(
    title="2️⃣ Settings",
    description="Settings for data comparsion and update.",
    content=Container(
        [default_settings_field, filter_settings_field, normalize_metadata_field]
    ),
)


@default_settings_checkbox.value_changed
def default_settings(is_checked: bool):
    """Handles click on checkbox for using default settings. If checked, the
    loads the default settings from globals and hides the widgets for
    selecting custom settings.

    :param is_checked: state of checkbox
    :type is_checked: bool
    """
    if is_checked:
        filter_settings_field.hide()
        normalize_metadata_field.hide()

        g.STATE.default_settings = True
        g.STATE.filter_by_annotation_type = True
        g.STATE.filter_by_tag_name = True

        compare.target_team_field.hide()
        compare.target_team_input.set_value(g.DEFAULT_TEAM_NAME)

    else:
        filter_settings_field.show()
        normalize_metadata_field.show()

        g.STATE.default_settings = False
        g.STATE.filter_by_annotation_type = False
        g.STATE.filter_by_tag_name = False

        compare.target_team_field.show()
        compare.target_team_input.set_value("")


@annotated_images_checkbox.value_changed
def annotated_filter(is_checked: bool):
    """Handles click on checkbox for filtering images by annotation types.
    Shows or hides the widget for selecting annotation types and changes global
    filter_by_annotation_type state.

    :param is_checked: state of checkbox
    :type is_checked: bool
    """
    if is_checked:
        annotation_type_select.show()
        g.STATE.filter_by_annotation_type = True
    else:
        annotation_type_select.hide()
        g.STATE.filter_by_annotation_type = False


@tagged_images_checkbox.value_changed
def tagged_filter(is_checked: bool):
    """Handles click on checkbox for filtering images by tag names. Shows or
    hides the widget for entering tag name and changes global filter_by_tag_name
    state.

    :param is_checked: state of checkbox
    :type is_checked: bool
    """
    if is_checked:
        tag_name_input.show()
        g.STATE.filter_by_tag_name = True
    else:
        tag_name_input.hide()
        g.STATE.filter_by_tag_name = False
