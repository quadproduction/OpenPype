import pyblish.api
import re

class CollectOutputFrameRange(pyblish.api.InstancePlugin):
    """Collect frame start/end from context.

    When instances are collected context does not contain `frameStart` and
    `frameEnd` keys yet. They are collected in global plugin
    `CollectContextEntities`.
    """

    label = "Collect output frame range"
    order = pyblish.api.CollectorOrder + 0.4999
    hosts = ["tvpaint"]
    families = ["review", "render"]

    def process(self, instance):
        asset_doc = instance.data.get("assetEntity")
        if not asset_doc:
            return

        context = instance.context

        frame_start = asset_doc["data"]["frameStart"]
        fps = asset_doc["data"]["fps"]
        frame_end = frame_start + (
            context.data["sceneMarkOut"] - context.data["sceneMarkIn"]
        )
        instance.data["fps"] = fps
        instance.data["frameStart"] = frame_start
        instance.data["frameEnd"] = frame_end
        self.log.info(
            "Set frames {}-{} on instance {} ".format(
                frame_start, frame_end, instance.data["subset"]
            )
        )

        custom_instance_frames = instance.data["creator_attributes"].get("custom_frames", None)
        keep_frame_index = instance.data["creator_attributes"].get("keep_frame_index", False)

        # If we want to keep the frame index from the tvpp scene and not recalculate them
        if keep_frame_index:
            frame_start = (instance.context.data["sceneMarkIn"] + instance.context.data["sceneStartFrame"])
            frame_end = (instance.context.data["sceneMarkOut"] + instance.context.data["sceneStartFrame"])
            instance.data["keepFrameIndex"] = keep_frame_index
            instance.data["frameStart"] = frame_start
            instance.data["frameEnd"] = frame_end

        # If custom frames are given
        if custom_instance_frames:
            # Create a list of custom frame to render
            custom_frames = self.list_custom_frames_export(
                        custom_instance_frames,
                        context.data["sceneMarkIn"],
                        context.data["sceneMarkOut"],
                        context.data["sceneStartFrame"]
                        )

            start_value = max(asset_doc["data"]["frameStart"], instance.context.data["sceneStartFrame"])
            # Avoid exporting frame before the tracker frameStart or scene sceneStartFrame
            if min(custom_frames) < start_value:
                self.log.warning("The custom frames to export start BEFORE the scene Tracking Start Frame or the tvpp scene Start Frame")
                self.log.info("An auto clean will be applied to start at {}".format(start_value))
                # Remove frames lower that the tracker frameStart
                custom_frames = [frame for frame in custom_frames if (start_value < frame)]
                # Replace by the true tracker frameStart
                custom_frames.insert(0, start_value)

            instance.data["customFrames"] = custom_frames

            # Update the instance data
            instance.data["frameStart"] = min(custom_frames)
            instance.data["frameEnd"] = max(custom_frames)

            if custom_instance_frames:
                self.log.info("Export Custom frames {}".format(custom_frames))

        if custom_instance_frames or keep_frame_index:
            self.log.info("Changed frames Start/End {}-{} on instance {} ".format(instance.data["frameStart"] , instance.data["frameEnd"], instance.data["subset"]))

    def list_custom_frames_export(self, custom_frames , mark_in, mark_out, sceneStartFrame):
        """
        Create a list of frame to export based on a string

        Args:
            custom_frames(str): frames to export, can be :
                                "1, 4, 6"
                                "[1-6], 15"
                                "[:-4], 6"
                                "1, 4, [6-:]"
                                the ":" implise that it will go to the mark_in or to the mark_out
            mark_in(int): frame on which is set markIn in tvpp
            mark_out(int): frame on which is set markOut in tvpp
            sceneStartFrame(int): frame de start du projet tvpp

        Returns:
            list: A interpreted list of int based on the str input
        """
        # if no str is given, return a range based on mark_in and mark_out
        if not custom_frames:
            return list(range(int(mark_in), int(mark_out) + 1))

        # Search intervals with regex
        pattern = r'\[(\d+|:)-(\d+|:)\]'
        range_pattern = re.findall(pattern, custom_frames)

        # Replace all intervals by int range
        for start, end in range_pattern:
            # Process Start of interval
            expanded_start = start
            if start in (':'):
                # Security if no start defined or
                # Case if must start on mark_in
                expanded_start = mark_in + sceneStartFrame

            # Process End of interval
            expanded_end = end
            if end in (":"):
                # Security if no end defined or
                # Case if must end on mark_out
                expanded_end = mark_out + sceneStartFrame

            # check if the end if AFTER the start
            # Can happen if the user set the markIn AFTER the end frame he entered in the custom frame string
            if int(expanded_end) < int(expanded_start):
                self.log.warning("The End frame in [:-{}] is lower than the tvpp markIn {}".format(expanded_end, start))
                raise IndexError

            # Create the replacement string
            expanded = ', '.join(str(i) for i in range(int(expanded_start), int(expanded_end) + 1))

            # Replace the interval by the ranged string
            custom_frames = re.sub(r'\[' + start + '-' + end + r'\]', expanded, custom_frames)

        # Clean to return a list of int
        return [int(x.strip()) for x in custom_frames.split(',')]
