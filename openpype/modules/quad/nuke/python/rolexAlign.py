import nuke


def align():
    # THIS FUNCTION ALIGNS THE NODES VERTICALLY
    nodeList = []
    for node in nuke.selectedNodes():
        if node.Class() == 'Read':
            fileKnob = (node['file'].value())
            render = fileKnob.split('/')[-1]
            nodeList.append((node, render))
        else:
            pass

    nodeList.sort(key=lambda x: x[1])

    n = len(nodeList)
    x = 0
    y = 0

    # SET AVERAGE XPOS AND YPOS VALUE
    for i in nodeList:
        x += i[0]['xpos'].value()
        y += i[0]['ypos'].value()
    x = x / n
    spacing = 150
    y = y / n - spacing * n / 2

    # MOVE NODES
    for i in nodeList:
        i[0]['xpos'].setValue(x)
        i[0]['ypos'].setValue(y)
        y += spacing
