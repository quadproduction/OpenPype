import os
import shutil


def copy_workspace_mel(workdir):
    # Check that source mel exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_filepath = os.path.join(current_dir, "resources", "workspace.mel")
    if not os.path.exists(src_filepath):
        print("Source mel file does not exist. {}".format(src_filepath))
        return

    # Skip if workspace.mel already exists
    dst_filepath = os.path.join(workdir, "workspace.mel")
    if os.path.exists(dst_filepath):
        return

    # Create workdir if does not exists yet
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    # Copy file
    print("Copying workspace mel \"{}\" -> \"{}\"".format(
        src_filepath, dst_filepath
    ))
    shutil.copy(src_filepath, dst_filepath)
