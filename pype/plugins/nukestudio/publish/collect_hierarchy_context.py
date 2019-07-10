import pyblish.api
import avalon.api as avalon
import re


class CollectHierarchyInstance(pyblish.api.ContextPlugin):
    """Collecting hierarchy context from `parents` and `hierarchy` data
    present in `clip` family instances coming from the request json data file

    It will add `hierarchical_context` into each instance for integrate
    plugins to be able to create needed parents for the context if they
    don't exist yet
    """

    label = "Collect Hierarchy Clip"
    order = pyblish.api.CollectorOrder + 0.101
    families = ["clip"]

    def convert_to_entity(self, key, value):
        # ftrack compatible entity types
        types = {"shot": "Shot",
                 "folder": "Folder",
                 "episode": "Episode",
                 "sequence": "Sequence",
                 "track": "Sequence",
                 }
        # convert to entity type
        entity_type = types.get(key, None)

        # return if any
        if entity_type:
            return {"entityType": entity_type, "entityName": value}

    def process(self, context):

        for instance in context[:]:
            tags = instance.data.get("tags", None)
            clip = instance.data["item"]
            asset = instance.data.get("asset")

            # build data for inner nukestudio project property
            data = {
                "sequence": (
                    context.data['activeSequence'].name().replace(' ', '_')
                ),
                "track": clip.parent().name().replace(' ', '_'),
                "clip": asset
            }
            self.log.debug("__ data: {}".format(data))

            # checking if tags are available
            self.log.debug("__ instance.data[name]: {}".format(
                instance.data["name"]))
            self.log.debug("__ tags: {}".format(tags))

            if not tags:
                return

            # loop trough all tags
            for t in tags:
                t_metadata = dict(t["metadata"])
                t_type = t_metadata.get("tag.label", "")
                t_note = t_metadata.get("tag.note", "")

                self.log.debug("__ t_type: {}".format(t_type))

                # and finding only hierarchical tag
                if "hierarchy" in t_type.lower():
                    d_metadata = dict()
                    parents = list()

                    # main template from Tag.note
                    template = t_note

                    # if shot in template then remove it
                    if "shot" in template.lower():
                        instance.data["asset"] = [
                            t for t in template.split('/')][-1]
                        template = "/".join([t for t in template.split('/')][0:-1])

                    # take template from Tag.note and break it into parts
                    template_split = template.split("/")
                    patern = re.compile(r"\{([a-z]*?)\}")
                    par_split = [patern.findall(t)
                                 for t in template.split("/")]

                    # format all {} in two layers
                    for k, v in t_metadata.items():
                        new_k = k.split(".")[1]

                        # ignore all help strings
                        if 'help' in k:
                            continue
                        # self.log.info("__ new_k: `{}`".format(new_k))
                        try:
                            # first try all data and context data to
                            # add to individual properties
                            new_v = str(v).format(
                                **dict(context.data, **data))
                            d_metadata[new_k] = new_v

                            # create parents
                            # find matching index of order
                            p_match_i = [i for i, p in enumerate(par_split)
                                         if new_k in p]

                            # if any is matching then convert to entity_types
                            if p_match_i:
                                parent = self.convert_to_entity(
                                    new_k, template_split[p_match_i[0]])
                                parents.insert(p_match_i[0], parent)
                        except Exception:
                            d_metadata[new_k] = v

                    # create new shot asset name
                    instance.data["asset"] = instance.data["asset"].format(
                        **d_metadata)
                    self.log.debug(
                        "__ instance.data[asset]: "
                        "{}".format(instance.data["asset"])
                    )

                    # lastly fill those individual properties itno
                    # format the string with collected data
                    parents = [{"entityName": p["entityName"].format(
                        **d_metadata), "entityType": p["entityType"]}
                        for p in parents]
                    self.log.debug("__ parents: {}".format(parents))

                    hierarchy = template.format(
                        **d_metadata)
                    self.log.debug("__ hierarchy: {}".format(hierarchy))

                    # check if hierarchy attribute is already created
                    # it should not be so return warning if it is
                    hd = instance.data.get("hierarchy")
                    assert not hd, (
                        "Only one Hierarchy Tag is allowed. "
                        "Clip: `{}`".format(asset)
                    )

                    assetsShared = {
                        asset: {
                            "asset": instance.data["asset"],
                            "hierarchy": hierarchy,
                            "parents": parents,
                            "tasks":  instance.data['tasks']
                        }}
                    self.log.debug("__ assetsShared: {}".format(assetsShared))
                    # add formated hierarchy path into instance data
                    instance.data["hierarchy"] = hierarchy
                    instance.data["parents"] = parents
                    context.data["assetsShared"].update(
                        assetsShared)


