import pyblish.api
from openpype.pipeline.editorial import frames_to_timecode

import hiero


class CollectExtraEditorialAttributes(pyblish.api.InstancePlugin):
    """Collect extra editorial attributes."""

    order = pyblish.api.CollectorOrder + 0.449
    label = "Collect Extra Editorial Attributes"
    hosts = ["hiero"]
    families = ["clip"]

    def process(self, instance):
        extra_attr = None
        otio_clip = instance.data["otioClip"]

        rush_name = otio_clip.media_reference.metadata["media.exr.owner"]
        head_in = instance.data['clipInH']
        tail_out = instance.data['clipOutH']
        frame_start = instance.data['frameStart']
        frame_end = instance.data['frameEnd']
        rush_frame_in = instance.data['sourceStart']
        rush_frame_out = instance.data['sourceEnd']
        record_frame_in = instance.data['clipIn']
        record_frame_out = instance.data['clipOut']

        fps = float(otio_clip.range_in_parent().start_time.rate)
        rush_tc_in = frames_to_timecode(rush_frame_in, fps)
        rush_tc_out = frames_to_timecode(rush_frame_out, fps)
        record_tc_in = frames_to_timecode(record_frame_in, fps)
        record_tc_out = frames_to_timecode(record_frame_out, fps)

        self.log.debug("rush_name: {}".format(rush_name))
        self.log.debug("head_in: {}".format(head_in))
        self.log.debug("tail_out: {}".format(tail_out))
        self.log.debug("frame_start: {}".format(frame_start))
        self.log.debug("frame_end: {}".format(frame_end))
        self.log.debug("rush_frame_in: {}".format(rush_frame_in))
        self.log.debug("rush_tc_in: {}".format(rush_tc_in))
        self.log.debug("rush_frame_out: {}".format(rush_frame_out))
        self.log.debug("rush_tc_out: {}".format(rush_tc_out))
        self.log.debug("record_frame_in: {}".format(record_frame_in))
        self.log.debug("record_tc_in: {}".format(record_tc_in))
        self.log.debug("record_frame_out: {}".format(record_frame_out))
        self.log.debug("record_tc_out: {}".format(record_tc_out))
