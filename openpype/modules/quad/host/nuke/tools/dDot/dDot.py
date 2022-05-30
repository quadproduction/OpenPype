#################################################################################################
#                                           dotToConnect                                        #
#################################################################################################

import nuke
import re

fontSize = 33
tileColor = 0
X_OFFSET = 34
Y_OFFSET = 50

def dDotParent():

    parentName = nuke.getInput('ParentName','')
    parentKnob = nuke.Text_Knob('parent', 'parent')

    if parentName == None:
        return False

    if parentName == '':
        nuke.message('No parent name given.')
        return False

    if nuke.Root().selectedNode() == None:
        nuke.message('Error:Nothing is selected.')

    elif len(nuke.selectedNodes()) > 1:
        nuke.message('Error:Multiple nodes selected')

    elif nuke.selectedNode().Class() == 'Dot':
        if nuke.selectedNode().knob('child'):
            nuke.message("Error:It's a child.")
        else:
                nuke.selectedNode().knob('label').setValue('[value name]')
                nuke.selectedNode().knob('name').setValue(parentName)
                nuke.selectedNode().knob('tile_color').setValue(tileColor)
                nuke.selectedNode().knob('note_font_size').setValue(fontSize)
                if nuke.selectedNode().knob('parent'):
                    pass
                else:
                    nuke.selectedNode().addKnob(parentKnob)

    else:
        newDot = nuke.createNode('Dot')
        newDot.knob('label').setValue('[value name]')
        newDot.knob('name').setValue(parentName)
        newDot.knob('tile_color').setValue(tileColor)
        newDot.knob('note_font_size').setValue(fontSize)
        newDot.addKnob(parentKnob)

def dDotConnect():
    dotList = []
    for node in nuke.allNodes('Dot'):
        if node.knob('parent'):
            dotList.append(node.name())

    dotList.sort()
    p = nuke.Panel('Parent Dot List')
    p.addEnumerationPulldown('Parent',' '.join(dotList))
    ret = p.show()
    if p.value('Parent') != None:
        selectedParent = p.value('Parent')
    else:
        return False
    parent = nuke.toNode(selectedParent)
    selectedNodes = nuke.selectedNodes()
    childKnob = nuke.Text_Knob('child', 'child')

    if len( selectedNodes ) !=0:
        for n in selectedNodes:
            if  n.knob('parent'):
                pass
            elif n.Class() != 'Dot':
                pass
            else:
                n.connectInput(0, parent)
                n.knob('label').setValue(selectedParent)
                n.knob('tile_color').setValue(tileColor)
                n.knob('hide_input').setValue(True)
                n.knob('note_font').setValue('italic')
                n.knob('note_font_size').setValue(fontSize)
                parentColor = n.input(0).knob('note_font_color').getValue()
                parentColor = int(parentColor)
                n.knob('note_font_color').setValue(parentColor)
                childKnob = nuke.Text_Knob('child', 'child')
                if n.knob('child'):
                    pass
                elif n.knob('parent'):
                    pass
                elif n.Class() != 'Dot':
                    pass
                else:
                    n.addKnob(childKnob)
    else:
        nuke.createNode("Dot").connectInput(0, parent)
        nuke.selectedNode().knob('label').setValue(selectedParent)
        nuke.selectedNode().knob('tile_color').setValue(tileColor)
        nuke.selectedNode().knob('hide_input').setValue(True)
        nuke.selectedNode().knob('note_font').setValue('italic')
        nuke.selectedNode().knob('note_font_size').setValue(fontSize)
        nuke.selectedNode().addKnob(childKnob)
        parentColor = nuke.selectedNode().input(0).knob('note_font_color').getValue()
        parentColor = int(parentColor)
        nuke.selectedNode().knob('note_font_color').setValue(parentColor)

