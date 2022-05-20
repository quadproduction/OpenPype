import logging
from . import imp_abc_maya_reference
from . import imp_abc_vray
from . import imp_camera_maya
from ppSgtkLibs import ppSgtkCmds
import ppma.core.ppNode as ppNode
from tank_vendor import yaml
import re
# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)


class Importer(ppSgtkCmds.Cmds):
    """docstring for Importer"""
    def __init__(self, arg=None):
        super(Importer, self).__init__(arg=arg)

        self.logger = logging.getLogger('ppma.action.ppImpExpAnim')
        self.logger.setLevel(logging.DEBUG)
        
        # retrieve sgtk instance
        self.init(arg=arg)

        # init importer
        self.imp_abc_maya_reference = imp_abc_maya_reference.Importer(parent=self)
        self.imp_abc_vray = imp_abc_vray.Importer(parent=self)
        # self.imp_camera_maya = imp_camera_maya.Importer(parent=self)
        # get references in scene
        self.references = ppNode.getReferenceNodeInScene(getContext=True, tk=self.tk)

        # ---
        # special tags for special action
        self.special_tags = ['dyn']
        # sg_published_file cache
        self.sg_published_files_cache = {}

    def start(self, nodes=[]):
        """
        """
        # for each importer
        for action in [self.imp_abc_maya_reference, self.imp_abc_vray]:
            action.imp(nodes=nodes)

    def _search_in_meta_data(self, meta_data, search_key="tags", filter_on_key="entityInfo"):
        """
        This function search in meta data a key.
        """
        if not filter_on_key:
            if search_key in meta_data.keys():
                return meta_data[search_key]
        else:
            if filter_on_key in meta_data.keys():
                if search_key in meta_data[filter_on_key].keys():
                    return meta_data[filter_on_key][search_key]
        return

    def _get_decrypted_meta_data(self, sg_published_file):
        """
        This function extract meta_data contain in sg_published file into a beautifull dict.
        """
        meta_data = yaml.load(sg_published_file['sg_pp_meta_data'])
        self.logger.info(meta_data)
        result = {
            "path": sg_published_file['path']['local_path'],
            "maya_name": meta_data['entityInfo']['name'],
            "entity_name": meta_data['entityInfo']['entityName'],
            "entity_type": meta_data['entityInfo']['entityType'],
            "step": meta_data['entityInfo']['step'],
            "instance_number": int(re.sub("[^0-9]", "", meta_data['entityInfo']['namespace'])),
            "tags": self._search_in_meta_data(meta_data, search_key="tags", filter_on_key="entityInfo"),
            "special_tag": False,
            "parent_entity_name": None
        }
        if 'entityParentInfo' in meta_data.keys():
            result["parent_entity_name"] = meta_data['entityParentInfo']['entityName']
        # check if sg_pf_tags contains special tags
        for s_t in self.special_tags:
            if s_t in result["tags"]:
                result["special_tag"] = True
        return result

    def _get_reference_data(self, reference):
        """
        This function take a reference object and convert it to a beautifull dict.
        """
        result = {
            "ref_node": reference.refNode,
            "path": reference.filename,
            "maya_name": reference.namespace.split(':')[0],
            "instance_number": 1,
            "step": None,
            "parent_entity_name": None
        }
        try:
            result["entity_name"] = reference.ctx.entity['name']
            result["entity_type"] = reference.ctx.entity['type']
            result["step"] = reference.ctx.step['name']
        except:
            self.logger.warning("Can't retrieve Context from :\n\tReference Node : {0}\n\tReference Filename : {1}".format(reference.refNode, reference.filename))
        try:
            result["instance_number"] = int(re.sub("[^0-9]", "", reference.namespace))
        except:
            pass
        return result

    def _get_meta_data_from_path(self, path):
        """
        This function retrieve sg_published file data
        """
        sg_pf = None
        # check if the path is not already cached
        if path in self.sg_published_files_cache.keys():
            sg_pf = self.sg_published_files_cache.get(path)
        else:
            # we assume project path always start by /prod/project/
            # and path cache contain only the path after /prod/project/
            path_cache = "/".join(path.split('/')[3:])
            filters = [['path_cache', 'is', path_cache]]
            fields_return = ['id', 'sg_pp_meta_data', 'path']
            sg_pf = self.tk.shotgun.find_one('PublishedFile', filters, fields_return)
        decrypted_sg_pf = self._get_decrypted_meta_data(sg_published_file=sg_pf)
        return decrypted_sg_pf
