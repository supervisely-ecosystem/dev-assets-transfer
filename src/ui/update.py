import json
import os

from datetime import datetime
from shutil import rmtree
from collections import defaultdict, namedtuple
from typing import List, Tuple, Dict

import supervisely as sly

from supervisely.app.widgets import (
    Card,
    Container,
    Text,
    Progress,
    Button,
    Flexbox,
)

import src.globals as g
import src.ui.settings as settings
import src.ui.compare as compare
import src.ui.keys as keys


# Container with all text widgets.
annotated_images_text = Text(
    f"Annotated images: {g.STATE.annotated_images}", status="info"
)
tagged_images_text = Text(f"Tagged images: {g.STATE.tagged_images}", status="info")
difference_text = Text(status="info")
uploaded_text = Text(status="success")
comparsion_texts = Container(
    [difference_text, annotated_images_text, tagged_images_text]
)

annotated_images_text.hide()
tagged_images_text.hide()
difference_text.hide()
uploaded_text.hide()

# Flexbox with all buttons.
upload_button = Button("Update data")
cancel_button = Button("Cancel", button_type="danger", icon="zmdi zmdi-close-circle-o")
buttons_flexbox = Flexbox([upload_button, cancel_button])

upload_button.hide()
cancel_button.hide()

# Progress bar for upload status.
upload_progress = Progress()

card = Card(
    title="4️⃣ Update data",
    description="Images from the source team will be filtered and uploaded to the target team.",
    content=Container([buttons_flexbox, upload_progress, uploaded_text]),
    lock_message="Select Team on step 3️⃣ and wait until comparison is finished.",
)

card.lock()


def team_difference(source_team_id):
    """Calculates difference between source and target teams.

    :param source_team_id: id of the source team in Supervisely instance.
    :type source_team_id: int
    """
    # Resetting all counters (for text widgets).
    g.STATE.reset_counters()
    compare.warning_message.hide()

    sly.logger.debug(
        f"Comparsion starting. Filter by annotation type: {g.STATE.filter_by_annotation_type}. "
        f"Filter by tag name: {g.STATE.filter_by_tag_name}."
    )
    if g.STATE.default_settings:
        sly.logger.debug("Using the default settings for comparison.")
        g.STATE.tag_name = g.DEFAULT_TAG_NAME
        g.STATE.annotation_types = g.DEFAULT_ANNOTATION_TYPES
    else:
        sly.logger.debug("Using custom settings for comparison.")
        if g.STATE.filter_by_annotation_type:
            sly.logger.debug("Filtering by annotation type is enabled.")
            g.STATE.annotation_types = settings.annotation_type_select.get_value()
            if not g.STATE.annotation_types:
                sly.logger.debug("No annotation types selected.")
                compare.warning_message.text = "No annotation types selected."
                compare.warning_message.status = "error"
                compare.warning_message.show()
                return
        if g.STATE.filter_by_tag_name:
            sly.logger.debug("Filtering by tag name is enabled.")
            g.STATE.tag_name = settings.tag_name_input.get_value()
            if not g.STATE.tag_name:
                compare.warning_message.text = "No tag name was entered."
                compare.warning_message.status = "error"
                compare.warning_message.show()
                return

    # Changing lock messages on other cards.
    keys.card._lock_message = "Comparing images..."
    settings.card._lock_message = "Comparing images..."
    card._lock_message = "Comparing images..."
    keys.card.lock()
    settings.card.lock()
    card.lock()

    # Updating text on widgets and showing them.
    annotated_images_text.text = f"Annotated images: {g.STATE.annotated_images}"
    tagged_images_text.text = f"Tagged images: {g.STATE.tagged_images}"

    if g.STATE.filter_by_annotation_type:
        annotated_images_text.show()
    if g.STATE.filter_by_tag_name:
        tagged_images_text.show()

    # Hiding texts with previous comparison and upload results.
    difference_text.hide()
    uploaded_text.hide()

    team_differences = defaultdict(list)

    team_name = g.STATE.target_team_name
    sly.logger.debug(f"Readed team name as {team_name}.")

    # Trying to find team with specified name in target instance.
    target_team = g.STATE.target_api.team.get_info_by_name(team_name)

    if target_team:
        target_team_id = target_team.id
        sly.logger.debug(
            f"Team {team_name} is found in target instance with ID {target_team_id}."
        )
    else:
        # If team is not found, it will be created.
        sly.logger.debug(
            f"Team {team_name} is not found in target instance. Will create it."
        )
        target_team_id = g.STATE.target_api.team.create(team_name).id
        sly.logger.debug(
            f"Team {team_name} is created in target instance with ID {target_team_id}."
        )

    # Getting list of workspaces in source team.
    source_workspaces = g.source_api.workspace.get_list(source_team_id)
    sly.logger.debug(
        f"Found {len(source_workspaces)} workspaces in source team, starting workspace comparison."
    )

    for workspace in source_workspaces:
        team_differences[workspace.name] = workspace_difference(
            workspace, target_team_id
        )

    sly.logger.debug(
        f"Finished workspaces comparison. Found new {g.STATE.annotated_images} annotated images "
        f"and {g.STATE.tagged_images} tagged images."
    )

    with open(g.DIFFERENCES_JSON, "w", encoding="utf-8") as f:
        json.dump(team_differences, f, ensure_ascii=False, indent=4)

    sly.logger.debug(f"Team differences are saved to {g.DIFFERENCES_JSON}.")

    # Hiding in-progress widgets and replacing them with the results.
    annotated_images_text.hide()
    tagged_images_text.hide()

    if not g.STATE.filter_by_annotation_type and not g.STATE.filter_by_tag_name:
        difference_text.text = f"Found {g.STATE.annotated_images} new images."
    else:
        difference_text.text = (
            f"Found {g.STATE.annotated_images} new annotated images "
            f"and {g.STATE.tagged_images} new tagged images."
        )
    difference_text.show()

    # Returning lock messages to default.
    card._lock_message = (
        "Select Team on step 2️⃣ and wait until comparison is finished."
    )
    card.unlock()
    settings.card.unlock()
    keys.card.unlock()


