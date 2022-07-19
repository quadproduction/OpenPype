import hiero.core
import hiero.ui

def run():
    sequence = hiero.ui.activeSequence()
    try:
        clips_bin = sequence.project().clipsBin()
    except Exception:
        return

    try:
        fixed_bin = clips_bin['fixed']
    except IndexError:
        fixed_bin = clips_bin.addItem(hiero.core.Bin('fixed'))

    for track in sequence.items():
        for item in track.items():
            if item.isMediaPresent():
                try:
                    temp = item.source().project().name()
                except Exception:
                    fixed_bin.addItem(hiero.core.BinItem(item.source()))
