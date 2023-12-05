from pymongo import UpdateOne

from openpype.client import get_projects
from openpype.pipeline import AvalonMongoDB
from openpype_modules.ftrack.lib import BaseAction, statics_icon


class HideDeletedProjects(BaseAction):
    """Hide projects on OP that no longer exsist in Ftrack
    or have no FtrackId
    """

    identifier = "hide.deleted.projects"
    show_identifier = "hide.deleted.projects"
    label = "OpenPype Admin"
    variant = "- Hide deleted projects"
    description = "Hide deleted projects from Ftrack in OP"
    icon = statics_icon("ftrack", "action_icons", "DeleteAsset.svg")

    def __init__(self, session):
        self.dbcon = AvalonMongoDB()
        super().__init__(session)

    def _discover(self, _event):
        return {
            "items": [{
                "label": self.label,
                "variant": self.variant,
                "description": self.description,
                "actionIdentifier": self.discover_identifier,
                "icon": self.icon,
            }]
        }

    def _launch(self, event):
        self.trigger_action(self.show_identifier, event)

    def register(self):
        # Register default action callbacks
        super(HideDeletedProjects, self).register()

        # # Add show identifier
        show_subscription = (
            "topic=ftrack.action.launch"
            " and data.actionIdentifier={}"
            " and source.user.username={}"
        ).format(
            self.show_identifier,
            self.session.api_user
        )
        self.session.event_hub.subscribe(
            show_subscription,
            self.hide_deleted_projects
        )

    def hide_deleted_projects(self, event):
        ftrack_projects = self.session.query("Project").all()
        ftrack_projects_ids = [project["id"] for project in ftrack_projects]
        mongo_projects = get_projects()

        projects_to_hide = []
        for project in mongo_projects:
            if "ftrackId" not in project["data"].keys():
                projects_to_hide.append(project)
            elif project["data"]["ftrackId"] not in ftrack_projects_ids:
                projects_to_hide.append(project)

        for project in projects_to_hide:
            filter = {"_id": project["_id"]}
            change_data = {"$set": {"data.active": False}}
            self.dbcon.Session["AVALON_PROJECT"] = project["name"]
            self.dbcon.bulk_write([UpdateOne(filter, change_data)])
            self.log.debug(f"No FtrackId for project {project['name']}"
                           " or project deleted from Ftrack."
                           " Project hidden.")


def register(session):
    HideDeletedProjects(session).register()
