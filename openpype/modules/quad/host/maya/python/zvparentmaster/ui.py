"""
The MIT License (MIT)

Copyright (c) 2006-2020 Paolo Dominici

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

ZV Parent Master is an animation tool that helps you to animate objects in mutual contact or interaction with ease.

Usage:
import zvparentmaster.ui
zvparentmaster.ui.show()
"""

__author__ = 'Paolo Dominici (paolodominici@gmail.com)'
__version__ = '1.3.4'
__date__ = '2020/04/10'
__copyright__ = 'Copyright (c) 2006-2020 Paolo Dominici'

from maya import cmds
import os
import sys
import math

##########################
# CUSTOMIZABLE CONSTANTS #
##########################

# On the first attachment ZVPM creates two groups above the control and one parent constraint node.
# You can customize their suffixes, just keep in mind your scene won't be compatible with other ZVPMs.
PARENT_HANDLE_SUFFIX = '_PH'
SNAP_GROUP_SUFFIX = '_SN'
PARENT_CONSTRAINT_SUFFIX = '_PC'

# If this constant is True ZVPM will not include the control suffix on ZVPM object names
# i.e. the snap group of leftfoot_CTRL will be named leftfoot_SN instead of leftfoot_CTRL_SN.
REMOVE_CONTROL_SUFFIX = False

# This constant is used only if REMOVE_CONTROL_SUFFIX = True.
CONTROL_SUFFIX = '_CTRL'

# The hierarchy of a referenced file is read-only so ZVPM cannot create its parent groups.
# However the root of a referenced file can be grouped, so you can use ZVPM on it.
# Set this constant to False in case you don't want a ref file root object to be used with ZVPM.
ALLOW_REFERENCE_ROOT = True


# Private constants
_default_size = (44, 208)
_loc_sfx = '_TMPLOC'
_time_win_sfx = '_WIN'
_time_form_div = 10000
_time_form_sfx = '_TMFRM'
_label_sfx = ['_TMLB', '_ATLB']
_timeline_hsv_colors = [(55.0, 1.0, 1.0),
                        (135.0, 1.0, 1.0),
                        (190.0, 1.0, 1.0),
                        (218.0, 0.85, 1.0),
                        (276.0, 0.67, 1.0),
                        (314.0, 0.65, 1.0),
                        (0.0, 1.0, 1.0),
                        (32.0, 0.8, 1.0),
                        (32.0, 0.8, 0.75),
                        (345.0, 1.0, 0.46)]

# icons path
_icons_path = os.path.join(os.path.dirname(__file__), 'icons')


def cb(method, *args):
    """Easy-call UI callback method."""

    return lambda *x: method(*args)


def _get_obj_name(obj):
    """Restituisce il nome pulito senza percorso o namespace."""

    idx = max(obj.rfind('|'), obj.rfind(':'))
    return obj[idx+1:]


def _get_obj_name_from_snap_group(sn_grp):
    """Restituisce il nome del controllo dallo snap group."""

    if sn_grp.endswith(SNAP_GROUP_SUFFIX):
        name = sn_grp[:-len(SNAP_GROUP_SUFFIX)]
        if REMOVE_CONTROL_SUFFIX and cmds.ls(name + CONTROL_SUFFIX):
            name += CONTROL_SUFFIX
        return name
    return None


def _get_parent_handle(obj):
    """Restituisce il nome del parent handle."""

    if REMOVE_CONTROL_SUFFIX and obj.endswith(CONTROL_SUFFIX):
        obj = obj[:-len(CONTROL_SUFFIX)]

    return obj + PARENT_HANDLE_SUFFIX


def _get_snap_group(obj):
    """Restituisce il nome dello snap group."""

    if REMOVE_CONTROL_SUFFIX and obj.endswith(CONTROL_SUFFIX):
        obj = obj[:-len(CONTROL_SUFFIX)]

    return obj + SNAP_GROUP_SUFFIX


def _get_parent_constraint(obj):
    """Nome del parent constraint."""

    if REMOVE_CONTROL_SUFFIX:
        return _get_parent_handle(obj.replace(':', '_')) + PARENT_CONSTRAINT_SUFFIX
    else:
        return _get_parent_handle(obj) + PARENT_CONSTRAINT_SUFFIX


def _get_world_location(obj):
    """Restituisce due array: posizione e rotazione assoluta."""

    return [cmds.xform(obj, q=True, rp=True, ws=True), cmds.xform(obj, q=True, ro=True, ws=True)]


def _set_world_location(obj, pos_rot):
    """Setta posizione e rotazione secondo gli array specificati."""

    pos = pos_rot[0]
    rot = pos_rot[1]
    obj_piv = cmds.xform(obj, q=True, rp=True, ws=True)
    diff = (pos[0] - obj_piv[0], pos[1] - obj_piv[1], pos[2] - obj_piv[2])
    cmds.xform(obj, t=diff, r=True, ws=True)
    cmds.xform(obj, ro=rot, a=True, ws=True)


def _get_active_attach_target(constr_name):
    """Restituisce il target attivo (quello con peso 1) per il constrain specificato."""

    targets = cmds.parentConstraint(constr_name, q=True, tl=True)
    active_target = None
    for i, target in enumerate(targets):
        if cmds.getAttr('%s.w%d' % (constr_name, i)) == 1.0:
            active_target = target
            break
    return active_target