def workspace_difference(
    source_workspace: sly.WorkspaceInfo, target_team_id: int
) -> defaultdict:
    """Calculates difference between source and target workspace.

    :param source_workspace: object with information about source workspace.
    :type source_workspace: sly.WorkspaceInfo
    :param target_team_id: id of the target team in Supervisely instance.
    :type target_team_id: int
    :return: defaultdict with information about difference between source and target workspace.
    :rtype: defaultdict
    """
    workspace_differences = defaultdict(list)

    workspace_name = source_workspace.name
    sly.logger.debug(f"Working on a workspace {workspace_name}.")

    # Trying to find workspace with specified name in target team.
    target_workspace = g.STATE.target_api.workspace.get_info_by_name(
        target_team_id, workspace_name
    )

    if target_workspace:
        target_workspace_id = target_workspace.id
        sly.logger.debug(
            f"Workspace {workspace_name} is found in target team with ID {target_workspace_id}."
        )
    else:
        # If workspace is not found, it will be created.
        sly.logger.debug(
            f"Workspace {workspace_name} is not found in target team. Will create it."
        )
        target_workspace_id = g.STATE.target_api.workspace.create(
            target_team_id, workspace_name
        ).id
        sly.logger.debug(
            f"Workspace {workspace_name} is created in target team with ID {target_workspace_id}."
        )

    # Getting list of projects in source workspace.
    source_projects = g.source_api.project.get_list(source_workspace.id)
    sly.logger.debug(
        f"Found {len(source_projects)} projects in source workspace, starting project comparison."
    )
    compare.compare_progress.show()

    with compare.compare_progress(
        message=f"Comparing projects in workspace {source_workspace.name}...",
        total=len(source_projects),
    ) as pbar:
        for project in source_projects:
            if g.STATE.continue_comparsion:
                workspace_differences[project.name] = project_difference(
                    project, target_workspace_id
                )
                pbar.update(1)

    sly.logger.debug("Finished projects comparison.")

    return workspace_differences


