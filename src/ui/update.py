import json
import os

from shutil import rmtree
from collections import defaultdict, namedtuple
from time import perf_counter

import supervisely as sly

from supervisely.app.widgets import Card, Container, Text, Progress, Button

import src.globals as g
import src.ui.keys as k

annotated_images = 0
tagged_images = 0

uploaded_annotated_images = 0
uploaded_tagged_images = 0

team_differences_path = os.path.join(g.TMP_DIR, "team_differences.json")

annotated_images_text = Text(f"Annotated images: {annotated_images}", status="info")
tagged_images_text = Text(f"Tagged images: {tagged_images}", status="info")
difference_text = Text(status="success")
uploaded_text = Text(status="success")

annotated_images_text.hide()
tagged_images_text.hide()
difference_text.hide()
uploaded_text.hide()

upload_button = Button("Upload data")
upload_button.hide()

progresses = {level: Progress() for level in g.LEVELS}
progresses_container = Container(widgets=list(progresses.values()))

upload_card = Card(
    title="3️⃣ Compare and upload",
    description="Compare and upload data between source and target instances.",
    content=Container(
        [
            difference_text,
            uploaded_text,
            upload_button,
            annotated_images_text,
            tagged_images_text,
        ]
    ),
    lock_message="Select Team on step 2️⃣ and wait until comparison is finished.",
)

status_card = Card(
    title="4️⃣ Status",
    description="Progress status of data comparison and upload.",
    content=progresses_container,
    lock_message="Select Team on step 2️⃣ and wait until comparison is finished.",
)

upload_card.lock()
status_card.lock()


def measure_time(function: callable) -> callable:
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = function(*args, **kwargs)
        end = perf_counter()
        time = end - start
        sly.logger.debug(
            f"TIME -> [{time:.2f} seconds] | FUNCTION -> [{function.__name__}]."
        )
        return result

    return wrapper


@measure_time
def team_difference(source_team_id):
    global annotated_images, tagged_images
    annotated_images = tagged_images = 0

    annotated_images_text.show()
    tagged_images_text.show()

    difference_text.hide()
    uploaded_text.hide()

    team_differences = defaultdict(list)

    team_name = "Assets2"
    sly.logger.debug(f"Readed team name as {team_name}.")
    target_team = k.target_api.team.get_info_by_name(team_name)

    if target_team:
        target_team_id = target_team.id
        sly.logger.debug(
            f"Team {team_name} is found in target instance with ID {target_team_id}."
        )
    else:
        sly.logger.debug(
            f"Team {team_name} is not found in target instance. Will create it."
        )
        target_team_id = k.target_api.team.create(team_name).id
        sly.logger.debug(
            f"Team {team_name} is created in target instance with ID {target_team_id}."
        )

    source_workspaces = g.source_api.workspace.get_list(source_team_id)
    sly.logger.debug(
        f"Found {len(source_workspaces)} workspaces in source team, starting workspace comparison."
    )
    with progresses["team"](
        message=f"Comparing workspaces in team {team_name}...",
        total=len(source_workspaces),
    ) as pbar:
        for workspace in source_workspaces:
            team_differences[workspace.name] = workspace_difference(
                workspace, target_team_id
            )
            pbar.update(1)

    sly.logger.debug(
        f"Finished workspaces comparison. Found new {annotated_images} annotated images "
        f"and {tagged_images} tagged images."
    )

    global team_differences_path
    team_differences_path = os.path.join(g.TMP_DIR, "team_differences.json")
    with open(team_differences_path, "w", encoding="utf-8") as f:
        json.dump(team_differences, f, ensure_ascii=False, indent=4)

    sly.logger.debug(f"Team differences are saved to {team_differences_path}.")

    annotated_images_text.hide()
    tagged_images_text.hide()
    upload_button.show()

    difference_text.text = f"Found {annotated_images} new annotated images and {tagged_images} new tagged images."
    difference_text.show()