def _clean_curves(anim_curves):
    """Pulisce le curve rimuovendo le chiavi superflue."""

    tol = 0.0001
    for c in anim_curves:
        key_count = cmds.keyframe(c, query=True, keyframeCount=True)
        if key_count == 0:
            continue
        # cancella le chiavi superflue intermedie
        if key_count > 2:
            times = cmds.keyframe(c, query=True, index=(0, key_count-1), timeChange=True)
            values = cmds.keyframe(c, query=True, index=(0, key_count-1), valueChange=True)
            in_tan = cmds.keyTangent(c, query=True, index=(0, key_count-1), inAngle=True)
            out_tan = cmds.keyTangent(c, query=True, index=(0, key_count-1), outAngle=True)
            for i in range(1, key_count-1):
                if math.fabs(values[i]-values[i-1]) < tol and math.fabs(values[i+1]-values[i]) < tol \
                        and math.fabs(in_tan[i]-out_tan[i-1]) < tol and math.fabs(in_tan[i+1]-out_tan[i]) < tol:
                    cmds.cutKey(c, time=(times[i], times[i]))

        # ricalcola il numero di chiavi e pulisce le chiavi agli estremi
        key_count = cmds.keyframe(c, query=True, keyframeCount=True)
        times = cmds.keyframe(c, query=True, index=(0, key_count-1), timeChange=True)
        values = cmds.keyframe(c, query=True, index=(0, key_count-1), valueChange=True)
        in_tan = cmds.keyTangent(c, query=True, index=(0, key_count-1), inAngle=True)
        out_tan = cmds.keyTangent(c, query=True, index=(0, key_count-1), outAngle=True)
        # piu' di due key rimanenti
        if key_count > 2:
            if math.fabs(values[1]-values[0]) < tol and math.fabs(in_tan[1]-out_tan[0]) < tol:
                cmds.cutKey(c, time=(times[0], times[0]))
            if math.fabs(values[-1]-values[-2]) < tol and math.fabs(in_tan[-1]-out_tan[-2]) < tol:
                cmds.cutKey(c, time=(times[-1], times[-1]))
        # uno o due key rimanenti
        elif key_count == 1 or (math.fabs(values[1]-values[0]) < tol and math.fabs(in_tan[1]-out_tan[0]) < tol):
            val = cmds.getAttr(c)		# debuggato
            cmds.cutKey(c)
            cmds.setAttr(c, val)


def _print_parents(constr_names):
    """Printa gli attuali parenti."""

    sys.stdout.write('[%s]\n' % ', '.join([str(_get_active_attach_target(s)) for s in constr_names]))


def _set_root_namespace():
    if cmds.namespaceInfo(cur=True) != ':':
        cmds.namespace(set=':')


def _get_ctrls_from_selection(postfix):
    """Validate selection, deve esistere un nodo con lo stesso nome + il postfix."""

    # carica la selezione
    sel = cmds.ls(sl=True)
    ctrls = []
    # aggiungi i controlli con parent constraint alla lista
    for ctrl in sel:
        tmp_ctrl = ctrl
        # se l'oggetto e' uno snapgroup restituisci il figlio
        ctrl_from_sn_grp = _get_obj_name_from_snap_group(ctrl)
        if ctrl_from_sn_grp:
            tmp_ctrl = ctrl_from_sn_grp

        if postfix == PARENT_HANDLE_SUFFIX:
            temp = _get_parent_handle(tmp_ctrl)
        elif postfix == SNAP_GROUP_SUFFIX:
            temp = _get_snap_group(tmp_ctrl)
        elif postfix == PARENT_CONSTRAINT_SUFFIX:
            temp = _get_parent_constraint(tmp_ctrl)
        else:
            temp = tmp_ctrl

        temp = cmds.ls(temp)

        # se non presente nella lista aggiungilo
        if temp and tmp_ctrl not in ctrls:
            ctrls.append(tmp_ctrl)

    return sel, ctrls


def _get_rigid_body(obj):
    """Restituisce il nodo di rigidBody."""

    try:
        return cmds.rigidBody(obj, q=True, n=True)
    except:
        return None


def _set_rigid_body_state(rb, val):
    """Se esiste ricava il nodo rigidBody e lo setta attivo o passivo."""

    cmds.setAttr(rb + '.active', val)
    cmds.setKeyframe(rb + '.active')
    cmds.keyframe(rb + '.active', tds=True)


def _rb_detach(obj):
    """Quando detacho diventa attivo."""

    rb = _get_rigid_body(obj)
    if rb:
        _set_rigid_body_state(rb, 1)


def _rb_attach(obj):
    """Quando attacho setto il rb passivo e setto le chiavi per la sua nuova posizione."""

    rb = _get_rigid_body(obj)
    if rb:
        w_loc = _get_world_location(obj)
        _set_rigid_body_state(rb, 0)
        _set_world_location(obj, w_loc)
        _set_world_location(obj, w_loc)
        cmds.setKeyframe(obj, at=['translate', 'rotate'], ott='step')

        # cerca le curve d'animazione
        choices = cmds.listConnections(obj, s=True, d=False, t='choice')
        anim_curves = cmds.listConnections(choices, s=True, d=False, t='animCurve')
        # setta le curve step
        cmds.keyTangent(anim_curves, ott='step')


def _reset_rigid_body(obj):
    """Cancella le chiavi messe al rigid body."""

    rb = _get_rigid_body(obj)
    if rb:
        # cancella le chiavi attivo-passivo
        cmds.cutKey(rb, cl=True, at='act')
        cmds.setAttr(rb + '.act', 1)
        # cancella le chiavi di posizione per lo stato passivo
        try:
            choices = cmds.listConnections(obj, d=False, s=True, t='choice')
            anim_curves = [cmds.listConnections(s + '.input[1]', d=False, s=True)[0] for s in choices]
            cmds.delete(anim_curves)
        except:
            pass


