import nuke

def run():
    task = nuke.ProgressTask("TimeOffset on Read")

    all_reads = nuke.allNodes('Read')
    number_nodes = len(all_reads)
    comp_first_frame = nuke.root().firstFrame()

    for index, read in enumerate(all_reads):

        task.setMessage(read.name())
        if task.isCancelled():
            break

        read_first_frame = read['first'].value()
        delta = comp_first_frame - read_first_frame

        if delta == 0:
            continue

        current_node = nuke.toNode(read.name())
        current_node.setSelected(True)

        time_offset = nuke.createNode('TimeOffset', inpanel=False)
        time_offset['time_offset'].setValue(delta)

        time_offset.setSelected(False)
        task.setProgress(int((index - 0) * (100 - 0) / (number_nodes - 0) + 0))