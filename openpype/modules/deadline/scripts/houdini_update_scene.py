## Update loaded asset to lastest  between dependent job
#  or only asset link to dependencie graph
import re
from System.IO import *
from Deadline.Scripting import *
import sys, os

def __main__(*args):
    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()

    dependencies = job.JobExtraInfo0
    hip = deadlinePlugin.GetPluginInfoEntry("SceneFile")
    

    hython = "/prod/softprod/apps/houdini/19.5.435/linux/bin/hython"
    script = "/users_roaming/elambert/openpype/OpenPype/openpype/modules/deadline/scripts/houdini_update_scene_hython.py"

    hython_cmd = "{hython} {script} -i {hipfile} -d {dependencies}".format(hython= hython, script= script, hipfile= hip, dependencies= dependencies)
    deadlinePlugin.LogInfo("Hython commande :   {}".format(hython_cmd))
    
    os.system(hython_cmd)



    #!/usr/bin/python
    def enableHouModule():
        '''Set up the environment so that "import hou" works.'''
        import sys, os

        # Importing hou will load Houdini's libraries and initialize Houdini.
        # This will cause Houdini to load any HDK extensions written in C++.p
        # These extensions need to link against Houdini's libraries,
        # so the symbols from Houdini's libraries must be visible to other
        # libraries that Houdini loads.  To make the symbols visible, we add the
        # RTLD_GLOBAL dlopen flag.
        if hasattr(sys, "setdlopenflags"):
            old_dlopen_flags = sys.getdlopenflags()
            sys.setdlopenflags(old_dlopen_flags | os.RTLD_GLOBAL)

        # For Windows only.
        # Add %HFS%/bin to the DLL search path so that Python can locate
        # the hou module's Houdini library dependencies.  Note that 
        # os.add_dll_directory() does not exist in older Python versions.
        # Python 3.7 users are expected to add %HFS%/bin to the PATH environment
        # variable instead prior to launching Python.
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            os.add_dll_directory("{}/bin".format(os.environ["HFS"]))
        os.environ["HHP"] = "/prod/softprod/apps/houdini/19.5.435/linux/houdini/python2.7libs"
        try:
            import hou
        except ImportError:
            # If the hou module could not be imported, then add 
            # $HFS/houdini/pythonX.Ylibs to sys.path so Python can locate the
            # hou module.
            sys.path.append(os.environ["HHP"])
            import hou
        finally:
            # Reset dlopen flags back to their original value.
            if hasattr(sys, "setdlopenflags"):
                sys.setdlopenflags(old_dlopen_flags)

    #enableHouModule()
    #import hou

    