def _create_parent_master(obj, translation=True, rotation=True):
    """Crea i gruppi necessari per utilizzare il parent master."""

    # creo il parent handle e lo snap group dell'oggetto (aventi stesso pivot)
    # un file referenziato genera eccezione
    if cmds.referenceQuery(obj, inr=True) and (not ALLOW_REFERENCE_ROOT or cmds.listRelatives(obj, p=True)):
        sys.stdout.write('Read-only hierarchy detected\n')
        msg = 'Are you working with referenced files?\n\n' \
              'ZVPM can\'t group "%s" because it\'s in a read-only hierarchy.\n\n\n' \
              'Do the following:\n\n' \
              '- Open the referenced file.\n' \
              '- Select this object, right-click on "Attach objects" button and "Create parent groups".\n' \
              '- Save the file.' % obj
        cmds.confirmDialog(title='Referenced file - ZV Parent Master', message=msg)
        return False

    # crea gruppi con la matrice del parente e il pivot dell'oggetto
    piv = cmds.xform(obj, q=True, rp=True, ws=True)
    obj_relatives = cmds.listRelatives(obj, p=True, pa=True)
    obj_parent = obj_relatives and obj_relatives[0] or None
    ph = cmds.createNode('transform', p=obj_parent, n=_get_parent_handle(obj))
    sg = cmds.createNode('transform', p=ph, n=_get_snap_group(obj))
    cmds.xform(ph, sg, piv=piv, ws=True)
    cmds.parent(obj, sg)

    # locca gli attributi non diponibili e quelli non richiesti
    ts = {'tx', 'ty', 'tz'}
    rs = {'rx', 'ry', 'rz'}

    avail_attrs = set(cmds.listAttr(obj, k=True, u=True, sn=True) or [])
    attrs_to_lock = (ts | rs) - avail_attrs
    if not translation:
        attrs_to_lock |= ts
    if not rotation:
        attrs_to_lock |= rs

    for attr in attrs_to_lock:
        cmds.setAttr('%s.%s' % (ph, attr), lock=True)

    return True


def _fix_this(ctrl, time_range):
    """Fixa lo snap per questo controllo."""

    constr_name = _get_parent_constraint(ctrl)
    # fixa il timerange corrente
    if time_range:
        current_frame = cmds.currentTime(q=True)
        all_key_times_raw = cmds.keyframe(constr_name, q=True,
                                          time=(cmds.playbackOptions(q=True, min=True),
                                                cmds.playbackOptions(q=True, max=True)),
                                          timeChange=True)
        all_key_times = list(set(all_key_times_raw))
        all_key_times.sort()
        for t in all_key_times:
            cmds.currentTime(t)
            _fix_this(ctrl, False)
        # ritorna al frame di prima
        cmds.currentTime(current_frame)
    # fixa solo il frame corrente
    else:
        # se sono al primo frame o non ci sono keyframe in questo frame esci
        first_frame = cmds.playbackOptions(q=True, ast=True)
        current_frame = cmds.currentTime(q=True)
        if current_frame == first_frame or cmds.keyframe(constr_name, q=True,
                                                         time=(current_frame, current_frame), timeChange=True) is None:
            sys.stdout.write('Nothing to fix at frame %d\n' % current_frame)
            return

        # target attivo
        active_target = _get_active_attach_target(constr_name)

        # elimina le chiavi
        select_constraint_nodes(ctrl)
        cmds.cutKey(t=(current_frame, current_frame))

        # se rigid body rivaluta dal primo frame
        if _get_rigid_body(ctrl):
            # dummy locator (faccio il bake su di lui e lo cancello)
            temp_loc = cmds.spaceLocator()[0]
            cmds.hide(temp_loc)
            # mi permette di riprodurre la simulazione dal primo frame fino a quello corrente
            cmds.bakeResults(temp_loc, at=['t'], sm=True, t=(first_frame, current_frame), dic=True, pok=True)
            cmds.delete(temp_loc)

        # rifai il parent (detach o attach)
        if not active_target:
            cmds.select(ctrl)
            detach()
        else:
            cmds.select([ctrl, active_target])
            attach()

        sys.stdout.write('Snap fixed at frame %d\n' % current_frame)