def project_difference(
    source_project: sly.ProjectInfo, target_workspace_id: int
) -> defaultdict:
    """Calculates difference between source and target project.

    :param source_project: object with information about source project.
    :type source_project: sly.ProjectInfo
    :param target_workspace_id: id of the target workspace in Supervisely instance.
    :type target_workspace_id: int
    :return: defaultdict with information about difference between source and target project.
    :rtype: defaultdict
    """
    project_differences = defaultdict(list)

    project_name = source_project.name
    sly.logger.debug(f"Working on a project {project_name}.")

    # Trying to find project with specified name in target workspace.
    target_project = g.STATE.target_api.project.get_info_by_name(
        target_workspace_id, project_name
    )

    if g.STATE.default_settings:
        source_project_meta_json = g.source_api.project.get_meta(source_project.id)
        source_project_meta = sly.ProjectMeta.from_json(source_project_meta_json)
        class_titles = [obj_class.name for obj_class in source_project_meta.obj_classes]

        workspace_name = g.source_api.workspace.get_info_by_id(
            source_project.workspace_id
        ).name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        error = None

        if len(class_titles) > 1:
            sly.logger.error(
                f"Default settings are enabled, but project {project_name} has more than one class."
            )
            error = "Project has more than one class."

        elif len(class_titles) == 1:
            class_name = str(class_titles[0]).lower()
            unified_class_name = class_name.rsplit("_", 1)[0]
            unified_project_name = project_name.replace(" ", "_").lower()

            sly.logger.debug(
                f"Checking if unified class name {unified_class_name} is equal "
                f"to unified project name {unified_project_name}."
            )

            if unified_class_name != unified_project_name:
                error = "Class name is incorrect."
                sly.logger.error(
                    "Unified class name is not equal to unified project name."
                )

        if error:
            error_report = {
                "timestamp": timestamp,
                "project_name": project_name,
                "error": error,
            }
            g.STATE.error_report[workspace_name].append(error_report)

    if target_project:
        target_project_id = target_project.id
        sly.logger.debug(
            f"Project {project_name} is found in target workspace with ID {target_project_id}."
        )
    else:
        # If project is not found, it will be created.
        sly.logger.debug(
            f"Project {project_name} is not found in target workspace. Will create it."
        )
        target_project_id = g.STATE.target_api.project.create(
            target_workspace_id, project_name
        ).id
        sly.logger.debug(
            f"Project {project_name} is created in target workspace with ID {target_project_id}."
        )

    # Getting list of datasets in source project.
    source_datasets = g.source_api.dataset.get_list(source_project.id)
    sly.logger.debug(
        f"Found {len(source_datasets)} datasets in source project, starting dataset comparison."
    )
    for dataset in source_datasets:
        if g.STATE.continue_comparsion:
            project_differences[dataset.name] = dataset_difference(
                dataset, target_project_id
            )

    sly.logger.debug("Finished datasets comparison.")

    return project_differences


