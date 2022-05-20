"""
DESCRIPTION:
    FkIk match is a tool for matching FkIk.
    Works properly in any version of Autodesk Maya.

USAGE:
    You may go to this link to have more detail >>
    http://projects.adiendendra.com/ad-universal-fkik-setup-tutorial/

AUTHOR:
    Adien Dendra

CONTACT:
    adprojects.animation@gmail.com | hello@adiendendra.com

VERSION:
    1.0 - 18 October 2020 - Initial Release
    1.1 - 01 November 2020 - Adding setup LocalSpace ctrl; Renaming joint guide; Deleting AD_MEASURE node fixed; Adding toe wiggle exists

LICENSE:
    Copyright (C) 2020 Adien Dendra - hello@adiendendra.com>
    This is commercial license can not be copied and/or
    distributed without the express permission of Adien Dendra

"""

import maya.OpenMaya as om
import pymel.core as pm

layout = 265
percentage = 0.01 * layout


def ad_match_fkik_ui():
    adien_match_fkIk = 'AD_MatchFkIk'
    pm.window(adien_match_fkIk, exists=True)

    if pm.window(adien_match_fkIk, exists=True):
        pm.deleteUI(adien_match_fkIk)

    with pm.window(adien_match_fkIk, title='AD Fk/Ik Match', width=layout + 10, height=150):
        with pm.columnLayout(rs=5, co=('both', 5), adj=True):
            pm.text(l='Select Leg/Arm Ctrl Setup:')
            # button to Fk
            pm.button(label='Match To Fk', width=layout, height=40, backgroundColor=[0.09804, 0.31373, 0.30196],
                      command=pm.Callback(ad_ik_to_fk))
            # button to Ik
            pm.button(label='Match To Ik', width=layout, height=40, backgroundColor=[1.00000, 0.43137, 0.00000],
                      command=pm.Callback(ad_fk_to_ik))
            with pm.rowLayout(nc=2, cw2=(32 * percentage, 32 * percentage),
                              cl2=('left', 'center'),
                              columnAttach=[(1, 'both', 1 * percentage), (2, 'both', 1 * percentage)], adj=True):
                pm.text(l='Adien Dendra | 11/2020 | Ver. 1.1')
                pm.text(
                    l='<a href="http://projects.adiendendra.com/ad-universal-fkik-setup-tutorial/">detail to use>> </a>',
                    hl=True)
            pm.separator(h=2, st="single")

    pm.showWindow()