def _bake_obj(obj):
    """Bake animazione."""

    constr_name = _get_parent_constraint(obj)
    constr_exists = cmds.ls(constr_name)

    # se il constraint non esiste o non contiene keyframe esci
    if not constr_exists or cmds.keyframe(constr_name, q=True, kc=True) == 0:
        sys.stdout.write('Nothing to bake\n')
        return

    # primo frame
    current_frame = cmds.currentTime(q=True)
    first_frame = cmds.playbackOptions(q=True, ast=True)
    cmds.currentTime(first_frame)

    # salva come last_frame l'ultimo frame d'animazione del constraint o dell'oggetto
    key_times = cmds.keyframe(obj, q=True, tc=True)
    if not key_times:
        key_times = cmds.keyframe(constr_name, q=True, tc=True)
    else:
        key_times.extend(cmds.keyframe(constr_name, q=True, tc=True))
    last_frame = max(key_times)

    # se all'ultimo frame rimane attached oppure il corpo e' rigido allora usa animation end time
    if max(cmds.keyframe(constr_name, q=True, ev=True, t=(last_frame, last_frame))) > 0.0 or _get_rigid_body(obj):
        last_frame = max(last_frame, cmds.playbackOptions(q=True, aet=True))

    # crea il locator
    locator_name = obj + _loc_sfx
    _set_root_namespace()
    is_joint = cmds.nodeType(obj) == 'joint'
    if is_joint:
        loc = cmds.createNode('joint', n=locator_name)
    else:
        loc = cmds.spaceLocator(n=locator_name)[0]
    cmds.hide(loc)

    # trova il parent del gruppo PH
    parent = cmds.listRelatives(_get_parent_handle(obj), p=True)
    if parent:
        cmds.parent([loc, parent[0]])

    # copia l'ordine degli assi
    cmds.setAttr('%s.rotateOrder' % loc, cmds.getAttr('%s.rotateOrder' % obj))

    # copia joint orient
    if is_joint:
        cmds.setAttr('%s.jo' % loc, *cmds.getAttr('%s.jo' % obj)[0])

    # copia matrice e pivot
    cmds.xform(loc, m=cmds.xform(obj, q=True, m=True, ws=True), ws=True)
    cmds.xform(loc, piv=cmds.xform(obj, q=True, rp=True, ws=True), ws=True)

    # costringi il locator
    constraint = cmds.parentConstraint(obj, loc, mo=True)[0]

    # fai il bake
    cmds.bakeResults(loc, at=['t', 'r'], sm=True, t=(first_frame, last_frame), dic=True, pok=True)

    # cancella il constraint
    cmds.delete(constraint)

    # ripristina il frame precedente
    cmds.currentTime(current_frame)