class CollectHierarchyContext(pyblish.api.ContextPlugin):
    '''Collecting Hierarchy from instaces and building
    context hierarchy tree
    '''

    label = "Collect Hierarchy Context"
    order = pyblish.api.CollectorOrder + 0.102

    def update_dict(self, ex_dict, new_dict):
        for key in ex_dict:
            if key in new_dict and isinstance(ex_dict[key], dict):
                new_dict[key] = self.update_dict(ex_dict[key], new_dict[key])
            else:
                if ex_dict.get(key) and new_dict.get(key):
                    continue
                else:
                    new_dict[key] = ex_dict[key]

        return new_dict

    def process(self, context):
        instances = context[:]
        # create hierarchyContext attr if context has none

        temp_context = {}
        for instance in instances:
            if 'projectfile' in instance.data.get('family', ''):
                continue

            name = instance.data["asset"]

            # get handles
            handle_start = int(instance.data["handleStart"])
            handle_end = int(instance.data["handleEnd"])

            # inject assetsShared to other plates types
            assets_shared = context.data.get("assetsShared")

            if assets_shared:
                s_asset_data = assets_shared.get(name)
                if s_asset_data:
                    self.log.debug("__ s_asset_data: {}".format(s_asset_data))
                    name = instance.data["asset"] = s_asset_data["asset"]
                    instance.data["parents"] = s_asset_data["parents"]
                    instance.data["hierarchy"] = s_asset_data["hierarchy"]
                    instance.data["tasks"] = s_asset_data["tasks"]

            self.log.debug(
                "__ instance.data[parents]: {}".format(
                    instance.data["parents"]
                )
            )
            self.log.debug(
                "__ instance.data[hierarchy]: {}".format(
                    instance.data["hierarchy"]
                )
            )
            self.log.debug(
                "__ instance.data[name]: {}".format(instance.data["name"])
            )

            in_info = {}

            in_info["inputs"] = [
                x["_id"] for x in instance.data.get("assetbuilds", [])
            ]

            # suppose that all instances are Shots
            in_info['entity_type'] = 'Shot'

            # get custom attributes of the shot
            if instance.data.get("main"):
                start_frame = instance.data.get("frameStart", 0)

                in_info['custom_attributes'] = {
                    'handles': int(instance.data.get('handles')),
                    'handle_start': handle_start,
                    'handle_end': handle_end,
                    'fstart': int(instance.data["startFrame"]),
                    'fend': int(instance.data["endFrame"]),
                    'fps': instance.data["fps"],
                    "edit_in": int(instance.data["startFrame"]),
                    "edit_out": int(instance.data["endFrame"])
                }
                if start_frame is not 0:
                    in_info['custom_attributes'].update({
                        'fstart': start_frame,
                        'fend': start_frame + (
                            instance.data["endFrame"] - instance.data["startFrame"])
                    })
                # adding SourceResolution if Tag was present
                s_res = instance.data.get("sourceResolution")
                if s_res and instance.data.get("main"):
                    item = instance.data["item"]
                    self.log.debug("TrackItem: `{0}`".format(
                        item))
                    width = int(item.source().mediaSource().width())
                    height = int(item.source().mediaSource().height())
                    self.log.info("Source Width and Height are: `{0} x {1}`".format(
                        width, height))
                    in_info['custom_attributes'].update({
                        "resolution_width": width,
                        "resolution_height": height
                    })

            in_info['tasks'] = instance.data['tasks']

            parents = instance.data.get('parents', [])
            self.log.debug("__ in_info: {}".format(in_info))

            actual = {name: in_info}

            for parent in reversed(parents):
                next_dict = {}
                parent_name = parent["entityName"]
                next_dict[parent_name] = {}
                next_dict[parent_name]["entity_type"] = parent["entityType"]
                next_dict[parent_name]["childs"] = actual
                actual = next_dict

            temp_context = self.update_dict(temp_context, actual)

        # TODO: 100% sure way of get project! Will be Name or Code?
        project_name = avalon.Session["AVALON_PROJECT"]
        final_context = {}
        final_context[project_name] = {}
        final_context[project_name]['entity_type'] = 'Project'
        final_context[project_name]['childs'] = temp_context

        # adding hierarchy context to instance
        context.data["hierarchyContext"] = final_context
        self.log.debug("context.data[hierarchyContext] is: {}".format(
            context.data["hierarchyContext"]))
