from fastapi import Response, status


class MusterModuleRestApi:
    def __init__(self, user_module, server_manager):
        self.module = user_module
        self.server_manager = server_manager

        self.prefix = "/muster"

        self.register()

    def register(self):
        self.server_manager.add_route(
            "GET",
            self.prefix + "/show_login",
            self.show_login_widget
        )

    async def show_login_widget(self, request):
        self.module.action_show_login.trigger()
        return Response(status_code=status.HTTP_200_OK)