def ad_ik_to_fk():
    fkik_ctrl_select = pm.ls(sl=1)
    fk_ik_attr_name = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Fk_Ik_Attr_Name')
    value_fk_attr = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Fk_Value_On')

    if pm.objExists(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Fk_Guide_Joint'):
        # condition of controller
        getattr_ctrl = pm.getAttr(fkik_ctrl_select[0] + '.' + fk_ik_attr_name)
        if getattr_ctrl == value_fk_attr:
            return fkik_ctrl_select[0]
        else:
            fk_stretch_axis = []
            upper_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Joint')[0]
            middle_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Middle_Limb_Joint')[0]
            lower_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Joint')[0]

            upper_limb_fk_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Fk_Guide_Joint')[0]
            middle_limb_fk_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Middle_Limb_Fk_Guide_Joint')[0]
            lower_limb_fk_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Fk_Guide_Joint')[0]
            upper_limb_fk_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Fk_Ctrl')[0]
            middle_limb_fk_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Middle_Limb_Fk_Ctrl')[0]
            lower_limb_fk_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Fk_Ctrl')[0]
            fk_ik_arm_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'FkIk_Arm_Setup_Controller', s=1)
            fk_ik_leg_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'FkIk_Leg_Setup_Controller', s=1)
            aim_axis = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Aim_Axis')
            middle_aim_translate_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Middle_Translate_Aim_Joint')
            lower_aim_translate_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Lower_Translate_Aim_Joint')
            upper_aim_scale_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Upper_Scale_Aim_Joint')
            middle_aim_scale_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Middle_Scale_Aim_Joint')
            fk_ctrl_up_stretch = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Fk_Ctrl_Up_Stretch', s=1)
            fk_ctrl_mid_stretch = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Fk_Ctrl_Mid_Stretch', s=1)

            if fk_ctrl_up_stretch:
                fk_stretch_axis = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Stretch_Attr')

            # run snap for arm
            if fk_ik_arm_ctrl:
                # run snap for arm
                ad_ik_to_fk_setup(upper_limb_fk_jnt=upper_limb_fk_jnt, middle_limb_fk_jnt=middle_limb_fk_jnt,
                                  lower_limb_fk_jnt=lower_limb_fk_jnt, middle_limb_ctrl=middle_limb_fk_ctrl,
                                  lower_limb_ctrl=lower_limb_fk_ctrl, upper_limb_ctrl=upper_limb_fk_ctrl,
                                  fkik_setup_controller=fkik_ctrl_select,
                                  value_axis_aim_translate_middle=middle_aim_translate_axis_value,
                                  value_axis_aim_translate_lower=lower_aim_translate_axis_value,
                                  value_axis_aim_scale_upper=upper_aim_scale_axis_value,
                                  value_axis_aim_scale_middle=middle_aim_scale_axis_value,
                                  fk_ctrl_up_stretch=fk_ctrl_up_stretch,
                                  fk_ctrl_mid_stretch=fk_ctrl_mid_stretch,
                                  middle_limb_jnt=middle_limb_jnt,
                                  upper_limb_jnt=upper_limb_jnt,
                                  lower_limb_jnt=lower_limb_jnt,
                                  fk_stretch_axis=fk_stretch_axis
                                  )
            # run snap for leg
            if fk_ik_leg_ctrl:
                end_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Joint')[0]
                end_limb_fk_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Fk_Guide_Joint')[0]
                end_limb_fk_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Fk_Ctrl')[0]

                ad_ik_to_fk_setup(upper_limb_fk_jnt=upper_limb_fk_jnt, middle_limb_fk_jnt=middle_limb_fk_jnt,
                                  lower_limb_fk_jnt=lower_limb_fk_jnt, middle_limb_ctrl=middle_limb_fk_ctrl,
                                  lower_limb_ctrl=lower_limb_fk_ctrl, upper_limb_ctrl=upper_limb_fk_ctrl,
                                  fkik_setup_controller=fkik_ctrl_select,
                                  value_axis_aim_translate_middle=middle_aim_translate_axis_value,
                                  value_axis_aim_translate_lower=lower_aim_translate_axis_value,
                                  value_axis_aim_scale_upper=upper_aim_scale_axis_value,
                                  value_axis_aim_scale_middle=middle_aim_scale_axis_value,
                                  fk_ctrl_up_stretch=fk_ctrl_up_stretch,
                                  fk_ctrl_mid_stretch=fk_ctrl_mid_stretch,
                                  end_limb_fk_jnt=end_limb_fk_jnt,
                                  end_limb_ctrl=end_limb_fk_ctrl,
                                  leg=True,
                                  upper_limb_jnt=upper_limb_jnt,
                                  middle_limb_jnt=middle_limb_jnt,
                                  lower_limb_jnt=lower_limb_jnt,
                                  fk_stretch_axis=fk_stretch_axis

                                  )

            pm.setAttr(fkik_ctrl_select[0] + '.' + fk_ik_attr_name, value_fk_attr)

    else:
        pm.error('Select arm or leg setup controller for matching to Fk!')


