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
            if custom_frames[0] < start_value:
                self.log.warning("The custom frames to export start BEFORE the scene Tracking Start Frame or the tvpp scene Start Frame")
                self.log.info("An auto clean will be applied to start at {}".format(start_value))
                # Remove frames lower that the tracker frameStart
                custom_frames = [frame for frame in custom_frames if (start_value < frame)]
                # Replace by the true tracker frameStart
                custom_frames.insert(0, start_value)

            instance.data["customFrames"] = custom_frames

            # Update the instance data
            instance.data["frameStart"] = custom_frames[0]
            instance.data["frameEnd"] = custom_frames[-1]
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
            list: A interpreted list of int based on the str input, sorted
        """
        # if no str is given, return a range based on mark_in and mark_out
        if not custom_frames:
            return list(range(int(mark_in), int(mark_out) + 1))

        # Check if custom_frames is correctly written and no illegal character is present
        character_pattern = r'[\d\[\],: -]+'
        match = re.match(character_pattern, custom_frames)

        if not match:
            self.log.warning("!!!!\nUnauthorized characters found: {}\n!!!!".format(match.group()))
            raise NameError

        # Prepare a list to separate each element in custom_frames
        custom_frames = re.sub(r'\s+', '', custom_frames)
        custom_frames_elements = custom_frames.split(",")

        custom_frames_list = set()
        for element in custom_frames_elements:
            matches = re.findall(r'\[(\d+|:)-(\d+|:)\]', element)
            # If element is [#-#], then process the custom_frames_list construction
            if matches:
                # Gather by binome in case multiple [#-#] are not separated by ","
                for match_group in matches:
                    start, end = match_group[0], match_group[1]
                    if start == ':' or int(start) < 0:
                        # Security if must start on mark_in
                        start = mark_in + sceneStartFrame

                    if end == ":" or int(end) < 0:
                        # Security if must end on mark_out
                        end = mark_out + sceneStartFrame

                    # Check if the end is AFTER the start
                    # Can happen if the user set the markIn AFTER the end frame he entered in the custom frame string
                    if int(end) < int(start):
                        self.log.warning("The End frame in [:-{}] is lower than the tvpp markIn {}".format(end, mark_in + sceneStartFrame))
                        raise IndexError

                    # Add frame_index in custom_frames_list for frame_index in [#-#]
                    for frame_index in range(int(start), int(end)+1):
                        custom_frames_list.add(frame_index)

            else:
                if element == ":":
                    self.log.warning("The ':' can't be used outside a [:-:] pattern")
                    raise IndexError
                if int(element) < 0:
                    self.log.warning("Numbers can't be negatives")
                    raise IndexError
                custom_frames_list.add(int(element))

        return list(sorted(custom_frames_list))
