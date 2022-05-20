import maya.cmds as cmds
import ppma.core.ppNode as ppNode
import ppma.core.ppSceneManagement as ppSceneManagement
import time
import os


class Importer(object):
    """docstring for Importer"""
    def __init__(self, parent):
        super(Importer, self).__init__()
        # for eassily retrieve sgtk instance etc..
        self.p = parent
        self.logger = parent.logger
        self.tk = parent.tk
        self.ctx = parent.ctx

        self.name = "Camera Maya Importer"

        self.input_files = []

    def _clean_force_remapping_reference(self):
        """
        this function remove the unused force remapping reference node
        """
        self.logger.info("Clean Force Remapping Reference Node")
        r = ppNode.Reference()
        cAttr = ppNode.CustomAttr()
        # buildNode name pattern
        pattern = "%s_%s*" % (cAttr.prefix, r.scriptNodeAttrReferenceNode)
        # get node
        nodes = cmds.ls(pattern)
        for n in nodes:
            # check if ref node associated exist
            if cmds.objExists("%s.%s_%s" % (n, cAttr.prefix, r.scriptNodeAttrReferenceNode)):
                refNode = cmds.getAttr("%s.%s_%s" % (n, cAttr.prefix, r.scriptNodeAttrReferenceNode))
                if refNode:
                    if not cmds.objExists(refNode):
                        cmds.delete(n)

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
            ['published_file_type.PublishedFileType.id', 'is', 12],  # 14 Camera
            ['name', 'is', 'cambaked'],  # publish name cambaked
            ['sg_status_list', 'is_not', 'omt']
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
        return True

    def _find_node_relative_to_sg_pf(self, sg_published_file):
        """
        """
        self.logger.info("Find Node relative to sg_published_file : {0}".format(sg_published_file.get("path").get("local_path")))
        # load meta_data for retrieving parent asset name
        sg_pf = self.p._get_decrypted_meta_data(sg_published_file)
        self.logger.debug("\t -- sg_published_file")
        for k in sorted(sg_pf.keys()):
            self.logger.debug("\t {0}: {1}".format(k, sg_pf[k]))
        # check each reference node
        for ref_node in self.p.references.keys():
            if self.p.references[ref_node].ctx:
                # get formatted reference data
                rf = self.p._get_reference_data(reference=self.p.references[ref_node])
                # debug log
                self.logger.debug("\t -- ref_node")
                for k in sorted(rf.keys()):
                    self.logger.debug("\t\t {0}: {1}".format(k, rf[k]))
                # case we already change reference to an abc file,
                # we must retrieve previous data from the previous abc published file
                if rf["entity_type"] == 'Shot' and os.path.splitext(rf["path"])[1] == ".abc":
                    self.logger.debug("Special Case it's an ABC")
                    decrypted_sg_pf = self.p._get_meta_data_from_path(path=rf["path"])
                    # update rf by tmp_sg_pf meta_data
                    rf.update(decrypted_sg_pf)
                    self.logger.debug("\t\t -- ref_node - updated by publsihed file")
                    for k in sorted(rf.keys()):
                        self.logger.debug("\t\t\t {0}: {1}".format(k, rf[k]))
                # check if reference node match our sg_published files
                match = True
                for k in ["entity_name", "entity_type", "step", "instance_number"]:
                    if rf[k] != sg_pf[k]:
                        match = False
                        break
                if match:
                    ref_node_found = True
                    # double check if parent are equal
                    # we don't test this before to increase performance
                    root_node = self.p.references[ref_node].getRootNode(refNode=ref_node)
                    parent_root_node = cmds.listRelatives(root_node, parent=True)[0]
                    ent = ppSceneManagement.Entity()
                    ent.getEntityInfo(node=parent_root_node)
                    rf["parent_entity_name"] = ent.info["entityName"]

                    if sg_pf["parent_entity_name"] != rf["parent_entity_name"]:
                        ref_node_found = False

                    if ref_node_found:
                        self.logger.debug("Reference Node found : {0}".format(rf))
                        return rf
        self.logger.debug("Reference Node Not found")
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

    def _update_reference(self, ref_node, filename):
        """
        """
        self.logger.info("Update Reference - ref_node: {0} / filename: {1}".format(ref_node, filename))
        r = ppNode.Reference()
        r.do_ReplaceReference(refNode=ref_node, path=filename, forceRemapping=True)
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
        rf = self._find_node_relative_to_sg_pf(sg_published_file)

        # if path exactly the same, do nothing
        if rf:
            if rf["path"] == sg_published_file.get("path").get("local_path"):
                return True

        # if not rf, create an asset properly for update it by our sg_published_file
        if not rf:
            rf = self._create_asset(sg_published_file)

        # update the reference node
        if rf:
            self._update_reference(ref_node=rf.get("ref_node"), filename=sg_published_file.get("path").get("local_path"))
        else:
            # can't import properly asset and update it
            # so we create a basic reference
            r = ppNode.Reference()
            r.do_createReference(namespace=sg_published_file.get("name"), filename=sg_published_file.get('path')('local_path'))
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
