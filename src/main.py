import supervisely as sly

from supervisely.app.widgets import Container

import src.ui.keys as keys
import src.ui.settings as settings
import src.ui.compare as compare
import src.ui.update as update

layout = Container(widgets=[keys.card, settings.card, compare.card, update.card])

app = sly.Application(layout=layout)