@measure_time
def workspace_difference(source_workspace, target_team_id):
    workspace_differences = defaultdict(list)

    workspace_name = source_workspace.name
    sly.logger.debug(f"Working on a workspace {workspace_name}.")
    target_workspace = k.target_api.workspace.get_info_by_name(
        target_team_id, workspace_name
    )

    if target_workspace:
        target_workspace_id = target_workspace.id
        sly.logger.debug(
            f"Workspace {workspace_name} is found in target team with ID {target_workspace_id}."
        )
    else:
        sly.logger.debug(
            f"Workspace {workspace_name} is not found in target team. Will create it."
        )
        target_workspace_id = k.target_api.workspace.create(
            target_team_id, workspace_name
        ).id
        sly.logger.debug(
            f"Workspace {workspace_name} is created in target team with ID {target_workspace_id}."
        )

    source_projects = g.source_api.project.get_list(source_workspace.id)
    sly.logger.debug(
        f"Found {len(source_projects)} projects in source workspace, starting project comparison."
    )

    with progresses["workspace"](
        message=f"Comparing projects in workspace {source_workspace.name}...",
        total=len(source_projects),
    ) as pbar:
        for project in source_projects:
            workspace_differences[project.name] = project_difference(
                project, target_workspace_id
            )
            pbar.update(1)

    sly.logger.debug("Finished projects comparison.")

    return workspace_differences


@measure_time
def project_difference(source_project, target_workspace_id):
    project_differences = defaultdict(list)

    project_name = source_project.name
    sly.logger.debug(f"Working on a project {project_name}.")
    target_project = k.target_api.project.get_info_by_name(
        target_workspace_id, project_name
    )

    if target_project:
        target_project_id = target_project.id
        sly.logger.debug(
            f"Project {project_name} is found in target workspace with ID {target_project_id}."
        )
    else:
        sly.logger.debug(
            f"Project {project_name} is not found in target workspace. Will create it."
        )
        target_project_id = k.target_api.project.create(
            target_workspace_id, project_name
        ).id
        sly.logger.debug(
            f"Project {project_name} is created in target workspace with ID {target_project_id}."
        )

    source_datasets = g.source_api.dataset.get_list(source_project.id)
    sly.logger.debug(
        f"Found {len(source_datasets)} datasets in source project, starting dataset comparison."
    )

    with progresses["project"](
        message=f"Comparing datasets in project {source_project.name}...",
        total=len(source_datasets),
    ) as pbar:
        for dataset in source_datasets:
            project_differences[dataset.name] = dataset_difference(
                dataset, target_project_id
            )
            pbar.update(1)

    sly.logger.debug("Finished datasets comparison.")

    return project_differences


@measure_time
def dataset_difference(source_dataset, target_project_id):
    dataset_name = source_dataset.name
    sly.logger.debug(f"Working on a dataset {dataset_name}.")
    target_dataset = k.target_api.dataset.get_info_by_name(
        target_project_id, dataset_name
    )

    if target_dataset:
        target_dataset_id = target_dataset.id
        sly.logger.debug(
            f"Dataset {dataset_name} is found in target project with ID {target_dataset_id}."
        )
    else:
        sly.logger.debug(
            f"Dataset {dataset_name} is not found in target project. Will create it."
        )
        target_dataset = k.target_api.dataset.create(target_project_id, dataset_name)
        target_dataset_id = target_dataset.id
        sly.logger.debug(
            f"Dataset {dataset_name} is created in target project with ID {target_dataset_id}."
        )

    source_images = g.source_api.image.get_list(source_dataset.id)
    sly.logger.debug(f"Found {len(source_images)} images in source dataset.")

    target_images = k.target_api.image.get_list(target_dataset_id)
    sly.logger.debug(f"Found {len(target_images)} images in target dataset.")

    target_names = [obj.name for obj in target_images]

    new_images = [obj for obj in source_images if obj.name not in target_names]

    sly.logger.debug(f"Found {len(new_images)} new images in dataset {dataset_name}.")

    new_annotated_images, new_tagged_images = filter_images(new_images, source_dataset)

    global annotated_images, tagged_images
    annotated_images += len(new_annotated_images)
    tagged_images += len(new_tagged_images)

    if len(new_annotated_images) > 0:
        annotated_images_text.text = (
            f"Annotated images: {annotated_images} "
            f"(+{len(new_annotated_images)} from {dataset_name})"
        )
    if len(new_tagged_images) > 0:
        tagged_images_text.text = (
            f"Tagged images: {tagged_images} "
            f"(+{len(new_tagged_images)} from {dataset_name})"
        )

    dataset_differences = {
        "source": source_dataset,
        "target": target_dataset,
        "annotated_images": new_annotated_images,
        "tagged_images": new_tagged_images,
    }

    sly.logger.debug(f"Prepared all data for dataset {dataset_name}.")

    return dataset_differences


