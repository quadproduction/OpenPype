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
import glob
import time
import nuke


def onAutoSave(filename):
    if nuke.root().name() == 'Root':
        return filename

    fileNo = 0
    files = getAutoSaveFiles(filename)

    if len(files) > 0:
        lastFile = files[-1]

        if len(lastFile) > 0:
            try:
                fileNo = int(lastFile[-1:])
            except ValueError:
                pass

            fileNo = fileNo + 1

    if (fileNo > 9):
        fileNo = 0

    if (fileNo != 0):
        filename = filename + str(fileNo)

    return filename


def onAutoSaveRestore(filename):
    files = getAutoSaveFiles(filename)
    if len(files) > 0:
        filename = files[-1]
    return filename


def onAutoSaveDelete(filename):
    if nuke.root().name() == 'Root':
        return filename
    # return None here to not delete auto save file
    return None


def getAutoSaveFiles(filename):
    date_file_list = []
    files = glob.glob(filename + '[1-9]')
    files.extend(glob.glob(filename))

    for file in files:
        stats = os.stat(file)
        lastmod_date = time.localtime(stats[8])
        date_file_tuple = lastmod_date, file
        date_file_list.append(date_file_tuple)

    date_file_list.sort()

    return [f for _, f in date_file_list]


# nuke.addAutoSaveFilter(onAutoSave)
# nuke.addAutoSaveRestoreFilter(onAutoSaveRestore)
# nuke.addAutoSaveDeleteFilter(onAutoSaveDelete)