def dataset_difference(
    source_dataset: sly.DatasetInfo, target_project_id: int
) -> defaultdict:
    """Calculates difference between source and target dataset, while filtering out images
    that doesn't have bitmap annotation or tag with specified name.

    :param source_dataset: object with information about source dataset.
    :type source_dataset: sly.DatasetInfo
    :param target_project_id: id of the target project in Supervisely instance.
    :type target_project_id: int
    :return: defaultdict with information about difference between source and target dataset.
    :rtype: defaultdict
    """
    dataset_name = source_dataset.name
    sly.logger.debug(f"Working on a dataset {dataset_name}.")

    # Trying to find dataset with specified name in target project.
    target_dataset = g.STATE.target_api.dataset.get_info_by_name(
        target_project_id, dataset_name
    )

    if target_dataset:
        target_dataset_id = target_dataset.id
        sly.logger.debug(
            f"Dataset {dataset_name} is found in target project with ID {target_dataset_id}."
        )
    else:
        # If dataset is not found, it will be created.
        sly.logger.debug(
            f"Dataset {dataset_name} is not found in target project. Will create it."
        )
        target_dataset = g.STATE.target_api.dataset.create(
            target_project_id, dataset_name
        )
        target_dataset_id = target_dataset.id
        sly.logger.debug(
            f"Dataset {dataset_name} is created in target project with ID {target_dataset_id}."
        )

    # Getting list of images in source dataset.
    source_images = g.source_api.image.get_list(source_dataset.id)
    sly.logger.debug(f"Found {len(source_images)} images in source dataset.")

    # Getting list of images in target dataset.
    target_images = g.STATE.target_api.image.get_list(target_dataset_id)
    sly.logger.debug(f"Found {len(target_images)} images in target dataset.")

    # Preparing list of file names of images in target dataset.
    target_names = [obj.name for obj in target_images]

    # Filtering out images that are already in target dataset.
    new_images = [obj for obj in source_images if obj.name not in target_names]

    sly.logger.debug(f"Found {len(new_images)} new images in dataset {dataset_name}.")

    # Launching function to filter out images that doesn't have bitmap annotation or tag with specified name.
    if g.STATE.filter_by_annotation_type or g.STATE.filter_by_tag_name:
        new_annotated_images, new_tagged_images = filter_images(
            new_images, source_dataset
        )

        # Updating counters for annotated and tagged images.
        g.STATE.annotated_images += len(new_annotated_images)
        g.STATE.tagged_images += len(new_tagged_images)

        if len(new_annotated_images) > 0:
            # Updading text in the widget if the number of annotated images was changed.
            annotated_images_text.text = (
                f"Annotated images: {g.STATE.annotated_images} "
                f"(+{len(new_annotated_images)} from {dataset_name})"
            )
        if len(new_tagged_images) > 0:
            # Updaing text in the widget if the number of tagged images was changed.
            tagged_images_text.text = (
                f"Tagged images: {g.STATE.tagged_images} "
                f"(+{len(new_tagged_images)} from {dataset_name})"
            )

    else:
        new_annotated_images = new_images
        new_tagged_images = []

    dataset_differences = {
        "source": source_dataset,
        "target": target_dataset,
        "annotated_images": new_annotated_images,
        "tagged_images": new_tagged_images,
    }

    sly.logger.debug(f"Prepared all data for dataset {dataset_name}.")

    return dataset_differences


def filter_images(
    new_images: List[sly.ImageInfo], source_dataset: sly.DatasetInfo
) -> Tuple[List[sly.ImageInfo], List[sly.ImageInfo]]:
    """Filters out images that doesn't have bitmap annotation or tag with specified name.

    :param new_images: list of images that are not in target dataset.
    :type new_images: List[sly.ImageInfo]
    :param source_dataset: object with information about source dataset.
    :type source_dataset: sly.DatasetInfo
    :return: tuple with two lists of images that have bitmap annotation and tag with specified name.
    :rtype: Tuple[List[sly.ImageInfo], List[sly.ImageInfo]]
    """
    sly.logger.debug(f"Starting filtering images in dataset {source_dataset.name}.")

    # Preparing list of annotations for images that are not in target dataset.
    source_annotations = g.source_api.annotation.download_batch(
        source_dataset.id, [image.id for image in new_images]
    )

    sly.logger.debug(
        f"Downloaded {len(source_annotations)} annotations from dataset {source_dataset.name}."
    )

    annotated_image_ids = []
    tagged_image_ids = []

    for annotation_info in source_annotations:
        # Iterating over annotations and checking if they have bitmap annotation or tag with specified name.
        annotation = annotation_info.annotation

        objects = annotation["objects"]
        tags = annotation["tags"]

        image_id = annotation_info.image_id

        if any(
            object["geometryType"] in g.STATE.annotation_types for object in objects
        ):
            # If image has bitmap annotation, it will be added to the list of annotated images.
            sly.logger.debug(
                f"Found annotation with correct type in image with ID {image_id}."
            )
            annotated_image_ids.append(image_id)

        elif tags:
            sly.logger.debug(f"Found tag annotation in image with ID {image_id}.")

            if any(tag["name"] == g.STATE.tag_name for tag in tags):
                # If image has tag with specified name, it will be added to the list of tagged images.
                sly.logger.debug(
                    f"Found tag {g.STATE.tag_name} in image with ID {image_id}."
                )
                tagged_image_ids.append(image_id)

    sly.logger.debug(f"Finished filtering images in dataset {source_dataset.name}.")
    sly.logger.debug(
        f"Found {len(annotated_image_ids)} annotated images and {len(tagged_image_ids)} tagged images."
    )

    new_annotated_images = [
        image for image in new_images if image.id in annotated_image_ids
    ]
    new_tagged_images = [image for image in new_images if image.id in tagged_image_ids]

    sly.logger.debug(
        f"Prepared lists of annotated and tagged images in dataset {source_dataset.name}."
    )

    return new_annotated_images, new_tagged_images