def _apply_baked_animation(obj):
    """Connetti l'animazione del bake locator all'oggetto."""

    # se il locator non e' stato creato (niente da bakare) esci
    locator_name = obj + _loc_sfx
    loc_list = cmds.ls(locator_name)
    if not loc_list:
        return
    loc = loc_list[0]

    # se esiste cancella il nodo rigidBody e il solver
    try:
        rb = _get_rigid_body(obj)
        if rb:
            solver = cmds.listConnections(rb + '.generalForce', s=False)[0]
            cmds.delete(rb)
            # se il rigid solver non e' usato cancellalo
            if not cmds.listConnections(solver + '.generalForce', d=False):
                cmds.delete(solver)
    # se il nodo rigidBody e' referenziato allora disconnetti solamente i choice dagli attributi dell'oggetto
    except:
        for choice in cmds.listConnections(obj, d=False, s=True, t='choice'):
            cmds.disconnectAttr(choice + '.output', cmds.listConnections(choice + '.output', p=True)[0])

    # cancella eventuali chiavi nel nodo di trasformazione dell'oggetto
    cmds.cutKey(obj, at=['t', 'r'])

    # trova le curve d'animazione del locator
    anim_curves = cmds.listConnections(loc, d=False, type='animCurve')

    # rinominale
    for animCurve in anim_curves:
        und_idx = animCurve.rindex('_')
        cmds.rename(animCurve, '%s%s' % (obj, animCurve[und_idx:]))

    # connetti le curve d'animazione all'oggetto
    attrs = cmds.listAttr([obj + '.t', obj + '.r'], u=True, s=True)
    if not attrs:
        return

    for attr in attrs:
        curve = '%s_%s' % (obj, attr)
        curve_name_attr = '%s.output' % curve
        cmds.connectAttr(curve_name_attr, '%s.%s' % (obj, attr))

        # remove namespace from anim curve
        if ':' in curve:
            cmds.rename(curve, curve[curve.index(':')+1:])

    # pulisci le curve
    sys.stdout.write('Optimizing translation and rotation keys...\n')
    _clean_curves(['%s.%s' % (obj, s) for s in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']])

    # cancella il locator
    cmds.delete(loc)


def _create_parent_constraint(obj, target, constr_name):
    """Crea il parent constraint."""

    ta = ('tx', 'ty', 'tz')
    ra = ('rx', 'ry', 'rz')

    # parent handle
    ph = _get_parent_handle(obj)

    # valuta quali sono gli attributi che non vanno costretti
    avail_attrs = cmds.listAttr(ph, k=True, u=True, sn=True) or []
    skip_translate = [s[1] for s in ta if s not in avail_attrs]
    skip_rotate = [s[1] for s in ra if s not in avail_attrs]

    # se tutte loccate lancia l'errore
    if len(skip_translate) == 3 and len(skip_rotate) == 3:
        raise Exception('The attributes of the selected object are locked')

    # crea il constraint
    _set_root_namespace()
    pc = cmds.parentConstraint(target, ph, mo=False, n=constr_name, w=1, st=skip_translate, sr=skip_rotate)[0]

    # azzera la rest position
    cmds.setAttr('%s.restTranslate' % pc, 0.0, 0.0, 0.0)
    cmds.setAttr('%s.restRotate' % pc, 0.0, 0.0, 0.0)


def _add_target(cns, target):
    """Aggiungi un target al parent constraint."""

    target_list = cmds.parentConstraint(cns, q=True, tl=True)
    count = len(target_list)
    cmds.addAttr(cns, sn='w%d' % count, ln='%sW%d' % (_get_obj_name(target), count),
                 dv=1.0, min=0.0, at='double', k=True)
    cmds.setAttr('%s.w%d' % (cns, count), 0.0)

    cmds.connectAttr('%s.t' % target, '%s.tg[%d].tt' % (cns, count))
    cmds.connectAttr('%s.rp' % target, '%s.tg[%d].trp' % (cns, count))
    cmds.connectAttr('%s.rpt' % target, '%s.tg[%d].trt' % (cns, count))
    cmds.connectAttr('%s.r' % target, '%s.tg[%d].tr' % (cns, count))
    cmds.connectAttr('%s.ro' % target, '%s.tg[%d].tro' % (cns, count))
    cmds.connectAttr('%s.s' % target, '%s.tg[%d].ts' % (cns, count))
    cmds.connectAttr('%s.pm' % target, '%s.tg[%d].tpm' % (cns, count))

    # connetti il peso
    cmds.connectAttr('%s.w%d' % (cns, count), '%s.tg[%d].tw' % (cns, count))


def create_parent_groups(translation=True, rotation=True):
    """Funzione popup per la preparazione dei controlli nel file reference."""

    # carica la selezione
    ctrls = cmds.ls(sl=True)

    # se non ci sono elementi selezionati esci
    if not ctrls:
        raise Exception('You must select one or more objects')

    counter = 0
    for ctrl in ctrls:
        # se l'oggetto non e' provvisto di parent handle e snap group creali
        temp = cmds.ls(_get_parent_handle(ctrl))
        if not temp:
            # se l'oggetto e' referenziato interrompi il ciclo
            if not _create_parent_master(ctrl, translation, rotation):
                return
            counter += 1
    # alla fine riseleziona i controlli
    cmds.select(ctrls)

    # messaggio
    if counter == 1:
        singplur = ''
    else:
        singplur = 's'
    sys.stdout.write('Parent groups created for %d object%s\n' % (len(ctrls), singplur))


def attach():
    """Parent constraint intelligente."""

    # carica la selezione
    sel = cmds.ls(sl=True)

    # nota: ls con filtro transforms non funziona bene (include i constraint)
    sel = [s for s in sel if cmds.nodeType(s) == 'transform' or cmds.nodeType(s) == 'joint']

    ctrls = []
    # elimina gli elementi che hanno un suffisso di ZVPM
    for s in sel:
        tmp = s
        obj_from_sn_grp = _get_obj_name_from_snap_group(s)
        if obj_from_sn_grp:
            tmp = obj_from_sn_grp
        if tmp not in ctrls:
            ctrls.append(tmp)

    # se sono selezionati meno di due elementi esci
    if len(ctrls) < 2:
        raise Exception('You must select one or more slave objects and a master object')

    target = ctrls.pop()

    current_frame = cmds.currentTime(q=True)
    first_frame = cmds.playbackOptions(q=True, ast=True)

    # si inizia!
    for ctrl in ctrls:
        # se l'oggetto non e' provvisto di parent handle e snap group creali
        temp = cmds.ls(_get_parent_handle(ctrl))
        if not temp:
            # se l'oggetto e' referenziato interrompi il ciclo
            if not _create_parent_master(ctrl):
                return

        snap_group = _get_snap_group(ctrl)
        # memorizza la posizione dello snap group per poi fare lo snap sulla stessa
        ctrl_w_loc = _get_world_location(snap_group)
        # nome del constrain
        constr_name = _get_parent_constraint(ctrl)

        temp = cmds.ls(constr_name)
        # se il parent constr esiste
        if temp:
            # se il target e' gia attivo esci
            if target == _get_active_attach_target(constr_name):
                continue

            target_list = cmds.parentConstraint(constr_name, q=True, tl=True)
            # azzera tutti i target
            for i, tt in enumerate(target_list):
                cmds.setAttr('%s.w%d' % (constr_name, i), 0.0)
                cmds.setKeyframe('%s.w%d' % (constr_name, i), ott='step')

            # se il target non e' presente nel constrain allora aggiungilo
            if target not in target_list:
                _add_target(constr_name, target)
                # settalo a 0 nel primo fotogramma (dato che e' nuovo), non vale se sono nel primo frame
                if current_frame > first_frame:
                    cmds.setKeyframe('%s.w%d' % (constr_name, len(target_list)), ott='step', t=first_frame, v=0.0)

            # settalo a 1 nel fotogramma corrente
            target_id = cmds.parentConstraint(constr_name, q=True, tl=True).index(target)
            cmds.setAttr('%s.w%d' % (constr_name, target_id), 1.0)
            cmds.setKeyframe('%s.w%d' % (constr_name, target_id), ott='step')

            # snappa la posizione del controllo snap sulla posizione precedente e setta le chiavi del controllo snap
            _set_world_location(snap_group, ctrl_w_loc)
            cmds.setKeyframe(snap_group, at=['translate', 'rotate'], ott='step')

        # se il constrain non esiste
        else:
            # crea il constrain e setta il keyframe
            _create_parent_constraint(ctrl, target, constr_name)
            cmds.setKeyframe(constr_name, at='w0', ott='step')

            # snappa la posizione del controllo snap sulla posizione precedente e setta le chiavi del controllo snap
            _set_world_location(snap_group, ctrl_w_loc)
            cmds.setKeyframe(snap_group, at=['translate', 'rotate'], ott='step')

            # settalo a 0 nel primo fotogramma (dato che e' nuovo), non vale se sono nel primo frame
            if current_frame > first_frame:
                cmds.setKeyframe(constr_name, at='w0', ott='step', t=first_frame, v=0.0)
                cmds.setKeyframe(snap_group, at=['translate', 'rotate'], ott='step', t=first_frame, v=0.0)

        # set keyframes to green
        cmds.keyframe([snap_group, constr_name], tds=True)
        # setta le curve step
        cmds.keyTangent([snap_group, constr_name], ott='step')

        # se e' un rigid body settalo passivo
        _rb_attach(ctrl)

        # aggiorna la timeline window
        pm_script_job_cmd(ctrl)

    # seleziona il target
    cmds.select(ctrls)
    # output
    sys.stdout.write(' '.join(ctrls) + ' attached to ' + target + '\n')


def detach():
    """Detacha il parent constraint attivo."""

    sel, ctrls = _get_ctrls_from_selection(PARENT_HANDLE_SUFFIX)

    # se non ho selezionato nessun controllo provvisto di ph esci
    if not ctrls:
        raise Exception('No valid objects selected')

    for ctrl in ctrls:
        snap_group = _get_snap_group(ctrl)
        # memorizza la posizione del controllo per poi fare lo snap sulla stessa
        ctrl_w_loc = _get_world_location(snap_group)
        # nome del constrain
        constr_name = _get_parent_constraint(ctrl)

        temp = cmds.ls(constr_name)
        # se il parent constr esiste
        if temp:
            # se non ci sono target attivi esci
            if not _get_active_attach_target(constr_name):
                continue

            target_list = cmds.parentConstraint(constr_name, q=True, tl=True)
            # azzera tutti i target
            for i, target in enumerate(target_list):
                cmds.setAttr('%s.w%d' % (constr_name, i), 0.0)
                cmds.setKeyframe('%s.w%d' % (constr_name, i), ott='step')

            # snappa la posizione del controllo sulla posizione precedente e setta le chiavi del controllo
            _set_world_location(snap_group, ctrl_w_loc)
            cmds.setKeyframe(snap_group, at=['translate', 'rotate'], ott='step')
            cmds.keyframe([snap_group, constr_name], tds=True)
            # setta le curve step
            cmds.keyTangent([snap_group, constr_name], ott='step')

            # se e' un rigid body settalo attivo da questo frame
            _rb_detach(ctrl)

            # aggiorna la timeline window
            pm_script_job_cmd(ctrl)

    # output
    sys.stdout.write(' '.join(ctrls) + ' detached\n')


def destroy():
    """Cancella i parent constraint."""

    sel, ctrls = _get_ctrls_from_selection(PARENT_HANDLE_SUFFIX)

    # se non ho selezionato nessun controllo provvisto di ph esci
    if not ctrls:
        raise Exception('No valid objects selected')

    # chiedi se fare bake o no
    result = cmds.confirmDialog(title='Destroy constraints',
                                message='The constraints will be deleted.\n'
                                        'Do you want to revert to previous state or bake and keep animation?',
                                button=['Revert', 'Bake', 'Cancel'],
                                defaultButton='Revert', cancelButton='Cancel', dismissString='Cancel')
    if result == 'Cancel':
        return
    bake = result == 'Bake'

    for ctrl in ctrls:
        # nome del constrain
        constr_name = _get_parent_constraint(ctrl)

        # se il gruppo snap esiste
        if cmds.objExists(_get_snap_group(ctrl)):
            # se il parent constr esiste (lo snap group puo' esistere anche senza parent constr...
            # vedi la feature Create parent groups)
            if cmds.objExists(constr_name):
                # se necessario crea il locator e fai il bake
                if bake:
                    _bake_obj(ctrl)
                target_list = cmds.parentConstraint(constr_name, q=True, tl=True)
                # azzera tutti i target e cancella il constraint
                for i, target in enumerate(target_list):
                    cmds.setAttr('%s.w%d' % (constr_name, i), 0.0)
                cmds.delete(constr_name)

            # cancella le chiavi del controllo snap
            cmds.cutKey(_get_snap_group(ctrl), at=['translate', 'rotate'])
            # ripristino gli attributi del controllo snap a 0
            [cmds.setAttr('%s.%s' % (_get_snap_group(ctrl), s), 0.0) for s in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']]

            # se possibile (cioe' se non referenziato) parento l'oggetto al genitore originario
            try:
                ctrl_parent = cmds.pickWalk(_get_parent_handle(ctrl), d='up')[0]
                if ctrl_parent == _get_parent_handle(ctrl):
                    cmds.parent(ctrl, r=True, w=True)
                else:
                    cmds.parent([ctrl, ctrl_parent], r=True)
                # cancello il parent handle
                cmds.delete(_get_parent_handle(ctrl))
            except:
                pass

            # resetta il rigid body
            _reset_rigid_body(ctrl)
            if bake:
                _apply_baked_animation(ctrl)

            # aggiorna la timeline window
            pm_script_job_cmd(ctrl)

    # seleziona i controlli
    cmds.select(ctrls)

    # output
    sys.stdout.write(' '.join(ctrls) + ' constraints destroyed\n')


def fix_snap(time_range=False, obj=None):
    """Fixa lo snap."""

    if obj:
        cmds.select(obj)

    # carica la selezione
    sel, ctrls = _get_ctrls_from_selection(PARENT_CONSTRAINT_SUFFIX)

    # se non ho selezionato nessun controllo provvisto di ph esci
    if not ctrls:
        raise Exception('No valid objects selected')

    # esegui il fix per ogni oggetto
    for ctrl in ctrls:
        _fix_this(ctrl, time_range)

    # ripristina la selezione
    cmds.select(sel)


def select_constraint_nodes(obj=None):
    """Metodo per la selezione del controllo snap e del constraint."""

    # se chiamo il metodo con l'argomento non leggere la selezione
    if obj:
        if isinstance(obj, list):
            sel = obj
        else:
            sel = [obj]
        ctrls = sel
    # leggi la selezione
    else:
        # carica la selezione
        sel, ctrls = _get_ctrls_from_selection(PARENT_HANDLE_SUFFIX)

        # se non ho selezionato nessun controllo provvisto di ph esci
        if not ctrls:
            raise Exception('No valid objects selected')

    # deseleziona tutto
    cmds.select(cl=True)
    for ctrl in ctrls:
        # nome del constrain
        constr_name = _get_parent_constraint(ctrl)

        temp = cmds.ls(constr_name)
        # se il parent constr esiste
        if temp:
            cmds.select([_get_snap_group(ctrl), constr_name], add=True)
            # se inoltre esiste anche il nodo rigidbody
            rb = _get_rigid_body(ctrl)
            if rb:
                try:
                    # seleziona i nodi di animazione del rigidbody (compreso l'animazione active)
                    choices = cmds.listConnections(ctrl, s=True, d=False, t='choice')
                    anim_curves = cmds.listConnections(choices, s=True, d=False, t='animCurve')
                    anim_curves.append(cmds.listConnections(rb + '.act', d=False)[0])
                    cmds.select(anim_curves, add=True)
                except:
                    pass

    # se ho specificato l'argomento, non printare niente
    if obj:
        return

    # mostra a chi e' parentato
    sel = cmds.ls(sl=True)
    if not sel:
        sys.stdout.write('%s not constrained\n' % ' '.join(ctrls))
    else:
        _print_parents(cmds.ls(sel, type='parentConstraint'))


def navigate(direction):
    """Go to next/prev constraint."""

    sel, constr_names = _get_ctrls_from_selection(PARENT_CONSTRAINT_SUFFIX)
    if not constr_names:
        return

    constr_names = [_get_parent_constraint(s) for s in constr_names]

    if direction > 0:
        current_frame = cmds.currentTime(q=True)
        target_frame = cmds.findKeyframe(constr_names, which='next', t=(current_frame+0.01, current_frame+0.01))
    else:
        target_frame = cmds.findKeyframe(constr_names, which='previous')

    # spostati nella timeline
    cmds.currentTime(target_frame)

    # visualizza gli oggetti a cui sono attaccati gli oggetti selezionati
    _print_parents(constr_names)


def show(width=_default_size[0], height=_default_size[1]):
    """Main UI."""

    win_name = 'zvParentMasterWin'
    if cmds.window(win_name, exists=True):
        cmds.deleteUI(win_name, window=True)

    cmds.window(win_name, title='ZV', tlb=True)
    cmds.columnLayout(adj=True, rs=0, bgc=(0.3, 0.3, 0.3))

    # PULSANTI #
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_attach.xpm'),
                        c=cb(attach), ann='Attach objects')
    cmds.popupMenu(mm=True)
    cmds.menuItem(l='Create parent groups - translation', c=cb(create_parent_groups, True, False), rp='NE')
    cmds.menuItem(l='Create parent groups - available attrs', c=cb(create_parent_groups), rp='E')
    cmds.menuItem(l='Create parent groups - rotation', c=cb(create_parent_groups, False, True), rp='SE')
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_detach.xpm'),
                        c=cb(detach), ann='Detach objects')
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_destroy.xpm'),
                        c=cb(destroy), ann='Destroy constraints')
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_fixsnap.xpm'),
                        c=cb(fix_snap), ann='Fix snap')
    cmds.popupMenu(mm=True)
    cmds.menuItem(l='Fix snaps in the active range', c=cb(fix_snap, True), rp='E')
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_select.xpm'),
                        c=cb(select_constraint_nodes), ann='Select constraints and snap groups')
    cmds.iconTextButton(style='iconOnly', h=34, bgc=(0.3, 0.3, 0.3), image=os.path.join(_icons_path, 'pm_timeline.xpm'),
                        c=cb(timeline), ann='Constraint timeline')
    cmds.popupMenu(mm=True)
    cmds.menuItem(l='<- Prev', c='%s.navigate(-1)' % __name__, rp='W')
    cmds.menuItem(l='Next ->', c='%s.navigate(1)' % __name__, rp='E')
    cmds.setParent('..')

    cmds.showWindow(win_name)
    cmds.window(win_name, edit=True, widthHeight=(width, height))

    sys.stdout.write('ZV Parent Master %s          http://www.paolodominici.com          paolodominici@gmail.com\n'
                     % __version__)