def dDotConnectSelected():
    selectedNodes = nuke.selectedNodes()
    parent = selectedNodes[0]
    children = selectedNodes[1:]
    parentName = selectedNodes[0]['name'].getValue()

    for n in children:
        if  n.knob('parent'):
            pass
        elif n.Class() != 'Dot':
            pass
        else:
            n.connectInput(0, parent)
            n.knob('label').setValue(parentName)
            n.knob('tile_color').setValue(tileColor)
            n.knob('hide_input').setValue(True)
            n.knob('note_font').setValue('italic')
            n.knob('note_font_size').setValue(fontSize)
            parentColor = n.input(0).knob('note_font_color').getValue()
            parentColor = int(parentColor)
            n.knob('note_font_color').setValue(parentColor)
        if n.knob('child'):
            pass
        elif n.knob('parent'):
            pass
        elif n.Class() != 'Dot':
            pass
        else:
            childKnob = nuke.Text_Knob('child', 'child')
            n.addKnob(childKnob)

def dDotCheckInput():
    brokenConnections = []
    for d in nuke.allNodes('Dot'):
        if d.input(0) == None:
            d['tile_color'].setValue(4278190335)
            brokenConnections.append(d.knob('name').getValue())
        else:
            if d.knob('child'):
                childLabel = d.knob('label').getValue()
                parentName = d.input(0).knob('name').getValue()
                if childLabel == parentName:
                    d['tile_color'].setValue(0)
                else:
                    d['tile_color'].setValue(4278190335)
                    brokenConnections.append(d.knob('name').getValue())
            else:
                d['tile_color'].setValue(0)
    if len(brokenConnections) > 0:
        brokenConnections.sort()
        nuke.message('%s connection(s) broken: \n %s' % (len(brokenConnections), brokenConnections))

def dDotAutoConnect():

    for d in nuke.selectedNodes('Dot'):
        if d.knob('child'):
            childLabel = d.knob('label').getValue()
            parent = nuke.toNode(childLabel)
            try:
                parentColor = parent.knob('note_font_color').getValue()
                parentColor = int(parentColor)
            except:
                parentColor = 4278190335
            if d.input(0) == None:
                d.connectInput(0, parent)
                d['tile_color'].setValue(0)
                d.knob('note_font_size').setValue(fontSize)
                d.knob('note_font_color').setValue(parentColor)
            else:
                parentName = d.input(0).knob('name').getValue()
                if childLabel != parentName:
                    d.connectInput(0, parent)
                    d['tile_color'].setValue(0)
                    d.knob('note_font_size').setValue(fontSize)
                    d.knob('note_font_color').setValue(parentColor)
    dDotCheckInput()

def dDotShowChildren():

    selectedNode = nuke.selectedNode()
    dependentNodes = selectedNode.dependent()
    selectedNode.setSelected(False)
    for depnd in dependentNodes:
        depnd.setSelected(True)

def dDotToggleConnectionsVisibility():
    selectedNode = nuke.selectedNode()
    dependentNodes = selectedNode.dependent()
    for depnd in dependentNodes:
        currentState = depnd.knob('hide_input').getValue()
        depnd.knob('hide_input').setValue(not currentState)

def dDotRollDownNameChange():
     selectedNode = nuke.selectedNode()
     selectedNodeName = selectedNode.knob('name').getValue()
     parentColor = selectedNode.knob('note_font_color').getValue()
     parentColor = int(parentColor)
     if selectedNode.Class() == 'Dot':
        if selectedNode.knob('parent'):
            dependentNodes = selectedNode.dependent()
            for depnd in dependentNodes:
                if depnd.knob('child'):
                    depnd.knob('label').setValue(selectedNodeName)
                    depnd.knob('note_font_color').setValue(parentColor)
            dDotCheckInput()

