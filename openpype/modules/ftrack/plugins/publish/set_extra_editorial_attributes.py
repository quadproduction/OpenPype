import os

import pyblish.api
from openpype.pipeline.editorial import frames_to_timecode
from openpype.settings import get_project_settings

import ftrack_api


class IntegrateExtraEditorialAttributes(pyblish.api.InstancePlugin):
    """Integrate extra editorial attributes."""

    order = pyblish.api.IntegratorOrder + 0.47
    label = "Set Extra Editorial Attributes"
    hosts = ["hiero", "flame", "traypublisher"]
    families = ["clip"]
    optional = True
    active = True

    def process(self, instance):
        instance.data['is_custom_attrs_set'] = False
        empty_data = []
        wrong_key = []
        project_settings = get_project_settings(os.getenv("AVALON_PROJECT"))
        rush_and_cut_data = project_settings['ftrack']['publish'][
            'IntegrateExtraEditorialAttributes'
        ]
        rush_and_cut_data.pop('enabled')
        session = self._get_ftrack_session()
        if not session:
            return

        ftrack_custom_attrs = self._get_ftrack_custom_attrs(
            session,
            os.getenv("AVALON_PROJECT"),
            instance
        )

        otio_attributes = self._get_otio_attributes(instance)

        for key, value in rush_and_cut_data.items():
            if value and value in ftrack_custom_attrs.keys():
                ftrack_custom_attrs[value] = otio_attributes[key]
            elif value and value not in ftrack_custom_attrs.keys():
                wrong_key.append(key)
            else:
                empty_data.append(key)

        if empty_data:
            self.log.warning(
                "Empty data in settings for key(s): {}".format(empty_data)
            )
        if wrong_key:
            self.log.warning(
                "Key(s) not found in ftrack custom attributes: {}".format(
                    wrong_key
                )
            )

        session.commit()
        instance.data['is_custom_attrs_set'] = True

    def _get_ftrack_session(self):
        """ Get the extra editorial attrs from Ftrack
        """
        server_url = os.environ["FTRACK_SERVER"]
        api_user = os.environ["FTRACK_API_USER"]
        api_key = os.environ["FTRACK_API_KEY"]
        try:
            session = ftrack_api.Session(
                server_url=server_url,
                api_user=api_user,
                api_key=api_key
            )
        except Exception:
            self.log.warning("Can't log into Ftrack with used credentials:")
            ftrack_cred = {
                "Ftrack server": str(server_url),
                "Username": str(api_user),
                "API key": str(api_key)
            }
            for key, value in ftrack_cred.items():
                self.log.warning("{}: {}".format(key, value))
            return

        return session

    def _get_ftrack_custom_attrs(self, session, project_name, instance):
        """ Get the extra editorial attrs from Ftrack
        """
        asset = instance.context.data['asset']
        query = session.query(
            "Shot where project.full_name is '{}' "
            "and name is '{}'".format(project_name, asset)
        ).one()

        return query['custom_attributes']

    def _get_otio_attributes(self, instance):
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

        otio_data = {
            "rush_name": rush_name,
            "head_in": head_in,
            "tail_out": tail_out,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "rush_frame_in": rush_frame_in,
            "rush_frame_out": rush_frame_out,
            "record_frame_in": record_frame_in,
            "record_frame_out": record_frame_out,
            "rush_tc_in": rush_tc_in,
            "rush_tc_out": rush_tc_out,
            "record_tc_in": record_tc_in,
            "record_tc_out": record_tc_out,
        }

        return otio_data
