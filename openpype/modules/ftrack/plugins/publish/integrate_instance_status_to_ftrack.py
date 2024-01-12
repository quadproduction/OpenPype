import pyblish.api


class IntegrateInstanceStatusToFtrack(pyblish.api.InstancePlugin):

    order = pyblish.api.IntegratorOrder + 0.49
    label = "Integrate Instance Status To Ftrack"
    active = True

    def process(self, instance):
        self.log.debug(f"SATUTS_TO_SET: {instance.data['creator_attributes'].get('ftrack_status')}")
