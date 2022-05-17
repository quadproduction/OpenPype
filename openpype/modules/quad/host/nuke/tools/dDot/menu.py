import nuke
import re
import dDot

class dDotPanel( nukescripts.PythonPanel ):
    def __init__( self ):
        nukescripts.PythonPanel.__init__( self, 'dDot Master', 'dDot.dDotPanel')

        # CREATE KNOBS

        self.createText = nuke.Text_Knob('createText', 'CREATE DOTS')
        self.readDot = nuke.PyScript_Knob('readDot', 'create Dots from Read')
        self.shuffleDot = nuke.PyScript_Knob('shuffleDot', 'create Dots from Shuffle')
        self.simpleDot = nuke.PyScript_Knob('simpleDot', 'create simple Dot')

        self.renameText = nuke.Text_Knob('renameText', 'RENAME DOTS')
        self.target = nuke.Enumeration_Knob( 'target', 'Target:', ['Parent', 'Child'])
        self.searchStr = nuke.String_Knob('searchStr', 'Search for:')
        self.searchStr.setTooltip( 'The text to search for' )
        self.clearSearch = nuke.PyScript_Knob('clearSearch', 'Clear')
        self.replaceStr = nuke.String_Knob('replaceStr', 'Replace with:')
        self.replaceStr.setTooltip( 'Text to replace the found text with' )
        self.clearReplace = nuke.PyScript_Knob('clearReplace', 'Clear')
        self.executeRename = nuke.PyScript_Knob('rename', 'Rename !')
        self.executeRename.setFlag( nuke.STARTLINE )

        # ADD KNOBS
        for k in ( self.createText, self.readDot, self.shuffleDot, self.simpleDot, self.renameText, self.target, self.searchStr, self.clearSearch, self.replaceStr, self.clearReplace, self.executeRename):
            self.addKnob( k )

    def dDotRename( self ):
        oldName = self.searchStr.value()
        newName = self.replaceStr.value()
        targetDot = self.target.value()
        for n in nuke.selectedNodes('Dot'):
            if targetDot == 'Parent':
                knob = n['name']
            else:
                knob = n['label']
            old_value = knob.value()
            knob.setValue(old_value.replace(oldName, newName))

    def dDotClearSearch( self ):
        self.searchStr.setValue('')

    def dDotClearReplace( self ):
        self.replaceStr.setValue('')

    # KNOB CHANGED
    def knobChanged ( self, knob ):
        if knob == self.readDot:
            dDot.dDotParentRead()
        elif knob == self.shuffleDot:
            dDot.dDotParentShuffle()
        elif knob == self.simpleDot:
            dDot.dDotParent()
        elif knob == self.clearSearch:
            self.dDotClearSearch()
        elif knob == self.clearReplace:
            self.dDotClearReplace()
        elif knob == self.executeRename:
            self.dDotRename()


def addPanel():
    return dDotPanel().addToPane()

menu = nuke.menu('Pane')
menu.addCommand('dDot Master', addPanel )
nukescripts.registerPanel( 'dDot.dDotPanel', addPanel )

#MENU dDot
toolbar = nuke.toolbar("Nodes")
menu_dDot = toolbar.addMenu('dDot', 'dDot.png')
menu_dDot.addCommand("dDotParent", "dDot.dDotParent()", "shift+p")
menu_dDot.addCommand("dDotConnect", "dDot.dDotConnect()",  "alt+shift+a")
menu_dDot.addCommand("dDotConnectSelected", "dDot.dDotConnectSelected()", "ctrl+,")
menu_dDot.addCommand("dDotCheckInput", "dDot.dDotCheckInput()", "ctrl+shift+,")
menu_dDot.addCommand("dDotAutoConnect", "dDot.dDotAutoConnect()", "alt+a")
menu_dDot.addCommand("dDotShowChildren", "dDot.dDotShowChildren()", "alt+,")
menu_dDot.addCommand("dDotToggleConnectionsVisibility", "dDot.dDotToggleConnectionsVisibility()", "alt+.")
menu_dDot.addCommand("dDotRollDownNameChange", "dDot.dDotRollDownNameChange()","alt+shift+,")
menu_dDot.addCommand("dDotGrabParentName", "dDot.dDotGrabParentName()","alt+shift+.")
menu_dDot.addCommand("dDotSelectChildren", "dDot.dDotSelectChildren()")
menu_dDot.addCommand("dDotParentShuffle", "dDot.dDotParentShuffle()", "shift+f")
menu_dDot.addCommand("dDotParentRead", "dDot.dDotParentRead()", "shift+r")

# #ADD in top menu
# m=nuke.menu('Nuke')
# n=m.addMenu('dDot Master')
# n.addCommand('create Dots from Read','dDot.dDotParentRead()')
# n.addCommand('create Dots from Shuffle','dDot.dDotParentShuffle()')
# n.addCommand('create simple Dot','dDot.dDotParent()')
