import nuke
import os
import logging
import ppSgtkLibs.ppSgtkUtils
import ppnk.core.ppSettings as ppSettings

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppInitNuke')
logger.setLevel(logging.INFO)


class Init(ppSgtkLibs.ppSgtkUtils.InitTk):
    """docstring for ClassName"""
    def __init__(self, arg=None):
        super(Init, self).__init__()
        logger.info('Retrieve settings from Shotgun...')
        self.settings = ppSettings.Settings()

    def _load_ocio(self):
        if os.environ.get('OCIO'):
            if nuke.NUKE_VERSION_MAJOR >= 10:
                logger.info("OCIO env var detected, change color management.")
                root = nuke.root()
                cm_values = root.knob("colorManagement").values()
                if "OCIO" in cm_values:
                    logger.info("Set Color Management to OCIO")
                    nuke.knobDefault("Root.colorManagement", "OCIO")
                    nuke.knobDefault("Root.defaultViewerLUT", "OCIO LUTs")
                else:
                    logger.warning("Can't Set OCIO. it doesn't exist in list : {cm_values}".format(cm_values=cm_values))
        else:
            logger.info("OCIO env var not detected.")

    def _get_project_settings(self):
        """
        this functions retiev from shotgun tle project resolution declared.
        """
        pass

    def _set_resolutions_format(self):
        """
        this functions retiev from shotgun tle project resolution declared.
        """
        self.settings._set_project_resolutions()

    def init_script(self):
        """
        """
        # load project resolution aka nuke format
        self._set_resolutions_format()

        # load OCIO
        self._load_ocio()


def init_script():
    """
    this awesome function initialize nuke.
    """
    i = Init()
    i.init_script()
