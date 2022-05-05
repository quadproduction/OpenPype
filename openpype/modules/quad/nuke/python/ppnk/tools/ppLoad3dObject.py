#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) Fix Studio, and/or its licensors.
# All rights reserved.
#
# The coded instructions, statements, computer programs, and/or related
# material (collectively the "Data") in these files contain unpublished
# information proprietary to Fix Studio and/or its licensors.
#
# The Data may not be disclosed or distributed to third parties or be
# copied or duplicated, in whole or in part, without the prior written
# consent of Fix Studio.

import os
import nuke


def onDropDataCallback(mimeType, text):
    allowed_extensions = ['.obj', '.fbx', '.abc']

    ext = os.path.splitext(text)[1]

    if not mimeType == 'text/plain' or ext not in allowed_extensions:
        return False
    else:
        read_geo = nuke.createNode("ReadGeo")
        read_geo.knob("file").setValue(text)

        return True