@measure_time
def filter_images(new_images, source_dataset):
    sly.logger.debug(f"Starting filtering images in dataset {source_dataset.name}.")
    source_annotations = g.source_api.annotation.download_batch(
        source_dataset.id, [image.id for image in new_images]
    )

    sly.logger.debug(
        f"Downloaded {len(source_annotations)} annotations from dataset {source_dataset.name}."
    )

    annotated_image_ids = []
    tagged_image_ids = []

    for annotation_info in source_annotations:
        annotation = annotation_info.annotation
        objects = annotation["objects"]
        tags = annotation["tags"]
        image_id = annotation_info.image_id

        if any(object["geometryType"] == "bitmap" for object in objects):
            sly.logger.debug(f"Found bitmap annotation in image with ID {image_id}.")
            annotated_image_ids.append(image_id)

        elif tags:
            sly.logger.debug(f"Found tag annotation in image with ID {image_id}.")

            if any(tag["name"] == g.TAG for tag in tags):
                sly.logger.debug(f"Found tag {g.TAG} in image with ID {image_id}.")
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
    sly.logger.debug("Starting upload of images.")

    upload_button.text = "Uploading..."
    uploaded_text.hide()

    import src.ui.team as team

    team.card._lock_message = "Uploading images..."
    team.card.lock()

    global team_differences_path
    with open(team_differences_path, "r", encoding="utf-8") as f:
        team_differences = json.load(f)

    sly.logger.debug("Successfully loaded team differences JSON file.")

    for workspace_name, projects in team_differences.items():
        sly.logger.debug(f"Working on a workspace {workspace_name}.")

        with progresses["workspace"](
            message=f"Uploading projects in workspace {workspace_name}...",
            total=len(projects),
        ) as ws_pbar:
            for project_name, datasets in projects.items():
                sly.logger.debug(f"Working on a project {project_name}.")

                with progresses["project"](
                    message=f"Uploading datasets in project {project_name}...",
                    total=len(datasets),
                ) as pr_pbar:
                    for dataset_name, dataset in datasets.items():
                        sly.logger.debug(f"Working on a dataset {dataset_name}.")

                        source_dataset_id = dataset["source"][0]
                        target_dataset_id = dataset["target"][0]

                        sly.logger.debug(
                            f"Source dataset ID: {source_dataset_id}. Target dataset ID: {target_dataset_id}."
                        )

                        annotated_images = get_image_data(dataset["annotated_images"])
                        tagged_images = get_image_data(dataset["tagged_images"])

                        if annotated_images is None or tagged_images is None:
                            sly.logger.error(
                                f"Failed to get images data for dataset {dataset_name}."
                            )
                            continue

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

                        project_meta = update_project_meta(
                            source_dataset_id, target_dataset_id
                        )

                        sly.logger.debug("Retrieved and updated project meta.")

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

                        global uploaded_annotated_images
                        uploaded_annotated_images += upload_images_with_annotations(
                            annotated_images,
                            target_dataset_id,
                            dataset_name,
                            annotated_annotations,
                        )

                        sly.logger.debug(
                            f"Uploaded annotated images with annotations to dataset {dataset_name}."
                        )

                        global uploaded_tagged_images
                        uploaded_tagged_images += upload_images_with_annotations(
                            tagged_images,
                            target_dataset_id,
                            dataset_name,
                            tagged_annotations,
                        )

                        sly.logger.debug(
                            f"Uploaded tagged images with annotations to dataset {dataset_name}."
                        )

                        sly.logger.debug(
                            f"Finished uploading images for dataset {dataset_name}."
                        )

                        pr_pbar.update(1)
                    sly.logger.debug(
                        f"Finished uploading datasets in project {project_name}."
                    )

                ws_pbar.update(1)
        sly.logger.debug(f"Finished uploading projects in workspace {workspace_name}.")
    sly.logger.debug("Finished uploading images.")

    upload_button.text = "Upload data"

    team.card.lock_message = (
        "Enter the Target API key and check the connection on step 1️⃣."
    )
    team.card.unlock()

    uploaded_text.text = (
        f"Successfully uploaded {len(uploaded_annotated_images)} annotated images "
        f"and {len(uploaded_tagged_images)} tagged images."
    )