def ad_fk_to_ik():
    # listing fk ik setup selection
    fkik_ctrl_select = pm.ls(sl=1)
    fk_ik_attr_name = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Fk_Ik_Attr_Name')
    value_ik_attr = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Ik_Value_On')

    if pm.objExists(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Ik_Guide_Joint'):
        # condition of controller
        getattr_ctrl = pm.getAttr(fkik_ctrl_select[0] + '.' + fk_ik_attr_name)
        if getattr_ctrl == value_ik_attr:
            return fkik_ctrl_select[0]
        else:
            upper_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Joint')[0]
            middle_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Middle_Limb_Joint')[0]
            lower_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Joint')[0]

            if pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Ik_Guide_Joint', s=1):
                upper_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Ik_Guide_Joint')[0]
            else:
                upper_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Joint')[0]
            middle_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Middle_Limb_Ik_Guide_Joint')[0]
            lower_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Ik_Guide_Joint')[0]
            upper_limb_ik_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Upper_Limb_Ik_Ctrl', s=1)
            poleVector_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Pole_Vector_Ik_Ctrl')[0]
            lower_limb_ik_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'Lower_Limb_Ik_Ctrl')[0]
            aim_axis = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Aim_Axis')
            middle_aim_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Middle_Translate_Aim_Joint')
            lower_aim_axis_value = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Lower_Translate_Aim_Joint')
            fk_ik_arm_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'FkIk_Arm_Setup_Controller', s=1)
            fk_ik_leg_ctrl = pm.listConnections(fkik_ctrl_select[0] + '.' + 'FkIk_Leg_Setup_Controller', s=1)

            # run for match arm
            if fk_ik_arm_ctrl:
                ad_fk_to_ik_setup(upper_limb_ik_jnt=upper_limb_ik_jnt, middle_limb_ik_jnt=middle_limb_ik_jnt,
                                  lower_limb_ik_jnt=lower_limb_ik_jnt, polevector_limb_ctrl=poleVector_ctrl,
                                  lower_limb_ctrl=lower_limb_ik_ctrl, upper_limb_ctrl=upper_limb_ik_ctrl,
                                  fkik_setup_controller=fkik_ctrl_select,
                                  )
            # run for match leg
            if fk_ik_leg_ctrl:
                rotation_wiggle = []
                ik_toe_wiggle_attr_name = []
                ik_toe_wiggle_ctrl = []

                end_limb_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Joint')[0]
                if pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Ik_Guide_Joint', s=1):
                    end_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Ik_Guide_Joint')[0]
                else:
                    end_limb_ik_jnt = pm.listConnections(fkik_ctrl_select[0] + '.' + 'End_Limb_Joint')[0]
                end_limb_ik_ctrl = pm.getAttr(fkik_ctrl_select[0] + '.' + 'End_Limb_Ik_Ctrl')

                if pm.attributeQuery('Rotation_Wiggle', n=fkik_ctrl_select[0], ex=True):
                    rotation_wiggle = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Rotation_Wiggle')
                    ik_toe_wiggle_attr_name = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Ik_Toe_Wiggle_Attr_Name')
                    ik_toe_wiggle_ctrl = pm.getAttr(fkik_ctrl_select[0] + '.' + 'Ik_Toe_Wiggle_Ctrl')

                ad_fk_to_ik_setup(upper_limb_ik_jnt=upper_limb_ik_jnt, middle_limb_ik_jnt=middle_limb_ik_jnt,
                                  lower_limb_ik_jnt=lower_limb_ik_jnt, polevector_limb_ctrl=poleVector_ctrl,
                                  lower_limb_ctrl=lower_limb_ik_ctrl, upper_limb_ctrl=upper_limb_ik_ctrl,
                                  fkik_setup_controller=fkik_ctrl_select,
                                  end_limb_ctrl=end_limb_ik_ctrl,
                                  rotation_wiggle=rotation_wiggle,
                                  ik_toe_wiggle_ctrl=ik_toe_wiggle_ctrl,
                                  ik_toe_wiggle_attr_name=ik_toe_wiggle_attr_name,
                                  end_limb_ik_jnt=end_limb_ik_jnt, leg=True,
                                  end_limb_jnt=end_limb_jnt
                                  )

            pm.setAttr(fkik_ctrl_select[0] + '.' + fk_ik_attr_name, value_ik_attr)
    else:
        pm.error('Select arm or leg setup controller for matching to Ik!')


