import maya.cmds as cmds
import ppma.core.ppNode as ppNode
import ppma.core.ppSceneManagement as ppSceneManagement
import time
import re


class Importer(object):
    """docstring for Importer"""
    def __init__(self, parent):
        super(Importer, self).__init__()
        # for eassily retrieve sgtk instance etc..
        self.p = parent
        self.logger = parent.logger
        self.tk = parent.tk
        self.ctx = parent.ctx

        self.name = "Abc VrayProxy Importer"
        self.input_files = []

    def get_input_files(self):
        """
        retrieve abc linked to shot
        """
        # time the import
        start_time = time.clock()
        self.logger.info("Get Input Files for {0} for {1} {2}".format(self.name, self.ctx.entity['name'], self.ctx.project['name']))
        # get abc linked to context
        filters = [
            ['entity.Shot.code', 'is', self.ctx.entity['name']],
            ['project.Project.name', 'is', self.ctx.project['name']],
            ['published_file_type.PublishedFileType.id', 'is', 14],  # 14 Alembic
            ['sg_status_list', 'is_not', 'omt'],
            ['tag_list', 'is', 'vray']
        ]
        fields_return = ['id', 'code', 'name', 'version_number', 'task', 'sg_pp_meta_data', 'path']
        order = [{'field_name': 'id', 'direction': 'desc'}]
        sg_published_files = self.tk.shotgun.find('PublishedFile', filters, fields_return, order)
        # keep only latest published file
        latest_pf_name = []
        latest_pf_files = []
        for sg_pf in sg_published_files:
            self.logger.debug("Published File %s : %s" % (sg_pf['name'], sg_pf))
            # push sg_pf to sg_published_files_cache
            self.p.sg_published_files_cache[sg_pf["path"]["local_path"]] = sg_pf
            # check if publish name already in latest publishfiles get publish
            if not sg_pf['name'] in latest_pf_name:
                latest_pf_name.append(sg_pf['name'])
                latest_pf_files.append(sg_pf)
        # stop watch
        end_time = time.clock()
        length = end_time - start_time
        self.logger.info("\t {0} Published Files found in {1}".format(len(latest_pf_files), length))
        for abc in latest_pf_files:
            self.logger.info("\t Abc - {code} - {version_number}".format(code=abc.get("code"), version_number=abc.get("version_number")))
        return latest_pf_files

    def _sanity_check_sg_pf(self, sg_published_file):
        """
        check if all required data are contains in the published file
        """
        self.logger.info("Sanity Check sg_published_file : {0}".format(sg_published_file.get("path").get("local_path")))
        if 'sg_pp_meta_data' not in sg_published_file.keys():
            self.logger.error("Can't Import SG Published Files. Published File have no meta_data. {0}".format(sg_published_file.get("code")))
            return False
        return True

    def _get_vraymesh_data(self, vraymesh):
        """
        This function decrypt a vraymesh node and convert it to a beautifull dict.
        """
        result = {
            "ref_node": vraymesh.ref_node,
            "node_name": vraymesh.node_name,
            "path": vraymesh.filename,
            "entity_name": None,
            "entity_type": None,
            "name": vraymesh.pp_name,
            "instance_number": 1,
            "step": None,
            "parent_entity_name": None,
            "maya_name": None
        }
        if vraymesh.is_node_referenced:
            # get reference detail for retrieving asset context
            # check if ref_node already in cache
            reference = None
            if vraymesh.ref_node in self.p.references.keys():
                self.logger.debug("ref_node found in cache : {0}".format(vraymesh.ref_node))
                reference = self.p.references[vraymesh.ref_node]
            else:
                self.logger.debug("get reference detail for node : {0}".format(vraymesh.ref_node))
                reference = ppNode.Reference()
                reference.getReferenceDetail(refNode=vraymesh.ref_node, getContext=True)
            result["entity_name"] = reference.ctx.entity['name']
            result["entity_type"] = reference.ctx.entity['type']
            try:
                result["step"] = reference.ctx.step['name']
            except:
                pass
            try:
                result["instance_number"] = int(re.sub("[^0-9]", "", reference.namespace))
            except:
                pass
        # update maya_name
        result["maya_name"] = "{entity_name}{instance_number}{name}".format(entity_name=result["entity_name"], instance_number="%03d" % result["instance_number"], name=result["name"])
        return result

    def _find_node_relative_to_sg_pf(self, sg_published_file):
        """
        """
        self.logger.info("Find Node relative to sg_published_file : {0}".format(sg_published_file.get("path").get("local_path")))
        # load meta_data for retrieving parent asset name
        sg_pf = self.p._get_decrypted_meta_data(sg_published_file)
        self.logger.debug("\t -- sg_published_file")
        for k in sorted(sg_pf.keys()):
            self.logger.debug("\t {0} : {1}".format(k, sg_pf[k]))

        # list all node VRayMesh
        vraymesh_nodes = ppNode.get_vraymesh_in_scene()
        self.logger.debug("\t -- vraymesh_nodes")
        for k in sorted(vraymesh_nodes.keys()):
            self.logger.debug("\t {0} : {1}".format(k, vraymesh_nodes[k]))
        for vraymesh_node in vraymesh_nodes:
            # get _get_vraymesh_data
            vrm = self._get_vraymesh_data(vraymesh=vraymesh_nodes[vraymesh_node])
            self.logger.debug("\t -- vraymesh")
            for k in sorted(vrm.keys()):
                self.logger.debug("\t {0} : {1}".format(k, vrm[k]))
            # compare
            match = True
            for k in ["entity_name", "entity_type", "maya_name"]:
                if vrm[k] != sg_pf[k]:
                    match = False
                    break
            if match:
                self.logger.debug("VRayMesh Node found : {0}".format(vrm))
                return vrm
        self.logger.debug("VRayMesh Node Not found")
        return

    def _create_asset(self, sg_published_file):
        """
        This function create an Asset into the current scene.
        """
        # load meta_data for retrieving parent asset name
        sg_pf = self.p._get_decrypted_meta_data(sg_published_file)
        # create a reference, the createEntity check in wich step the current scene is
        # and load the preferred asset step for the current scene
        e = ppSceneManagement.Entity()
        ref_node = e.createEntity(
            projectPath=self.tk.project_path,
            entityName=sg_pf['entity_name'],
            entityType=sg_pf['entity_type'],
            instanceNumber=sg_pf['instance_number']
        )
        self.logger.info("ref_node created : {0}".format(ref_node))
        # usually we retrieve the asset in shading so we apply an override for force abc loading
        if ref_node:
            # we looking for the sub reference node (model)
            # get reference detail
            r = ppNode.Reference()
            r.getReferenceDetail(refNode=ref_node)
            sub_ref_nodes = r.getSubReferenceNode(ref_node)
            # post-creation we update reference with the latest abc available
            if ref_node and sub_ref_nodes:
                for sub_ref_node in sub_ref_nodes:
                    # check if it's the same step
                    sub_ref = ppNode.Reference()
                    sub_ref.getReferenceDetail(refNode=sub_ref_node, getContext=True)
                    # get formatted reference data
                    rf = self.p._get_reference_data(reference=sub_ref)
                    return rf

        # no shading asset found
        self.logger.warning("Can't create Asset : {0} {1}".format(sg_pf['entity_name'], sg_pf['entity_type']))
        return

    def _update_vraymesh(self, node, filename):
        """
        """
        self.logger.info("Update VRayMesh - node : {0} / filename: {1}".format(node, filename))
        cmds.setAttr("{0}.fileName2".format(node), filename, type="string")
        return True

    def _import_file(self, sg_published_file):
        """
        import shotgun published file into the scene.
        """
        self.logger.info("Import sg_published_file : {0}".format(sg_published_file.get("path").get("local_path")))
        # sanity check published file
        if not self._sanity_check_sg_pf(sg_published_file):
            return False
        # retrieve node relative to our published file
        vrm = self._find_node_relative_to_sg_pf(sg_published_file)

        # if path exactly the same, do nothing
        if vrm:
            if vrm["path"] == sg_published_file.get("path").get("local_path"):
                return True

        # if not vrm, create a VRayMesh properly for update it by our sg_published_file
        if not vrm:
            vrm = self._create_asset(sg_published_file)

        # update the reference node
        if vrm:
            self._update_vraymesh(node=vrm.get("node_name"), filename=sg_published_file.get("path").get("local_path"))
        else:
            # can't import properly asset and update it
            # so we create a basic reference
            # r.do_createReference(namespace=sg_published_file.get("name"), filename=sg_published_file.get('path')('local_path'))
            return True

    def imp(self, nodes=[]):
        """
        """
        self.logger.info("---")
        self.logger.info("Start - {0}".format(self.name))
        # get files available for the importer
        self.input_files = self.get_input_files()
        # import file
        for input_file in self.input_files:
            if self._import_file(sg_published_file=input_file):
                self.logger.info("Successfuly Imported : {0}".format(input_file.get("path").get("local_path")))
            else:
                self.logger.warning("Not Successfuly Imported : {0}".format(input_file.get("path").get("local_path")))
        self.logger.info("---")
        self.logger.info("End - {0}".format(self.name))