@upload_button.click
def upload_images():
    """Uploads images from source dataset to target dataset using JSON file with differences between
    source and target datasets."""
    sly.logger.debug("Starting upload of images.")

    g.STATE.continue_upload = True
    cancel_button.show()

    upload_button.text = "Updating..."
    uploaded_text.hide()

    if g.STATE.default_settings:
        g.STATE.normalize_image_metadata = True
    else:
        g.STATE.normalize_image_metadata = (
            settings.normalize_metadata_checkbox.is_checked()
        )

    sly.logger.debug(
        f"Normalize image metadata is set to {g.STATE.normalize_image_metadata}."
    )

    keys.card._lock_message = "Updating images..."
    settings.card._lock_message = "Updating images..."
    compare.card._lock_message = "Updating images..."
    keys.card.lock()
    settings.card.lock()
    compare.card.lock()

    # Loading JSON file with differences between source and target datasets.
    with open(g.DIFFERENCES_JSON, "r", encoding="utf-8") as f:
        team_differences = json.load(f)

    sly.logger.debug("Successfully loaded team differences JSON file.")

    for workspace_name, projects in team_differences.items():
        sly.logger.debug(f"Working on a workspace {workspace_name}.")

        upload_progress.show()

        with upload_progress(
            message=f"Uploading projects in workspace {workspace_name}...",
            total=len(projects),
        ) as pbar:
            for project_name, datasets in projects.items():
                sly.logger.debug(f"Working on a project {project_name}.")

                if g.STATE.continue_upload:
                    for dataset_name, dataset in datasets.items():
                        sly.logger.debug(f"Working on a dataset {dataset_name}.")

                        # Getting IDs of source and target datasets from JSON file.
                        source_dataset_id = dataset["source"][0]
                        target_dataset_id = dataset["target"][0]

                        sly.logger.debug(
                            f"Source dataset ID: {source_dataset_id}. Target dataset ID: {target_dataset_id}."
                        )

                        # Getting information about annotated images, which are going to be uploaded.
                        annotated_images = get_image_data(
                            dataset["annotated_images"], dataset_name
                        )

                        # Getting information about tagged images, which are going to be uploaded.
                        tagged_images = get_image_data(
                            dataset["tagged_images"], dataset_name
                        )

                        if annotated_images is None or tagged_images is None:
                            sly.logger.error(
                                f"Failed to get images data for dataset {dataset_name}."
                            )
                            continue

                        # Downloading annotated and tagged images from source dataset.
                        download_images(
                            annotated_images, source_dataset_id, dataset_name
                        )

                        sly.logger.debug(
                            f"Finished downloading annotated images for dataset {dataset_name}."
                        )

                        download_images(tagged_images, source_dataset_id, dataset_name)

                        sly.logger.debug(
                            f"Finished downloading tagged images for dataset {dataset_name}."
                        )

                        # Rettrieving project meta from source instance and updating it in target instance.
                        project_meta = update_project_meta(
                            source_dataset_id, target_dataset_id
                        )

                        sly.logger.debug("Retrieved and updated project meta.")

                        # Downloading annotations for annotated and tagged images.
                        annotated_annotations = download_annotations(
                            source_dataset_id, annotated_images.ids, project_meta
                        )

                        sly.logger.debug(
                            f"Downloaded {len(annotated_annotations)} annotated annotations."
                        )

                        tagged_annotations = download_annotations(
                            source_dataset_id, tagged_images.ids, project_meta
                        )

                        sly.logger.debug(
                            f"Downloaded {len(tagged_annotations)} tagged annotations."
                        )

                        # Updating counter for annotated and tagged images.
                        g.STATE.uploaded_annotated_images += (
                            upload_images_with_annotations(
                                annotated_images,
                                target_dataset_id,
                                dataset_name,
                                annotated_annotations,
                            )
                        )

                        sly.logger.debug(
                            f"Uploaded annotated images with annotations to dataset {dataset_name}."
                        )

                        g.STATE.uploaded_tagged_images += (
                            upload_images_with_annotations(
                                tagged_images,
                                target_dataset_id,
                                dataset_name,
                                tagged_annotations,
                            )
                        )

                        sly.logger.debug(
                            f"Uploaded tagged images with annotations to dataset {dataset_name}."
                        )

                        sly.logger.debug(
                            f"Finished uploading images for dataset {dataset_name}."
                        )

                        # Removing directory with downloaded images after uploading them.
                        rmtree(os.path.join(g.IMAGES_DIR, dataset_name))
                        sly.logger.debug(
                            f"Removed directory {os.path.join(g.IMAGES_DIR, dataset_name)} after uploading images."
                        )

                        sly.logger.debug(
                            f"Finished uploading datasets in project {project_name}."
                        )
                    pbar.update(1)
        if not g.STATE.continue_upload:
            sly.logger.debug(
                f"Uploading of images was interrupted, while working on workspace {workspace_name}."
            )
            break
        sly.logger.debug(f"Finished uploading projects in workspace {workspace_name}.")
    if g.STATE.continue_upload:
        # If uploading was not interrupted, show success message.
        sly.logger.debug("Finished uploading images.")
        uploaded_text.status = "success"

        if not g.STATE.filter_by_annotation_type and not g.STATE.filter_by_tag_name:
            uploaded_text.text = (
                f"Successfully uploaded {g.STATE.uploaded_annotated_images} images."
            )

        uploaded_text.text = (
            f"Successfully uploaded {g.STATE.uploaded_annotated_images} annotated images "
            f"and {g.STATE.uploaded_tagged_images} tagged images."
        )
    else:
        # If uploading was interrupted, show warning message.
        sly.logger.debug("Uploading of images was interrupted.")
        uploaded_text.status = "warning"

        if not g.STATE.filter_by_annotation_type and not g.STATE.filter_by_tag_name:
            uploaded_text.text = (
                f"Uploading of images was cancelled after uploading "
                f"{g.STATE.uploaded_annotated_images} images."
            )

        uploaded_text.text = (
            f"Uploading of images was cancelled after uploading {g.STATE.uploaded_annotated_images} annotated images "
            f"and {g.STATE.uploaded_tagged_images} tagged images."
        )

    upload_progress.hide()
    upload_button.hide()
    cancel_button.hide()
    upload_button.text = "Update data"

    keys.card.unlock()
    settings.card.unlock()
    compare.card.unlock()

    uploaded_text.show()


