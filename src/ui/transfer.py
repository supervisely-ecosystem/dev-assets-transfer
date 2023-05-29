import os

from supervisely.app.widgets import (
    Container,
    Card,
    Button,
    Input,
    Field,
    SelectProject,
)

import supervisely as sly

import src.globals as g


project_select = SelectProject(
    workspace_id=g.WORKSPACE_ID,
    compact=True,
    allowed_types=[sly.ProjectType.VIDEOS],
)

target_team_input = Input(
    "debug_team", minlength=1, placeholder="Enter target team name"
)
target_wotkspace_input = Input(
    "debug_workspace", minlength=1, placeholder="Enter target workspace name"
)

target_team_field = Field(
    Container([target_team_input, target_wotkspace_input]),
    "Target team name",
    "Enter the name of the team in the target instance to which the data will be uploaded.",
)

transfer_button = Button("Transfer")

card = Card(
    "3️⃣ Transfer",
    "Select the project to transfer and enter the name of the team in the target instance.",
    content=Container(
        widgets=[project_select, target_team_field, transfer_button],
    ),
)


@transfer_button.click
def transfer():
    sly.fs.clean_dir(g.TMP_DIR)
    project_id = project_select.get_selected_id()
    project_info = g.source_api.project.get_info_by_id(project_id)
    project_name = project_info.name

    datasets = g.source_api.dataset.get_list(project_id)

    sly.logger.info(
        f"Readed project name: {project_name} with {len(datasets)} datasets"
    )

    target_team_name = target_team_input.get_value()
    target_workspace_name = target_wotkspace_input.get_value()

    target_team_info = g.STATE.target_api.team.get_info_by_name(target_team_name)
    if not target_team_info:
        raise RuntimeError(f"Team {target_team_name} not found")

    target_workspace_info = g.STATE.target_api.workspace.get_info_by_name(
        target_team_info.id, target_workspace_name
    )
    if not target_workspace_info:
        target_workspace_info = g.STATE.target_api.workspace.create(
            target_team_info.id, target_workspace_name, change_name_if_conflict=True
        )
        sly.logger.info(
            f"Can't find workspace {target_workspace_name}, created new one"
        )

    sly.logger.info(f"Target workspace id: {target_workspace_info.id}")

    project_path = os.path.join(g.TMP_DIR, project_name)

    sly.download_video_project(g.source_api, project_id, project_path)
    sly.upload_video_project(project_path, g.STATE.target_api, target_workspace_info.id)
