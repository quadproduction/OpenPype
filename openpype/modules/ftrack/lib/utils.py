import ftrack_api


def get_ftrack_statuses(project_name):
    session = ftrack_api.Session(auto_connect_event_hub=False)
    statuses_name = []

    project_entity = session.query((
        "select project_schema from Project where full_name is \"{}\""
    ).format(project_name)).one()
    project_schema = project_entity["project_schema"]
    task_type_ids = {
        task_type["id"]
        for task_type in session.query("select id from Type").all()
    }
    statuses = project_schema.get_statuses("Task", task_type_ids)
    for status in statuses:
        statuses_name.append(status["name"])

    return statuses