def download_images(
    images: List[sly.ImageInfo], source_dataset_id: int, dataset_name: str
):
    """Download images from the source dataset to the local directory.

    :param images: list of objects with information about images
    :type images: List[sly.ImageInfo]
    :param source_dataset_id: ID of the source dataset in Supervisely instance
    :type source_dataset_id: int
    :param dataset_name: name of the dataset (for convinient logging)
    :type dataset_name: str
    """
    sly.logger.debug(f"Starting download of images from dataset {dataset_name}.")

    for batch_names, batch_paths in zip(
        sly.batched(images.ids, batch_size=g.BATCH_SIZE),
        sly.batched(images.paths, batch_size=g.BATCH_SIZE),
    ):
        g.source_api.image.download_paths(source_dataset_id, batch_names, batch_paths)

        sly.logger.debug(
            f"Downloaded {len(batch_names)} images from dataset {dataset_name}."
        )
    sly.logger.debug(f"Finished download of images from dataset {dataset_name}.")


def update_project_meta(
    source_dataset_id: int, target_dataset_id: int
) -> sly.ProjectMeta:
    """Updates the meta in target instance with the meta from source instance. Returns the updated meta.

    :param source_dataset_id: the id of the source dataset
    :type source_dataset_id: int
    :param target_dataset_id: the id of the target dataset
    :type target_dataset_id: int
    :return: object with meta information about the project
    :rtype: sly.ProjectMeta
    """
    source_project_id = g.source_api.dataset.get_info_by_id(
        source_dataset_id
    ).project_id

    sly.logger.debug(f"Retrieved source project ID: {source_project_id}.")

    # Retrieving and converting project meta from the source instance.
    meta_json = g.source_api.project.get_meta(source_project_id)
    project_meta = sly.ProjectMeta.from_json(meta_json)

    sly.logger.debug(
        f"Successfully downloaded project meta for dataset {source_dataset_id}."
    )

    target_project_id = g.STATE.target_api.dataset.get_info_by_id(
        target_dataset_id
    ).project_id

    sly.logger.debug(f"Retrieved target project ID: {target_project_id}.")

    # Updating project meta in target instance.
    g.STATE.target_api.project.update_meta(target_project_id, project_meta)

    sly.logger.debug(
        f"Successfully updated project meta for dataset {target_dataset_id}."
    )

    return project_meta


