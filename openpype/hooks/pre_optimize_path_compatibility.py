from openpype.lib.applications import PreLaunchHook, LaunchTypes
from openpype.lib import optimize_path_compatibility


class WindowsPathOptimizer(PreLaunchHook):
    """
    PreLaunchHook to optimize environment paths for Windows.

    This class modifies the environment variables in the launch context to
    ensure that all paths are compatible with Windows systems.

    """
    order = 1001
    platforms = {"windows"}
    launch_types = {LaunchTypes.local}

    def execute(self, *args, **kwargs):
        """ Optimize environment paths in the launch context. """
        optimized_env = {}

        # Iterate through each environment variable
        for env_key, env_value in self.launch_context.env.items():
            # Check if the environment variable contains multiple paths (separated by ;)
            if ";" in env_value:
                paths = env_value.split(";")
                optimized_paths = [optimize_path_compatibility(path) for path in paths]
                optimized_env[env_key] = ";".join(optimized_paths)
            else:
                # Optimize the single path
                optimized_env[env_key] = optimize_path_compatibility(env_value)

        # Update the launch context with the optimized environment
        self.launch_context.kwargs['env'] = optimized_env
