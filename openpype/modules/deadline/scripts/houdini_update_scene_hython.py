#
#  /path/to/hython /path/to/script.py -i /path/to/hip.hip
#

from optparse import OptionParser
import os
import hou

def do_the_thing(dependencies):
    # do amazing things here
    for dependency in dependencies: 
        fileNode = hou.node("/obj/AVALON_CONTAINERS/{0}_CON/{0}".format(dependency))

        # get current path from file node
        path = fileNode.parm("file").rawValue()

        currentVersion = path.split("/")[-2]
        versionFolderPath = path.split("/")[:-2]
        versionFolderPath = "/".join(versionFolderPath)
        newVersion = sorted(os.listdir(versionFolderPath))[-1]

        # set New path in file node
        newPath = path.replace(currentVersion, newVersion)
        
        fileNode.parm("file").set(newPath)

if __name__ == "__main__":
    # this gets run when called via the commandline
    # parse commandline arguments here and pass to the main function
    parser = OptionParser()
    parser.add_option("-i", "--hip", dest="hipfile", help="path to .hip file")
    parser.add_option("-d", "--dependencies", dest="dependencies", help="dependencies name list")

    (options, args) = parser.parse_args()
    dependencies = options.dependencies.split(",")
    # load the scene
    hou.hipFile.load(options.hipfile)


    # now do the thing with the scene
    do_the_thing(dependencies)
    hou.hipFile.save(options.hipfile)