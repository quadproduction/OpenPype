# -*- coding: utf-8 -*-
import re
import gazu
import pyblish.api


class IntegrateKitsuReview(pyblish.api.InstancePlugin):
    """Integrate Kitsu Review"""

    order = pyblish.api.IntegratorOrder + 0.01
    label = "Kitsu Review"
    families = ["render", "image", "online", "plate", "kitsu"]
    optional = True

    def process(self, instance):
        if not getattr(self, 'enabled', True):
            return

        # Check comment has been created
        comment_id = instance.data.get("kitsu_comment", {}).get("id")
        if not comment_id:
            self.log.debug(
                "Comment not created, review not pushed to preview."
            )
            return

        # Add review representations as preview of comment
        task_id = instance.data["kitsu_task"]["id"]
        for representation in instance.data.get("representations", []):
            # Skip if not tagged as review
            if "kitsureview" not in representation.get("tags", []):
                continue

            filenames = representation.get("files")

            custom_frames = instance.data.get("customFrames", [])
            keep_frame_index = instance.data.get("keepFrameIndex", False)
            frame_start = instance.data["frameStart"]
            frame_end = instance.data["frameEnd"]

            # If only one frame force a list
            if not isinstance(filenames, list):
                filenames = [filenames]

            extension = representation.get("ext")
            if not extension:
                self.log.warning("No extension found in representation.")
                raise IndexError

            review_path = representation.get("published_path")
            if not review_path:
                self.log.warning("No publish path found in representation.")
                raise IndexError
            self.log.debug("Found review at: {}".format(review_path))

            frame_indexes = list(range(frame_start, frame_end+1))
            if custom_frames:
                frame_indexes = custom_frames

            if "burnin" in representation.get("tags", []):
                filenames = ["{:04d}.{}".format(index, extension) for index in frame_indexes]

            for file_index in filenames:
                image_filepath = self._rename_output_filepath(review_path, extension, file_index)
                self.log.info(image_filepath)

                gazu.task.add_preview(
                    task_id, comment_id, image_filepath, normalize_movie=getattr(self, 'normalize', True)
                )

            self.log.info("Review upload on comment")

    def _rename_output_filepath(self, published_path, extension, file_index):
        # Replace frame number + extension in given filepath with new file_index
        return re.sub(r"\d{4}\." + re.escape(extension), file_index, published_path)
