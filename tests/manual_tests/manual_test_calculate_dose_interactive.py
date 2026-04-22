from base_dev_settings import DEVELOPMENT_PARAMETERS

from mypyskindose import constants
from mypyskindose.main import main
from mypyskindose.settings import PyskindoseSettings

settings = PyskindoseSettings(settings=DEVELOPMENT_PARAMETERS)
settings.mode = constants.MODE_CALCULATE_DOSE
settings.plot.interactivity = True
settings.plot.plot_dosemap = True

main(settings=settings)
