import qtawesome
import rv

from openpype.client import get_representations, get_asset_by_name
from openpype.hosts.openrv.api.pipeline import get_containers
from openpype.hosts.openrv.api import lib
from openpype.pipeline import get_current_project_name

from openpype.pipeline import (
    AutoCreator,
    CreatedInstance,
)


class AnnotationCreator(AutoCreator):
    """Collect each drawn annotation over a loaded container as an annotation.
    """
    identifier = "annotation"
    family = "annotation"
    label = "Annotation"

    default_variant = "Main"

    create_allow_context_change = False

    def create(self, options=None):
        # We never create an instance since it's collected from user
        # drawn annotations
        pass

    def collect_instances(self):

        project_name = get_current_project_name()

        # Query the representations in one go (optimization)
        # TODO: We could optimize more by first checking annotated frames
        #   and then only query the representations for those containers
        #   that have any annotated frames.
        containers = list(get_containers())
        representation_ids = set(c["representation"] for c in containers)
        representations = get_representations(
            project_name, representation_ids=representation_ids
        )
        representations_by_id = {
            str(repre["_id"]): repre for repre in representations
        }

        with lib.maintained_view():
            for container in containers:
                self._collect_container(container,
                                        project_name,
                                        representations_by_id)

    def _collect_container(self,
                           container,
                           project_name,
                           representations_by_id):

        node = container["node"]
        self.log.debug(f"Processing container node: {node}")

        # View this particular group to get its marked and annotated frames
        # TODO: This will only find annotations on the actual source group
        #   and not for e.g. the source in the `defaultSequence`.
        # For now it's easiest to enable 'Annotation > Configure > Draw On
        # Source If Possible' so that most annotations end up on source
        source_group = rv.commands.nodeGroup(node)
        rv.commands.setViewNode(source_group)
        annotated_frames = rv.extra_commands.findAnnotatedFrames()
        if not annotated_frames:
            return

        namespace = container["namespace"]
        repre_id = container["representation"]
        repre_doc = representations_by_id.get(repre_id)
        if not repre_doc:
            # This could happen if for example a representation was loaded
            # through the library loader
            self.log.warning(f"No representation found in database for "
                             f"container: {container}")
            return

        repre_context = repre_doc["context"]
        source_representation_asset = repre_context["asset"]
        source_representation_task = repre_context["task"]["name"]

        # QUESTION Do we want to do anything with marked frames?
        # for marked in marked_frames:
        #     print("MARKED ------------ ", container, marked, source_group)

        source_representation_asset_doc = get_asset_by_name(
            project_name=project_name,
            asset_name=source_representation_asset
        )

        for noted_frame in annotated_frames:
            print(f"Found annotation for {source_group} frame {noted_frame}")

            variant = f"{namespace}_{noted_frame}"
            subset_name = self.get_subset_name(
                variant=variant,
                task_name=source_representation_task,
                asset_doc=source_representation_asset_doc,
                project_name=project_name,
            )
            data = {
                "tags": ["review", "ftrackreview"],
                "task": source_representation_task,
                "asset": source_representation_asset,
                "subset": subset_name,
                "label": subset_name,
                "publish": True,
                "review": True,
                "annotated_frame": noted_frame,

                # TODO: Retrieve actual review comment for annotated frame
                "comment": "NEW COMMENT FROM UI {}".format(noted_frame),
            }

            instance = CreatedInstance(
                family=self.family,
                subset_name=data["subset"],
                data=data,
                creator=self
            )

            self._add_instance_to_context(instance)

    def update_instances(self, update_list):
        # TODO: Implement storage of annotation instance settings
        #   Need to define where to store the annotation instance data.
        pass

    def get_icon(self):
        return qtawesome.icon("fa.comments", color="white")