def dDotGrabParentName():
    for n in nuke.selectedNodes('Dot'):
        if n.knob('child'):
            parentName = n.input(0).knob('name').getValue()
            parentNameNoNumbers = filter(lambda x: x.isalpha(), parentName)
            parentColor = n.input(0).knob('note_font_color').getValue()
            parentColor = int(parentColor)
            childName = n.knob('label').getValue()
            childNameNoNumbers = filter(lambda x: x.isalpha(), childName)
            if childNameNoNumbers.startswith(parentNameNoNumbers):
                n.knob('label').setValue(parentName)
                n.knob('note_font_color').setValue(parentColor)

    dDotCheckInput()

def dDotSelectChildren():
    childName = nuke.getInput('select child nodes labeled:','')
    for n in nuke.allNodes('Dot'):
        if n.knob('child') and n.knob('label'). getValue() == childName:
            n.setSelected(True)


###dDotFromShuffle

def dDotParentShuffle():

    if nuke.Root().selectedNode() is None:
        nuke.message('Error : Nothing is selected.')

    elif nuke.selectedNode().Class() != 'Shuffle':
        nuke.message('Error : You must select a Shuffle node.')

    else:
        count = len(nuke.selectedNodes('Shuffle'))

        row = 5
        if row > count:
            row = count

        errorMsg = ''
        txt = nuke.getInput('Enter prefix', '')

        if txt:
            i = row
            for n in sorted(nuke.selectedNodes('Shuffle'), key=lambda k: k['xpos'].value()):
                xPos = n['xpos'].value()
                yPos = n['ypos'].value()
                channelName = n['in'].value().lower()
                input_name = txt + '_' + channelName
                nodeExists = bool([n for e in nuke.allNodes() if e.name() == input_name])

                if not nodeExists:
                    newDot = nuke.nodes.Dot(xpos=xPos + X_OFFSET, ypos=yPos + ((i + 1) * Y_OFFSET))
                    newDot.knob('label').setValue('[value name]')
                    newDot.knob('name').setValue(input_name)
                    newDot.knob('tile_color').setValue(tileColor)
                    newDot.knob('note_font_size').setValue(fontSize)
                    parent = nuke.Text_Knob('parent', 'parent')
                    newDot.addKnob(parent)
                    newDot.setInput(0, n)
                    i = i - 1

                    if i == 0:
                        i = row

                else:
                    errorMsg = errorMsg + input_name + ', '

            if errorMsg != '':
                nuke.message('Error : ' + errorMsg + ' allready exists.')

def dDotParentRead():

    if nuke.Root().selectedNode() is None:
        nuke.message('Error : Nothing is selected.')

    elif nuke.selectedNode().Class() != 'Read':
        nuke.message('Error : You must select a Read node.')

    else:
        count = len(nuke.selectedNodes('Read'))

        row = 5
        if row > count:
            row = count

        errorMsg = ''
        txt = nuke.getInput('Enter prefix', '')

        if txt:
            i = row
            for n in sorted(nuke.selectedNodes('Read'), key=lambda k: k['xpos'].value()):
                xPos = n['xpos'].value()
                yPos = n['ypos'].value()
                channelName = n['file'].value().rsplit("/").__getitem__(-1)
                input_name = txt + '_' + channelName
                nodeExists = bool([n for e in nuke.allNodes() if e.name() == input_name])

                if not nodeExists:
                    newDot = nuke.nodes.Dot(xpos=xPos + X_OFFSET, ypos=yPos + ((i + 1) * Y_OFFSET))
                    newDot.knob('label').setValue('[value name]')
                    newDot.knob('name').setValue(input_name)
                    newDot.knob('tile_color').setValue(tileColor)
                    newDot.knob('note_font_size').setValue(fontSize)
                    parent = nuke.Text_Knob('parent', 'parent')
                    newDot.addKnob(parent)
                    newDot.setInput(0, n)
                    i = i - 1

                    if i == 0:
                        i = row

                else:
                    errorMsg = errorMsg + input_name + ', '

            if errorMsg != '':
                nuke.message('Error : ' + errorMsg + ' allready exists.')
