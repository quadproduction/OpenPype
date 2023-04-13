import copy

import clique

from openpype.pipeline import (
    load,
    get_representation_context
)
from openpype.pipeline.load import get_representation_path_from_context

from openpype.hosts.openrv.api.pipeline import imprint_container
from openpype.hosts.openrv.api.commands import (
    set_session_fps,
    reset_frame_range
)
from openpype.lib.transcoding import IMAGE_EXTENSIONS

import rv


class FramesLoader(load.LoaderPlugin):
    """Load frames into OpenRV"""

    label = "Load Frames"
    families = ["*"]
    representations = ["exr"]
    order = 0

    icon = "code-fork"
    color = "orange"

    def load(self, context, name=None, namespace=None, data=None):

        filepath = self._format_path(context)
        # Command fails on unicode so we must force it to be strings
        filepath = str(filepath)

        # node_name = "{}_{}".format(namespace, name) if namespace else name
        namespace = namespace if namespace else context["asset"]["name"]

        set_session_fps()
        reset_frame_range()
        loaded_node = rv.commands.addSourceVerbose([filepath])
        print("loaded_node", loaded_node)
        imprint_container(
            loaded_node,
            name=name,
            namespace=namespace,
            context=context,
            loader=self.__class__.__name__
        )

    def update(self, container, representation):
        node = container["node"]

        context = get_representation_context(representation)
        filepath = self._format_path(context)
        filepath = str(filepath)

        set_session_fps()
        reset_frame_range()
        # change path
        rv.commands.setSourceMedia(node, [filepath])
        # update name
        rv.commands.setStringProperty(node + ".media.name",
                                      ["newname"], True)
        rv.commands.setStringProperty(node + ".media.repName",
                                      ["repname"], True)
        rv.commands.setStringProperty(node + ".openpype.representation",
                                      [str(representation["_id"])], True)

    def remove(self, container):
        # todo: implement remove
        # node = container["node"]
        return

    def _get_sequence_range(self, context):
        """Return frame range for image sequences.

        The start and end frame is based on the start frame and end frame of
        the representation or version documents. A single frame is never
        considered to be a sequence.

        Warning:
            If there are published sequences that do *not* have start and
            end frame data in the database then this will FAIL to detect
            it as a sequence.

        Args:
            context (dict): Representation context.

        Returns:
            tuple or None: (start, end) tuple if it is an image sequence
                otherwise it returns None.

        """
        version = context.get("version", {})
        representation = context.get("representation", {})

        # Only images may be sequences, not videos
        ext = representation.get("ext", representation.get("name"))
        if f".{ext}" not in IMAGE_EXTENSIONS:
            return

        for doc in [representation, version]:
            # Frame range can be set on version or representation.
            # When set on representation it overrides version data.
            data = doc.get("data", {})
            start = data.get("frameStartHandle", data.get("frameStart", None))
            end = data.get("frameEndHandle", data.get("frameEnd", None))

            if start is None or end is None:
                continue

            if start != end:
                return start, end
            else:
                # Single frame
                return

        # Fallback for image sequence that does not have frame start and frame
        # end stored in the database.
        if "frame" in representation.get("context", {}):
            # Guess the frame range from the files
            files = representation.get("files", [])
            if len(files) > 1:
                paths = [f["path"] for f in representation["files"]]
                collections, _remainder = clique.assemble(paths)
                if collections:
                    collection = collections[0]
                    frames = list(collection.indexes)
                    return frames[0], frames[-1]

        return

    def _format_path(self, context):
        """Format the path with correct frame range.

        The openRV load command requires image sequences to be provided
        with `{start}-{end}#` for its frame numbers, for example:
            /path/to/sequence.1001-1010#.exr

        """

        sequence_range = self._get_sequence_range(context)
        if not sequence_range:
            return get_representation_path_from_context(context)

        context = copy.deepcopy(context)
        representation = context["representation"]
        template = representation.get("data", {}).get("template")
        if not template:
            # No template to find token locations for
            return get_representation_path_from_context(context)

        def _placeholder(key):
            # Substitute with a long placeholder value so that potential
            # custom formatting with padding doesn't find its way into
            # our formatting, so that <f> wouldn't be padded as 0<f>
            return "___{}___".format(key)

        # We format UDIM and Frame numbers with their specific tokens. To do so
        # we in-place change the representation context data to format the path
        # with our own data
        start, end = sequence_range
        tokens = {
            "frame": f"{start}-{end}#",
        }
        has_tokens = False
        repre_context = representation["context"]
        for key, _token in tokens.items():
            if key in repre_context:
                repre_context[key] = _placeholder(key)
                has_tokens = True

        # Replace with our custom template that has the tokens set
        representation["data"]["template"] = template
        path = get_representation_path_from_context(context)

        if has_tokens:
            for key, token in tokens.items():
                if key in repre_context:
                    path = path.replace(_placeholder(key), token)

        return path
