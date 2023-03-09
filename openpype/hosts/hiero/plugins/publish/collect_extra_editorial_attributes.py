from tracemalloc import start
import pyblish.api


class CollectExtraEditorialAttributes(pyblish.api.InstancePlugin):
    """Collect extra editorial attributes."""

    order = pyblish.api.CollectorOrder + 0.449
    label = "Collect Extra Editorial Attributes"
    hosts = ["hiero"]
    families = ["clip"]

    def process(self, instance):
        item = instance.data['item']
        self.log.debug("ITEM: {}".format(item))

        # rush_name == metadata > exr > owner OR clipName
        # head_in == tag OP > handle start == frame start - handle start
        # tail out == tag OP > handle end == (rush frame out - rush frame in + 1) + frame start + handle end

        # rush frame in == spreadsheet > src in (frame, from rush)
        # rush frame out == spreadsheet > src out (frame, from rush)
        # rush tc in == spreadsheet > src in (timecode, from rush)
        # rush tc out == spreadsheet > src out (timecode, from rush)
        # record frame in == spreadsheet > src in (frame, from clip)
        # record frame out == spreadsheet > dist out (frame, from clip)
        # record tc in == spreadsheet > src in (timecode, from clip)
        # record tc out == spreadsheet > dist out (timecode, from clip)

        if not extra_attr:
            # frame start == tag OP > workfile frame start
            # frame end == tag OP > workfile frame start == (rush frame out - rush frame in + 1) + frame start
        else:
            # frame start == tag OP > workfile frame start == old rush tc in - new tush tc in + old frame start
            # frame end == tag OP > workfile frame start == (new rush frame out - new rush frame in + 1) + (old rush tc in - new rush tc in + old frame start)
