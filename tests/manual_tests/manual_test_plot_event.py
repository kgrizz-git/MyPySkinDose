from base_dev_settings import DEVELOPMENT_PARAMETERS

from mypyskindose import constants
from mypyskindose.main import main
from mypyskindose.settings import PyskindoseSettings

settings = PyskindoseSettings(settings=DEVELOPMENT_PARAMETERS)
settings.mode = constants.MODE_PLOT_EVENT
settings.plot_event_index = 12

main(settings=settings)