def download_annotations(
    source_dataset_id: int, image_ids: List[int], project_meta: sly.ProjectMeta
) -> List[sly.Annotation]:
    """Download annotations for the images in the source dataset.

    :param source_dataset_id: the id of the source dataset
    :type source_dataset_id: int
    :param image_ids: list of ids of images
    :type image_ids: List[int]
    :param project_meta: object with meta information about the project
    :type project_meta: sly.ProjectMeta
    :return: list of objects with annotations for the images
    :rtype: List[sly.Annotation]
    """
    sly.logger.debug(
        f"Starting download of annotations from dataset with id {source_dataset_id}."
    )

    # Retrieving AnnotationInfo objects for the images.
    annotation_infos = g.source_api.annotation.download_batch(
        source_dataset_id, image_ids
    )

    # Converting AnnotationInfo objects to JSON.
    annotation_jsons = [
        annotation_info.annotation for annotation_info in annotation_infos
    ]

    # Creating Annotation objects from JSON.
    annotations = [
        sly.Annotation.from_json(json, project_meta) for json in annotation_jsons
    ]

    sly.logger.debug(
        f"Downloaded {len(annotations)} annotations from dataset with id {source_dataset_id}."
    )

    return annotations


def upload_images_with_annotations(
    images: List[sly.ImageInfo],
    target_dataset_id: int,
    dataset_name: str,
    annotations: List[sly.Annotation],
) -> int:
    """Upload images with annotations to the target dataset.

    :param images: list of objects with information about images
    :type images: List[sly.ImageInfo]
    :param target_dataset_id: ID of the target dataset in Supervisely instance
    :type target_dataset_id: int
    :param dataset_name: name of the dataset (for convinient logging)
    :type dataset_name: str
    :param annotations: list of objects with annotations for the images to be uploaded
    :type annotations: List[sly.Annotation]
    :return: number of uploaded images
    :rtype: int
    """
    sly.logger.debug(f"Starting upload of images to dataset {dataset_name}.")

    uploaded_image_ids = []

    for batch_names, batch_paths, batch_metas in zip(
        sly.batched(images.names, batch_size=g.BATCH_SIZE),
        sly.batched(images.paths, batch_size=g.BATCH_SIZE),
        sly.batched(images.metas, batch_size=g.BATCH_SIZE),
    ):
        uploaded_batch = g.STATE.target_api.image.upload_paths(
            target_dataset_id, batch_names, batch_paths, metas=batch_metas
        )

        # Getting list of image ids for the uploaded images.
        uploaded_batch_ids = [image.id for image in uploaded_batch]
        uploaded_image_ids.extend(uploaded_batch_ids)

        sly.logger.debug(
            f"Uploaded {len(batch_names)} images to dataset {dataset_name}."
        )
    sly.logger.debug(f"Finished upload of images to dataset {dataset_name}.")

    # Uploading annotations for the uploaded images.
    g.STATE.target_api.annotation.upload_anns(uploaded_image_ids, annotations)

    sly.logger.debug(
        f"Uploaded {len(annotations)} annotations to dataset {dataset_name}."
    )

    return len(uploaded_image_ids)


