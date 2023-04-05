import supervisely as sly

from supervisely.app.widgets import Container

import src.ui.keys as keys
import src.ui.team as team
import src.ui.update as update

layout = Container(
    widgets=[keys.card, team.card, update.upload_card, update.status_card]
)

app = sly.Application(layout=layout)
