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
            if type(filenames) != list:
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

            if "burnin" in representation.get("tags", []):
                enumerate_files = zip(list(range(frame_start, frame_end+1)), filenames)
                # Update the enumerate_files index if custom_frames is given
                if custom_frames:
                    enumerate_files = zip(custom_frames, filenames)
                filenames = ["{:04d}.{}".format(index, extension) for index, file in enumerate_files]

            for filename in filenames:
                image_filepath = self._rename_output_filepath(review_path, extension, filename)
                self.log.info(image_filepath)

                gazu.task.add_preview(
                    task_id, comment_id, image_filepath, normalize_movie=getattr(self, 'normalize', True)
                )

            self.log.info("Review upload on comment")

    def _rename_output_filepath(self, published_path, extension, filename):
        # Replace frame number + extension in given filepath with new filename
        return re.sub(r"\d{4}\." + re.escape(extension), filename, published_path)
