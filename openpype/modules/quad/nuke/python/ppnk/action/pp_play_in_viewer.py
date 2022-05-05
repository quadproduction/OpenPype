import nuke
import subprocess
import os


def play_selection(play_mode="play", viewer="rv"):
    """
    This function play node like read, write, shotgun_write in a viewer like rv.
    """
    nodes = nuke.selectedNodes()
    if not nodes:
        nuke.message("Can't <b>{play_mode}</b>.<br>- Please Select a Node.".format(play_mode=play_mode.title()))
        return
    play(nodes=nodes, play_mode=play_mode, viewer=viewer)


def play(nodes=[], play_mode="play", viewer="rv"):
    """
    This function play node like read, write, shotgun_write in a viewer like rv.
    :param nodes: node list of name or nuke node.nuke
    :type nodes: str o nuke node
    :param play_mode: "play", "compare", "push"
    :type play_mode: str
    :param viewer: viewer name only rv supported
    :type viewer: str:
    :returns: return a boolean
    :rtype: bool
    """
    # viewer definition
    viewers = {
        "rv_play": ["pp-launch-rv", "-l", "-play"],
        "rv_compare": ["pp-launch-rv", "-l", "-play", "-layout", "row", "-comp", "tile", "-view", "defaultLayout"],
        # use env var PP_SHOT in rv tag name to ensure this rv session is linked to the current nuke
        "rv_push": ["pp-launch-rvpush", "-tag", "nukerv{0}".format(os.environ.get("PP_SHOT")), "merge"]
    }

    cmd = []
    # add viewer software path
    if "{0}_{1}".format(viewer, play_mode) in viewers.keys():
        cmd.extend(viewers.get("{0}_{1}".format(viewer, play_mode)))
    # fps
    fps = nuke.knob('root.fps')
    supported_nodes = []
    unsupported_nodes = []
    supported_nodes_list = ["Read", "Write", "WriteTank"]
    for node in nodes:
        n = node
        if isinstance(node, str):
            # get node
            n = nuke.toNode(node)
        # case Read
        if n.Class() in supported_nodes_list:
            supported_nodes.append(n)
        else:
            unsupported_nodes.append(n)

    if unsupported_nodes:
        txt = "Can't <b>{play_mode}.</b><br>".format(play_mode=play_mode.title())
        txt += "The following nodes are not supported :<br>".format(play_mode=play_mode.title())
        for un in unsupported_nodes:
            txt += "- {node_name} : {node_class}<br>".format(node_class=n.Class(), node_name=n.name())
        txt += "<hr>".format(play_mode=play_mode.title())
        txt += "The supported nodes are :<br>".format(play_mode=play_mode.title())
        for sn in supported_nodes_list:
            txt += "- {node_class}<br>".format(node_class=sn)
        nuke.message(txt)
        if not supported_nodes:
            return

    if supported_nodes:
        # get path and frame
        for n in supported_nodes:
            # case Read
            if n.Class() == "Read":
                path = n.knob("file").value()
                # get frame range
                start = n.knob("first").value()
                end = n.knob("last").value()
                # append command
                img = ['[', path, '-in', str(start), '-out', str(end), '-fps', str(fps), ']']
                cmd.extend(img)

            if n.Class() == "Write":
                path = n.knob("file").value()
                # append command
                img = ['[', path, '-fps', str(fps), ']']
                cmd.extend(img)

            if n.Class() == "WriteTank":
                path = n.knob("cached_path").value()
                # append command
                img = ['[', path, '-fps', str(fps), ']']
                cmd.extend(img)

        # launch
        print(" ".join(cmd))
        subprocess.Popen(cmd)
        return True