@measure_time
def download_images(images, source_dataset_id, dataset_name):
    sly.logger.debug(f"Starting download of images from dataset {dataset_name}.")

    with progresses["image"](
        message=f"Downloading images from dataset {dataset_name}...",
        total=len(images.ids),
    ) as pbar:
        for batch_names, batch_paths in zip(
            sly.batched(images.ids, batch_size=g.BATCH_SIZE),
            sly.batched(images.paths, batch_size=g.BATCH_SIZE),
        ):
            g.source_api.image.download_paths(
                source_dataset_id, batch_names, batch_paths
            )
            pbar.update(len(batch_names))

            sly.logger.debug(
                f"Downloaded {len(batch_names)} images from dataset {dataset_name}."
            )
        sly.logger.debug(f"Finished download of images from dataset {dataset_name}.")


def update_project_meta(source_dataset_id, target_dataset_id):
    source_project_id = g.source_api.dataset.get_info_by_id(
        source_dataset_id
    ).project_id

    sly.logger.debug(f"Retrieved source project ID: {source_project_id}.")

    meta_json = g.source_api.project.get_meta(source_project_id)
    project_meta = sly.ProjectMeta.from_json(meta_json)

    sly.logger.debug(
        f"Successfully downloaded project meta for dataset {source_dataset_id}."
    )

    target_project_id = k.target_api.dataset.get_info_by_id(
        target_dataset_id
    ).project_id

    sly.logger.debug(f"Retrieved target project ID: {target_project_id}.")

    k.target_api.project.update_meta(target_project_id, project_meta)

    sly.logger.debug(
        f"Successfully updated project meta for dataset {target_dataset_id}."
    )

    return project_meta


@measure_time
def download_annotations(source_dataset_id, image_ids, project_meta):
    sly.logger.debug(
        f"Starting download of annotations from dataset with id {source_dataset_id}."
    )

    annotation_infos = g.source_api.annotation.download_batch(
        source_dataset_id, image_ids
    )

    annotation_jsons = [
        annotation_info.annotation for annotation_info in annotation_infos
    ]

    annotations = [
        sly.Annotation.from_json(json, project_meta) for json in annotation_jsons
    ]

    sly.logger.debug(
        f"Downloaded {len(annotations)} annotations from dataset with id {source_dataset_id}."
    )

    return annotations


@measure_time
def upload_images_with_annotations(
    images, target_dataset_id, dataset_name, annotations
):
    sly.logger.debug(f"Starting upload of images to dataset {dataset_name}.")

    uploaded_image_ids = []

    with progresses["image"](
        message=f"Uploading images to dataset {dataset_name}...", total=len(images.ids)
    ) as pbar:
        for batch_names, batch_paths, batch_metas in zip(
            sly.batched(images.names, batch_size=g.BATCH_SIZE),
            sly.batched(images.paths, batch_size=g.BATCH_SIZE),
            sly.batched(images.metas, batch_size=g.BATCH_SIZE),
        ):
            uploaded_batch = k.target_api.image.upload_paths(
                target_dataset_id, batch_names, batch_paths, metas=batch_metas
            )

            uploaded_batch_ids = [image.id for image in uploaded_batch]
            uploaded_image_ids.extend(uploaded_batch_ids)

            pbar.update(len(batch_names))

            sly.logger.debug(
                f"Uploaded {len(batch_names)} images to dataset {dataset_name}."
            )
        sly.logger.debug(f"Finished upload of images to dataset {dataset_name}.")

    k.target_api.annotation.upload_anns(uploaded_image_ids, annotations)

    sly.logger.debug(
        f"Uploaded {len(annotations)} annotations to dataset {dataset_name}."
    )

    rmtree(g.IMAGES_DIR)
    os.makedirs(g.IMAGES_DIR, exist_ok=True)
    sly.logger.debug(f"Removed directory {g.IMAGES_DIR} and created it again.")

    return len(uploaded_image_ids)


@measure_time
def get_image_data(images):
    image_ids = [image[g.INDICES["images_ids"]] for image in images]
    image_names = [image[g.INDICES["image_names"]] for image in images]
    image_metas = [image[g.INDICES["image_metas"]] for image in images]

    sly.logger.debug(f"Readed {len(image_ids)} image IDs and names.")

    if len(image_ids) == len(image_names) == len(image_metas):
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

    paths = [os.path.join(g.IMAGES_DIR, image_name) for image_name in image_names]

    ImagesData = namedtuple("ImagesData", ["ids", "names", "paths", "metas"])
    images_data = ImagesData(image_ids, image_names, paths, image_metas)

    return images_data