def ad_ik_to_fk_setup(upper_limb_fk_jnt, middle_limb_fk_jnt, lower_limb_fk_jnt, middle_limb_ctrl, lower_limb_ctrl,
                      fkik_setup_controller, upper_limb_ctrl,
                      value_axis_aim_translate_middle,
                      value_axis_aim_translate_lower,
                      value_axis_aim_scale_upper, value_axis_aim_scale_middle,
                      fk_ctrl_up_stretch, fk_ctrl_mid_stretch, upper_limb_jnt, middle_limb_jnt, lower_limb_jnt,
                      end_limb_fk_jnt=None, end_limb_ctrl=None, leg=None, fk_stretch_axis=None):
    # query world position
    xform_upper_limb_rot = pm.xform(upper_limb_fk_jnt, ws=1, q=1, ro=1)
    xform_middle_limb_rot = pm.xform(middle_limb_fk_jnt, ws=1, q=1, ro=1)
    xform_low_limb_rot = pm.xform(lower_limb_fk_jnt, ws=1, q=1, ro=1)
    xform_upper_limb_pos = pm.xform(upper_limb_fk_jnt, ws=1, q=1, t=1)
    xform_middle_limb_pos = pm.xform(middle_limb_fk_jnt, ws=1, q=1, t=1)
    xform_low_limb_pos = pm.xform(lower_limb_fk_jnt, ws=1, q=1, t=1)

    # set to default
    selection = fkik_setup_controller[0]
    list_attribute_additional = pm.listAttr(selection)
    if filter(lambda x: '_DOTAT_' and '_DOTFK_' in x or '_DOTVA_' and '_DOTFK_' in x, list_attribute_additional):
        filtering_attr = filter(lambda x: '_DOTAT_' in x and '_DOTFK_' in x, list_attribute_additional)
        filtering_value = filter(lambda x: '_DOTVA_' in x and '_DOTFK_' in x, list_attribute_additional)
        for item_attr, item_value in zip(filtering_attr, filtering_value):
            get_item_attr = pm.getAttr('%s.%s' % (selection, item_attr))
            get_value_attr = pm.getAttr('%s.%s' % (selection, item_value))
            item_list = item_attr.replace('_DOTAT_', ',').replace('_DOTFK_', ',').split(',')
            item_attribute, item_controller = ' '.join(item_list).split()
            pm.setAttr('%s.%s' % (get_item_attr, item_attribute), get_value_attr)

    pm.xform(upper_limb_ctrl, ws=1, ro=(xform_upper_limb_rot[0], xform_upper_limb_rot[1], xform_upper_limb_rot[2]))
    pm.xform(middle_limb_ctrl, ws=1, ro=(xform_middle_limb_rot[0], xform_middle_limb_rot[1], xform_middle_limb_rot[2]))
    pm.xform(lower_limb_ctrl, ws=1, ro=(xform_low_limb_rot[0], xform_low_limb_rot[1], xform_low_limb_rot[2]))

    if pm.getAttr(selection + '.' + 'Translate_Fk_Ctrl_Exists'):
        upper_stretch_attr = pm.getAttr(selection + '.' + 'Fk_Attr_Up_Stretch')
        middle_stretch_attr = pm.getAttr(selection + '.' + 'Fk_Attr_Mid_Stretch')
        current_value_axis_towards_upper_jnt = pm.getAttr('%s.%s' % (upper_limb_jnt, fk_stretch_axis))
        current_value_axis_towards_middle_jnt = pm.getAttr('%s.%s' % (middle_limb_jnt, fk_stretch_axis))
        current_value_axis_towards_lower_jnt = pm.getAttr('%s.%s' % (lower_limb_jnt, fk_stretch_axis))

        if 'scale' in fk_stretch_axis:
            if pm.getAttr(selection + '.' + 'Fk_Value_Up_Stretch') < 1.0:
                length_factor_middle_jnt = current_value_axis_towards_upper_jnt - value_axis_aim_scale_upper
                length_factor_middle_jnt_result = length_factor_middle_jnt / value_axis_aim_scale_upper
                length_middle_result = length_factor_middle_jnt_result * 10.0
                pm.setAttr(fk_ctrl_up_stretch[0] + '.' + upper_stretch_attr, length_middle_result)
            else:
                length_factor_middle_jnt = current_value_axis_towards_upper_jnt / value_axis_aim_scale_upper
                pm.setAttr(fk_ctrl_up_stretch[0] + '.' + upper_stretch_attr, length_factor_middle_jnt)

            if pm.getAttr(selection + '.' + 'Fk_Value_Mid_Stretch') < 1.0:
                length_factor_lower_jnt = current_value_axis_towards_middle_jnt - value_axis_aim_scale_middle
                length_factor_lower_jnt_result = length_factor_lower_jnt / value_axis_aim_scale_middle
                length_lower_result = length_factor_lower_jnt_result * 10.0
                pm.setAttr(fk_ctrl_mid_stretch[0] + '.' + middle_stretch_attr, length_lower_result)
            else:
                length_factor_lower_jnt = current_value_axis_towards_middle_jnt / value_axis_aim_scale_middle
                pm.setAttr(fk_ctrl_mid_stretch[0] + '.' + middle_stretch_attr, length_factor_lower_jnt)
        else:
            if pm.getAttr(selection + '.' + 'Fk_Value_Up_Stretch') < 1.0:
                length_factor_middle_jnt = current_value_axis_towards_middle_jnt - value_axis_aim_translate_middle
                length_factor_middle_jnt_result = length_factor_middle_jnt / value_axis_aim_translate_middle
                length_middle_result = length_factor_middle_jnt_result * 10.0
                pm.setAttr(fk_ctrl_up_stretch[0] + '.' + upper_stretch_attr, length_middle_result)
            else:
                length_factor_middle_jnt = current_value_axis_towards_middle_jnt / value_axis_aim_translate_middle
                pm.setAttr(fk_ctrl_up_stretch[0] + '.' + upper_stretch_attr, length_factor_middle_jnt)

            if pm.getAttr(selection + '.' + 'Fk_Value_Mid_Stretch') < 1.0:
                length_factor_lower_jnt = current_value_axis_towards_lower_jnt - value_axis_aim_translate_lower
                length_factor_lower_jnt_result = length_factor_lower_jnt / value_axis_aim_translate_lower
                length_lower_result = length_factor_lower_jnt_result * 10.0
                pm.setAttr(fk_ctrl_mid_stretch[0] + '.' + middle_stretch_attr, length_lower_result)
            else:
                length_factor_lower_jnt = current_value_axis_towards_lower_jnt / value_axis_aim_translate_lower
                pm.setAttr(fk_ctrl_mid_stretch[0] + '.' + middle_stretch_attr, length_factor_lower_jnt)

    else:
        pm.xform(upper_limb_ctrl, ws=1, t=(xform_upper_limb_pos[0] - ad_localSpace_pivot_query(upper_limb_ctrl)[0],
                                           xform_upper_limb_pos[1] - ad_localSpace_pivot_query(upper_limb_ctrl)[1],
                                           xform_upper_limb_pos[2] - ad_localSpace_pivot_query(upper_limb_ctrl)[2]))
        pm.xform(middle_limb_ctrl, ws=1, t=(xform_middle_limb_pos[0] - ad_localSpace_pivot_query(middle_limb_ctrl)[0],
                                            xform_middle_limb_pos[1] - ad_localSpace_pivot_query(middle_limb_ctrl)[1],
                                            xform_middle_limb_pos[2] - ad_localSpace_pivot_query(middle_limb_ctrl)[2]))
        pm.xform(lower_limb_ctrl, ws=1, t=(xform_low_limb_pos[0] - ad_localSpace_pivot_query(lower_limb_ctrl)[0],
                                           xform_low_limb_pos[1] - ad_localSpace_pivot_query(lower_limb_ctrl)[1],
                                           xform_low_limb_pos[2] - ad_localSpace_pivot_query(lower_limb_ctrl)[2]))

    # exeption for the leg
    if leg:
        # ad_set_rotation_order(end_limb_fk_jnt, target=end_limb_ctrl)
        xform_end_limb_rot = pm.xform(end_limb_fk_jnt, ws=1, q=1, ro=1)
        xform_end_limb_pos = pm.xform(end_limb_fk_jnt, ws=1, q=1, t=1)
        pm.xform(end_limb_ctrl, ws=1, ro=(xform_end_limb_rot[0], xform_end_limb_rot[1], xform_end_limb_rot[2]))
        pm.xform(end_limb_ctrl, ws=1, t=(xform_end_limb_pos[0] - ad_localSpace_pivot_query(end_limb_ctrl)[0],
                                         xform_end_limb_pos[1] - ad_localSpace_pivot_query(end_limb_ctrl)[1],
                                         xform_end_limb_pos[2] - ad_localSpace_pivot_query(end_limb_ctrl)[2]))


