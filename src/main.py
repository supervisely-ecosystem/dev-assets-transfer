import supervisely as sly

from supervisely.app.widgets import Container

import src.ui.keys as keys

# import src.ui.settings as settings
# import src.ui.compare as compare
# import src.ui.update as update
import src.ui.transfer as transfer

layout = Container(widgets=[keys.card, transfer.card])

app = sly.Application(layout=layout)
