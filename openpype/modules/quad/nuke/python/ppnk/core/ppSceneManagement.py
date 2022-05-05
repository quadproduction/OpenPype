
import logging
import nuke

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppSceneManagement')
logger.setLevel(logging.INFO)


def get_dependency_paths():
    """
    Scan Scene to retrieve dependency path.
    """
    dependency_paths = []

    def validate_and_append(file_path):
        """validate that a file is ok to be a dependency"""
        dependency_paths.append(file_path)

    # get all nodes dependencies
    for read_node in nuke.allNodes('Read'):
        validate_and_append(read_node.knob('file').value())
    for camera_node in nuke.allNodes('Camera2'):
        if camera_node.knob('read_from_file').value():
            validate_and_append(camera_node.knob('file').value())
    for readGeo_node in nuke.allNodes('ReadGeo2'):
        validate_and_append(readGeo_node.knob('file').value())
    for mxi_mixer_node in nuke.allNodes('MxiMixer'):
        validate_and_append(mxi_mixer_node.knob('Filename').value())
    for mxi_mask_node in nuke.allNodes('MxiMask'):
        validate_and_append(mxi_mask_node.knob('mxs_file').value())
    return dependency_paths