def ad_fk_to_ik_setup(upper_limb_ik_jnt, middle_limb_ik_jnt, lower_limb_ik_jnt,
                      polevector_limb_ctrl, lower_limb_ctrl,
                      upper_limb_ctrl,
                      fkik_setup_controller,
                      end_limb_jnt=None,
                      end_limb_ctrl=None,
                      rotation_wiggle=None, ik_toe_wiggle_ctrl=None, ik_toe_wiggle_attr_name=None,
                      end_limb_ik_jnt=None, leg=None):
    # query position and rotation
    xform_upper_limb_rot = pm.xform(upper_limb_ik_jnt, ws=1, q=1, ro=1)
    xform_low_limb_rot = pm.xform(lower_limb_ik_jnt, ws=1, q=1, ro=1)
    xform_upper_limb_pos = pm.xform(upper_limb_ik_jnt, ws=1, q=1, t=1)
    xform_middle_limb_pos = pm.xform(middle_limb_ik_jnt, ws=1, q=1, t=1)
    xform_low_limb_pos = pm.xform(lower_limb_ik_jnt, ws=1, q=1, t=1)

    # set to default
    selection = fkik_setup_controller[0]
    list_attribute_additional = pm.listAttr(selection)
    if filter(lambda x: '_DOTAT_' and '_DOTIK_' in x or '_DOTVA_' and '_DOTIK_' in x, list_attribute_additional):
        filtering_attr = filter(lambda x: '_DOTAT_' in x and '_DOTIK_' in x, list_attribute_additional)
        filtering_value = filter(lambda x: '_DOTVA_' in x and '_DOTIK_' in x, list_attribute_additional)
        for item_attr, item_value in zip(filtering_attr, filtering_value):
            get_item_attr = pm.getAttr('%s.%s' % (selection, item_attr))
            get_value_attr = pm.getAttr('%s.%s' % (selection, item_value))
            item_list = item_attr.replace('_DOTAT_', ',').replace('_DOTIK_', ',').split(',')
            item_attribute, item_controller = ' '.join(item_list).split()
            pm.setAttr('%s.%s' % (get_item_attr, item_attribute), get_value_attr)

    if pm.listConnections(selection + '.' + 'Upper_Limb_Ik_Ctrl', s=1):
        pm.xform(upper_limb_ctrl, ws=1, ro=(xform_upper_limb_rot[0], xform_upper_limb_rot[1], xform_upper_limb_rot[2]))
        pm.xform(upper_limb_ctrl, ws=1, t=(xform_upper_limb_pos[0] - ad_localSpace_pivot_query(upper_limb_ctrl[0])[0],
                                           xform_upper_limb_pos[1] - ad_localSpace_pivot_query(upper_limb_ctrl[0])[1],
                                           xform_upper_limb_pos[2] - ad_localSpace_pivot_query(upper_limb_ctrl[0])[2]))

    # set lower position
    pm.xform(lower_limb_ctrl, ws=1, ro=(xform_low_limb_rot[0], xform_low_limb_rot[1], xform_low_limb_rot[2]))
    pm.xform(lower_limb_ctrl, ws=1, t=(xform_low_limb_pos[0] - ad_localSpace_pivot_query(lower_limb_ctrl)[0],
                                       xform_low_limb_pos[1] - ad_localSpace_pivot_query(lower_limb_ctrl)[1],
                                       xform_low_limb_pos[2] - ad_localSpace_pivot_query(lower_limb_ctrl)[2]))

    # condition leg true
    if leg:
        if not pm.listConnections(selection + '.' + 'End_Limb_Ik_Ctrl', s=1):
            if pm.getAttr(selection + '.' + 'Toe_Wiggle_Exists'):
                xform_end_limb_rot = pm.getAttr(end_limb_jnt + '.' + rotation_wiggle)
                get_reverse_wiggle = pm.getAttr(fkik_setup_controller[0] + '.' + 'Reverse_Wiggle_Value')

                if get_reverse_wiggle:
                    pm.setAttr('%s.%s' % (ik_toe_wiggle_ctrl, ik_toe_wiggle_attr_name), (-1 * xform_end_limb_rot))
                else:
                    pm.setAttr('%s.%s' % (ik_toe_wiggle_ctrl, ik_toe_wiggle_attr_name), xform_end_limb_rot)
            else:
                pass
        else:
            xform_end_limb_pos = pm.xform(end_limb_ik_jnt, ws=1, q=1, t=1)
            xform_end_limb_rot = pm.xform(end_limb_ik_jnt, ws=1, q=1, ro=1)

            pm.xform(end_limb_ctrl, ws=1, ro=(xform_end_limb_rot[0], xform_end_limb_rot[1], xform_end_limb_rot[2]))
            pm.xform(end_limb_ctrl, ws=1, t=(xform_end_limb_pos[0] - ad_localSpace_pivot_query(end_limb_ctrl)[0],
                                             xform_end_limb_pos[1] - ad_localSpace_pivot_query(end_limb_ctrl)[1],
                                             xform_end_limb_pos[2] - ad_localSpace_pivot_query(end_limb_ctrl)[2]))

    # for pole vector position
    get_poleVector_position = ad_get_pole_vector_position(xform_upper_limb_pos, xform_middle_limb_pos,
                                                          xform_low_limb_pos)

    pm.move((get_poleVector_position.x - ad_localSpace_pivot_query(polevector_limb_ctrl)[0],
             get_poleVector_position.y - ad_localSpace_pivot_query(polevector_limb_ctrl)[1],
             get_poleVector_position.z - ad_localSpace_pivot_query(polevector_limb_ctrl)[2], polevector_limb_ctrl))

    # calculate for stretching and matching the pole vector controller
    total_value_default = pm.getAttr('%s.Joint_Distance_Value_Static' % selection)
    total_current_value = pm.getAttr('%s.Joint_Distance_Value_Dynamic' % selection)

    # condition match elbow or knee
    if pm.getAttr(selection + '.' + 'Ik_Snap_Checkbox'):
        ik_snap_ctrl_name = pm.listConnections(selection + '.' + 'Ik_Snap_Ctrl_Name', s=1)[0]
        ik_snap_attr_name = pm.getAttr(selection + '.' + 'Ik_Snap_Attr_Name')
        ik_snap_on = pm.getAttr(selection + '.' + 'Ik_Snap_On')
        ik_snap_off = pm.getAttr(selection + '.' + 'Ik_Snap_Off')
        if abs(total_current_value) > total_value_default:
            ad_ik_snap_set_on(polevector_limb_ctrl, xform_middle_limb_pos, ik_snap_ctrl_name,
                              ik_snap_attr_name, ik_snap_on)
        else:
            pm.setAttr(ik_snap_ctrl_name + '.' + ik_snap_attr_name, ik_snap_off)