################
#   TIMELINE   #
################
def timeline():
    """Timeline UI."""

    sel, objects = _get_ctrls_from_selection(PARENT_CONSTRAINT_SUFFIX)

    if not objects:
        raise Exception('No valid objects selected')

    width, height = _get_timeline_win_size()

    for obj in objects:
        win_name = obj + _time_win_sfx
        if cmds.window(win_name, exists=True):
            cmds.deleteUI(win_name, window=True)

        cmds.window(win_name, title=obj, tlb=True)

        main_form = cmds.formLayout(nd=100, bgc=(0.3, 0.3, 0.3))

        # controlli del form
        frt = cmds.text(obj + _label_sfx[0], l='', al='center', w=50, bgc=(0.6, 0.6, 0.6))
        att = cmds.text(obj + _label_sfx[1], l='', fn='boldLabelFont', bgc=(0.6, 0.6, 0.6))
        time_form = cmds.formLayout(obj + _time_form_sfx, nd=_time_form_div, bgc=(0.3, 0.3, 0.3))

        # edita il form principale
        cmds.formLayout(main_form, e=True,
                        attachForm=[(time_form, 'left', 0), (time_form, 'top', 0), (time_form, 'right', 0),
                                    (frt, 'left', 0), (frt, 'bottom', 0), (att, 'right', 0), (att, 'bottom', 0)],
                        attachControl=[(time_form, 'bottom', 0, frt), (att, 'left', 0, frt)])

        _refr_time_form(obj)

        cmds.showWindow(win_name)
        cmds.window(win_name, e=True, wh=(width, height))

        pm_script_job(obj, win_name)


