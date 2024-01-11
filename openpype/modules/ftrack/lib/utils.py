import ftrack_api


def get_ftrack_statuses():
    session = ftrack_api.Session(auto_connect_event_hub=False)
    statuses = session.query("Status").all()
    statuses = [status["name"] for status in statuses]

    return sorted(statuses)