def ad_ik_snap_set_on(polevector_limb_ctrl, xform_middle_limb_pos, ik_snap_ctrl_name, ik_snap_attr_name, ik_snap_on):
    pm.setAttr('%s.%s' % (ik_snap_ctrl_name, ik_snap_attr_name), ik_snap_on)
    pm.xform(polevector_limb_ctrl, ws=1, t=(xform_middle_limb_pos[0], xform_middle_limb_pos[1],
                                            xform_middle_limb_pos[2]))


def ad_get_pole_vector_position(root_pos, mid_pos, end_pos):
    root_jnt_vector = om.MVector(root_pos[0], root_pos[1], root_pos[2])
    mid_jnt_vector = om.MVector(mid_pos[0], mid_pos[1], mid_pos[2])
    end_jnt_vector = om.MVector(end_pos[0], end_pos[1], end_pos[2])

    line = (end_jnt_vector - root_jnt_vector)
    point = (mid_jnt_vector - root_jnt_vector)

    scale_value = (line * point) / (line * line)
    projection_vector = line * scale_value + root_jnt_vector

    pole_vector_position = (mid_jnt_vector - projection_vector).normal() + mid_jnt_vector

    return pole_vector_position


def ad_localSpace_pivot_query(controller):
    rotatePivot = pm.getAttr(controller + '.rotatePivot')

    return rotatePivot
