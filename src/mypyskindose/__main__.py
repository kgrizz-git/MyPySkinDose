"""Allow running mypyskindose as a module: python -m mypyskindose"""

import sys
from mypyskindose.main import get_argument_parser, main
from mypyskindose.constants import RUN_ARGUMENTS_MODE_GUI
from mypyskindose.dev_data import DEVELOPMENT_PARAMETERS
import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    args = get_argument_parser(sys.argv[1:])

    if args.mode == RUN_ARGUMENTS_MODE_GUI:
        from mypyskindose.gui.app import run_gui
        run_gui(native=getattr(args, "native", False))
    else:
        if (run_settings := args.settings) is None:
            logger.warning("No settings specified. Running with development parameters")
            run_settings = DEVELOPMENT_PARAMETERS

        main(file_path=args.file_path, settings=run_settings)
