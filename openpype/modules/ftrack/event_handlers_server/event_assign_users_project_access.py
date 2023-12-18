from openpype_modules.ftrack.lib import BaseEvent


class AssignUsersProjectAccess(BaseEvent):

    def launch(self, session, event):
        if not event.get("data", None):
            return

        entities_info = event["data"].get("entities", None)
        if not entities_info:
            return

        if entities_info[0].get("entity_type", None) != "Appointment":
            return

        project = self.get_entity_project(session, entities_info[0])
        if not project:
            return

        action_name = entities_info[0].get("action", None)

        if action_name == "add":
            self.add_group_users_to_project_access(session, entities_info[0])
        elif action_name == "remove":
            self.sync_users_to_project_access(session, entities_info[0])

    def add_group_users_to_project_access(self, session, project):
        # Retrieve already present user security roles
        added_user_security_role = [obj["user_security_role"] for obj in project["user_security_role_projects"]]

        # Iterate over all groups and add the users to the project access section
        for allocation in project["allocations"]:
            resource = allocation["resource"]
            if not isinstance(resource, session.types["Group"]):
                continue

            users_dict = {membership["user"]: membership["user"]["user_security_roles"] for membership in
                          resource["memberships"]}

            for user, security_roles in users_dict.items():
                for user_security_role in security_roles:
                    # Do not try to add already added user security roles or roles
                    # with all open projects enabled to avoid exception raised
                    if user_security_role in added_user_security_role or \
                            user_security_role["is_all_open_projects"]:
                        continue

                    try:
                        session.call([{
                            "action": "grant_user_security_role_project",
                            "user_id": user["id"],
                            "role_id": user_security_role["security_role_id"],
                            "project_id": project["id"]
                        }])
                        added_user_security_role.append(user_security_role)
                    except Exception:
                        # The exception will be logged anyway by the session.call method
                        # so encapsulating it will simply avoid this script to crash.
                        pass

    def sync_users_to_project_access(self, session, project):
        # Iterate over all project security roles
        # (info: the "all_open_projects"aren't in this list)
        for obj in project["user_security_role_projects"]:
            user_security_role = obj["user_security_role"]

            try:
                session.call([{
                    "action": "revoke_user_security_role_project",
                    "user_id": user_security_role["user_id"],
                    "role_id": user_security_role["security_role_id"],
                    "project_id": project["id"]
                }])
            except Exception:
                # The exception will be logged anyway by the session.call method
                # so encapsulating it will simply avoid this script to crash.
                pass

        # Now that we removed all user security roles we can add them back,
        # according to the groups specified in the project
        self.add_users_to_project_access(session, project)

    @staticmethod
    def get_entity_project(session, entity_info):
        parents = entity_info.get("parents", None)

        if not parents:
            return None

        # The last parent should be the Project
        project_id = parents[-1]["entityId"]

        if not project_id:
            return
        return session.get("Project", project_id)


def register(session):
    AssignUsersProjectAccess(session).register()