def _refr_time_form(obj):
    """Aggiorna il form della timeline window."""

    time_form = obj + _time_form_sfx
    tmin = cmds.playbackOptions(q=True, min=True)
    tmax = cmds.playbackOptions(q=True, max=True)
    rng = tmax - tmin + 1.0
    current_frame = cmds.currentTime(q=True)

    # rimuovi gli elementi del time form
    children = cmds.formLayout(time_form, q=True, ca=True)
    if children:
        cmds.deleteUI(children)

    # rintraccia il nodo di parent
    pc_node = cmds.ls(_get_parent_constraint(obj))
    if pc_node:
        pc_node = pc_node[0]
    else:
        # aggiorna le label
        cmds.text(obj + _label_sfx[0], e=True, l='%d' % current_frame, w=50)
        cmds.text(obj + _label_sfx[1], e=True, l='')
        return

    # il main form e' il parent
    cmds.setParent(time_form)

    # parametri per l'edit del form
    attach_positions = []
    attach_forms = []

    # lista dei target
    targets = cmds.parentConstraint(pc_node, q=True, tl=True)
    for tid, target in enumerate(targets):
        times = cmds.keyframe('%s.w%d' % (pc_node, tid), q=True, tc=True)
        values = cmds.keyframe('%s.w%d' % (pc_node, tid), q=True, vc=True)

        # nessuna chiave, lista nulla e passa al successivo
        if not times:
            continue

        # indici dei tempi delle chiavi di attach/detach
        idx_list = []
        check = True
        for v, val in enumerate(values):
            if val == check:
                idx_list.append(v)
                check = not check

        # deve funzionare anche se l'ultima chiave e' attached (quindi numero chiavi dispari)
        times.append(cmds.playbackOptions(q=True, aet=True)+1.0)

        # ogni elemento di attach times e' relativo ad un particolare target ed e' una lista di questo tipo
        # [[3,10], [12, 20]]
        time_ranges = [times[idx_list[i]:idx_list[i]+2] for i in range(0, len(idx_list), 2)]

        hsv_col = _get_color(tid)

        # aggiungi i nuovi controlli
        for timeRange in time_ranges:
            # normalizza il timeRange
            norm_range = [_time_form_div * (_crop(tr, tmin, tmax + 1) - tmin) / rng for tr in timeRange]

            # se l'elemento e' stato croppato dal timerange passa al successivo
            if norm_range[0] == norm_range[1]:
                continue

            control = cmds.canvas(hsvValue=hsv_col, w=1, h=1, ann='%s [%d, %d]' %
                                                                  (target, timeRange[0], timeRange[1]-1.0))
            for button in [1, 3]:
                cmds.popupMenu(mm=True, b=button)
                cmds.menuItem(l='[%s]' % target, c=cb(cmds.select, target), rp='N')
                cmds.menuItem(l='Select child', c=cb(cmds.select, obj), rp='S')
                cmds.menuItem(l='Fix snaps', c=cb(fix_snap, True, obj), rp='E')

            attach_forms.extend([(control, 'top', 0), (control, 'bottom', 0)])
            attach_positions.extend([(control, 'left', 0, norm_range[0]), (control, 'right', 0, norm_range[1])])

    # current frame
    if tmin <= current_frame <= tmax:
        frame_size = _time_form_div / rng
        norm_cf = frame_size*(current_frame - tmin)
        current_target = _get_active_attach_target(pc_node)
        if not current_target:
            hsv_col = (0.0, 0.0, 0.85)
        else:
            hsv_col = _get_color(targets.index(current_target), 0.15)
        cf = cmds.canvas(hsvValue=hsv_col, w=1, h=1)

        attach_forms.extend([(cf, 'top', 0), (cf, 'bottom', 0)])
        attach_positions.extend([(cf, 'left', 0, norm_cf), (cf, 'right', 0, norm_cf+frame_size)])

    # setta i parametri del form
    cmds.formLayout(time_form, e=True, attachForm=attach_forms, attachPosition=attach_positions)

    # aggiorna le label
    cmds.text(obj + _label_sfx[0], e=True, l='%d' % current_frame, w=50)
    cmds.text(obj + _label_sfx[1], e=True, l='[%s]' % _get_active_attach_target(pc_node))


def pm_script_job(obj, parent):
    job_nums = [cmds.scriptJob(p=parent, e=['timeChanged', cb(pm_script_job_cmd, obj)]),
                cmds.scriptJob(p=parent, e=['playbackRangeChanged', cb(pm_script_job_cmd, obj)]),
                cmds.scriptJob(p=parent, e=['playbackRangeSliderChanged', cb(pm_script_job_cmd, obj)])]

    return job_nums


def pm_script_job_cmd(obj):
    if cmds.window(obj + _time_win_sfx, exists=True):
        _refr_time_form(obj)


def _crop(val, min_val, max_val):
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    else:
        return val


def _get_color(idx, sat=None):
    """Restituisce il colore (in hsv) della barra della timeline per un dato indice.
    Ogni parente ha un colore diverso."""

    hsv_col = _timeline_hsv_colors[idx % len(_timeline_hsv_colors)]
    if not sat:
        return hsv_col
    else:
        return hsv_col[0], sat*hsv_col[1], hsv_col[2]


def _get_timeline_win_size():
    """Dimensione finestra timeline."""

    return 1600, 38
