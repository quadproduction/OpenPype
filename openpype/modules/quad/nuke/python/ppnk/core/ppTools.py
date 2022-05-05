
import os
import logging
import re
import nuke
import sgtk
import ppUtils.ppColorSpace as ppColorSpace

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppTools')
logger.setLevel(logging.DEBUG)


def get_dependencies():
    """
    Find all dependencies for the current nuke script
    """

    # get dependencies
    nodes_type_list = [
        'Read'
    ]

    dependency_paths = []

    for node_type in nodes_type_list:
        for read_node in nuke.allNodes(node_type):
            # make sure we have a file path and normalize it
            # file knobs set to "" in Python will evaluate to None. This is different than
            # if you set file to an empty string in the UI, which will evaluate to ""!
            file_name = read_node.knob("file").evaluate()
            if not file_name:
                continue
            file_name = file_name.replace('/', os.path.sep)

            dependency_paths.append(file_name)

    return dependency_paths


def get_next_name_available(name):
    """
    """
    new_name = name

    # get nodes list
    nodes = []
    for n in nuke.allNodes():
        nodes.append(n.knob("name").value())

    if name in nodes:

        # check if we have digits into name
        digits = re.sub("[^0-9]", "", name)

        if digits:
            new_digits = int(digits) + 1
            new_name = name.replace(str(digits), str(new_digits))
        else:
            # no digits found so
            new_name = "{name}_001".format(name=name)

    return new_name


def get_name_from_path(path):
    """
    "/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx"
    """
    # isolate name
    basename = os.path.basename(path)
    # remove ext en padding
    root_name = basename.split(".")[0]

    return root_name


def get_format(width=None, height=None, pixelAspect=1.0, name=None):
    """
    "/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx"
    """

    # list all format
    formats = nuke.formats()

    for f in formats:
        if name:
            if name == f.name():
                return f
        else:
            # check if match
            if width == f.width() and height == f.height() and pixelAspect == f.pixelAspect():
                return f

    return None


class Ocio(object):
    """docstring for Ocio_context"""
    def __init__(self):
        super(Ocio, self).__init__()

        self.cs = ppColorSpace.ColorSpace()
        self.ocio_context = None

        self.node = None

        # ocio attr on node
        self.ocio_attrs = {
            "key1": None,
            "key2": None,
            "key3": None,
            "key4": None,

            "value1": None,
            "value2": None,
            "value3": None,
            "value4": None,
        }

    def _get_cocio_context_from_env(self):
        """
        """
        self.ocio_context = self.cs.get_ocio_context_env()

    def _clear_ocio_attr_on_node(self, node):
        """
        """
        for k in self.ocio_attrs.keys():
            node.knob(k).setValue()

    def _set_ocio_attr_on_node(self, node, data):
        """
        """
        for i in range(0, len(data.keys())):
            key = sorted(data.keys())[i]
            value = data.get(key)
            node.knob("key{i}".format(i=i + 1)).setValue(key)
            node.knob("value{i}".format(i=i + 1)).setValue(value)

            if key not in os.environ:
                if value:
                    os.environ[key] = value

    def set_ocio_context_to_node(self, node, seq=None, shot=None, sg_publish_data={}, from_env=False):
        """
        """
        if not nuke.exists(node.name()):
            raise RuntimeError("This node : {n} not exists.".format(n=node.name()))

        self._get_cocio_context_from_env()
        logger.info('------------------ ocio_context: %s' % self.ocio_context)

        if sg_publish_data:
            # try to retrieve seq and shot
            if "entity.Shot.sg_sequence" in sg_publish_data.keys() and not seq:
                seq = sg_publish_data.get("entity.Shot.sg_sequence").get("name")
            if "entity" in sg_publish_data.keys() and not shot:
                shot = sg_publish_data.get("entity").get("name")

        if seq:
            self.ocio_context["PP_SEQ"] = seq
        if shot:
            self.ocio_context["PP_SHOT"] = shot

        # push ocio context to node
        if not seq and not shot and not from_env:
            return
        else:
            # push to node
            return self._set_ocio_attr_on_node(node=node, data=self.ocio_context)


def set_ocio_context_to_node(node, seq=None, shot=None, sg_publish_data={}, from_env=False):
    """
    """
    o = Ocio()
    o.set_ocio_context_to_node(node=node, seq=seq, shot=shot, sg_publish_data=sg_publish_data, from_env=from_env)


def auto_set_context_selected_ocio_node(node_type=[]):
    """
    """
    sel = nuke.selectedNodes()
    if not sel:
        raise RuntimeError("Please select a node before.")
    
    auto_set_context_ocio_node(node_type=[], sel=sel)


def auto_set_context_ocio_node(node_type=[], sel=[]):
    """
    This function get the context from sgtk and try to applied it on each ocio node.
    :param node_type: specify node type list included for auto-set. like ['OCIODisplay', 'OCIOColorSpace']
    :type node_type: list

    :returns: nothing but self.sgCmds is initialized
    :rtype: None
    """
    # ocio node type which accept context
    ocio_node_type_available = [
        "OCIODisplay",
        "OCIOColorSpace"
    ]

    ocio_node_type_list = []
    if not node_type:
        ocio_node_type_list = ocio_node_type_available
    else:
        ocio_node_type_list = node_type

    nodes = []
    for node_type in ocio_node_type_list:
        if sel:
            for n in sel:
                if n.Class() == node_type:
                    nodes.append(n)
        else:
            ns = nuke.allNodes(node_type)
            if ns:
                nodes.extend(ns)

    if not nodes:
        return
    else:
        # get context from nuke script path
        nuke_script_path = nuke.root().name()
        logger.info('nuke_script_path : {0}'.format(nuke_script_path))
        tk = sgtk.sgtk_from_path(nuke_script_path)
        ctx = tk.context_from_path(nuke_script_path)

        # check if it's a shot
        if ctx.entity:
            if ctx.entity.get("type") == "Shot":

                for n in nodes:
                    #
                    shot = ctx.entity.get("name")
                    logger.info("Set context on node : {node_name}, Shot : {shot}".format(node_name=n.name(), shot=shot))
                    set_ocio_context_to_node(node=n, seq=None, shot=shot, sg_publish_data={}, from_env=False)