def get_image_data(images: List[sly.ImageInfo], dataset_name: str) -> namedtuple:
    """_summary_

    :param images: list of objects with information about images
    :type images: List[sly.ImageInfo]
    :param dataset_name: name of the dataset
    :type dataset_name: str
    :return: ImagesData namedtuple, containing lists of image ids, names, paths and metas
    :rtype: namedtuple
    """
    image_ids = [image[g.INDICES["images_ids"]] for image in images]
    image_names = [image[g.INDICES["image_names"]] for image in images]
    image_metas = [image[g.INDICES["image_metas"]] for image in images]

    sly.logger.debug(f"Readed {len(image_ids)} image IDs and names.")

    if g.STATE.normalize_image_metadata:
        # Normalizing image metadata if checkbox is checked.
        image_metas = normalize_image_metadata(image_metas)
        sly.logger.debug(f"Normalized {len(image_metas)} image metas.")

    if len(image_ids) == len(image_names) == len(image_metas):
        # Checking if all three lists have the same length.
        sly.logger.debug("All three lists have the same length.")
    else:
        sly.logger.error(
            "At least one of the lists (ids, names, metas) has different length."
        )
        sly.app.show_dialog(
            "Bad image data",
            "There was an error while reading image data. Try to load image data again.",
            status="error",
        )
        return

    # Creating list of paths to the images in the local directory.
    paths = [
        os.path.join(g.IMAGES_DIR, dataset_name, image_name)
        for image_name in image_names
    ]
    os.makedirs(os.path.join(g.IMAGES_DIR, dataset_name), exist_ok=True)

    ImagesData = namedtuple("ImagesData", ["ids", "names", "paths", "metas"])

    # Creating namedtuple with the lists of image ids, names, paths and metas.
    images_data = ImagesData(image_ids, image_names, paths, image_metas)

    return images_data


def normalize_image_metadata(image_metas: List[Dict]) -> List[Dict]:
    """Updates the image metadata dict to match the format of the target dataset (Assets).

    :param image_metas: list of dicts with image metadata
    :type image_metas: List[Dict]
    :return: updated list of dicts with image metadata
    :rtype: List[Dict]

    :Assets instance metadtata format:
    TARGET_METADATA_FIELDS = ["URL", "License", "Author"]

    :Possible metadata fields in the source dataset:
    SOURCE_URL_FIELDS = ["Flickr image URL", "Pexels image URL", "Source URL"]
    SOURCE_AUTHOR_FIELDS = ["Flickr owner id", "Photographer name"]
    SOURCE_LICENSE_FIELDS = ["License", "license", None]
    """

    new_image_metas = []

    for image_meta in image_metas:
        new_image_meta = {}
        new_image_meta["URL"] = (
            image_meta.get("Flickr image URL")
            or image_meta.get("Pexels image URL")
            or image_meta.get("Source URL")
        )
        new_image_meta["Author"] = image_meta.get("Flickr owner id") or image_meta.get(
            "Photographer name"
        )

        new_image_meta["License"] = (
            image_meta.get("License") or image_meta.get("license") or "Pexels license"
        )

        new_image_metas.append(new_image_meta)

    return new_image_metas


@cancel_button.click
def cancel():
    """Handles click on the cancel button. Stops the upload process."""
    g.STATE.continue_upload = False
    cancel_button.hide()
