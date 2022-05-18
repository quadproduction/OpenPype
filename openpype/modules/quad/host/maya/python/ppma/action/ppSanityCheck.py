# -*- coding: utf-8 -*-

"""
import export command
"""
import maya.cmds as cmds
import fnmatch
import logging

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppSanityCheck')
logger.setLevel(logging.DEBUG)


class SanityCheck(object):
	"""docstring for ClassName"""
	def __init__(self):
		super(SanityCheck, self).__init__()

		# setting global / how to know wich sanity check must applied for a step
		self.settings = {
							"common": {
										"check_list": [
														{"root_transform_exist": {}},
														{"no_unknown_node": {}},
														{"no_unassociated_reference_node": {}},
													]

							},

							"surface": {
										"check_list": ["do_setMaxwellRenderMinTime"]
							}
		}

		# init sanity check result
		self.global_status = True

		# init result
		self.result = {}

	def start_sanity_check(self, step=None):
		"""
		launch bunch of process to check the scene sanity.
		:param step: step name like surface, light, anim. please refer to shotgun pipeline step.
		"""
		# init global result
		self.global_status = True

		# init commands list
		sc_cmds = []

		# first thing we add the common sanity check.
		sc_cmds.extend(self.settings['common']['check_list'])

		# extend the list by the step sanity check
		if step:
			if step in self.settings.keys():
				sc_cmds.extend(self.settings[step]['check_list'])

		for sc_cmd in sc_cmds:
			# sc_cmd follow the template {"function_to_evaluate": {'arg1':'argValue1', 'arg2':'argValue2'}},
			# construct command
			cmdList = ["self.%s(" % sc_cmd.keys()[0]]
			for arg in sc_cmd[sc_cmd.keys()[0]].keys():
				if len(cmdList) > 1:
					cmdList.append(',')

				cmdList.append("{arg}={val}".format(arg=arg, val=sc_cmd[sc_cmd.keys()[0]][arg]))

			cmdList.append(')')

			# stringify the command list
			cmd = " ".join(cmdList)

			# evaluate command
			logger.error("evaluate sanity check : {s}".format(s=sc_cmd.keys()[0]))
			try:
				exec(cmd)
			except RuntimeError, e:
				logger.error("can't evaluate sanity check : {s}".format(s=sc_cmd.keys()[0]))
				logger.error("error : {e}".format(e=e))

		# set global status
		self.global_status = self.get_global_status()

		# print report
		self.create_report()

		return self.global_status

	def create_report(self, force=True):
		"""
		"""
		self.report = ""
		# print sanity check report
		if not self.global_status or force:
			self.report = "===: Sanity Check Report:===\n"
			for key in sorted(self.result.keys()):
				self.report += "\t {cmd}: {r}\n".format(cmd=key, r=self.result[key]['result'])
				self.report += "\t\t detail: {d}\n".format(d=self.result[key]['detail'])

		logger.info(self.report)

	def get_global_status(self):
		"""
		get global sanity check status.
		parse the self.result for gettting the global status
		"""

		# init result
		self.global_status = True

		for key in self.result.keys():

			if not self.result[key]['result']:
				self.global_status = False

		return self.global_status

	def root_transform_exist(self):
		"""
		this func check if a root group exist at the in the scene.
		"""
		node = '|root'

		if not cmds.ls(node):
			cmds.createNode('transform', name=node)

		if not cmds.ls(node):
			# set result
			self.result['root_transform_exist'] = {"result": False, 'detail': None}
			return False
		else:
			# set result
			self.result['root_transform_exist'] = {"result": True, 'detail': None}
			return True

	def no_unknown_node(self, and_remove=True):
		"""
		this func check."""

		node_list_pattern = ['_UNKNOWN_REF_NODE_']
		node_type_list_pattern = ['unknown']
		node_list = cmds.ls()

		# init report
		report_list = ['nodes_found:']
		good = True

		# check node based on name
		for node_pattern in node_list_pattern:
			for node in node_list:
				if fnmatch.fnmatch(node, node_pattern):
					# check if node locked
					if cmds.lockNode(node, lock=True, query=True):
						cmds.lockNode(node, lock=False)

					# delete it
					if and_remove:
						logger.info("==> sanity check : delete node : {n}".format(n=node))
						cmds.delete(node)
					else:
						good = False
						report_list.append(node)

		# check node based on node type
		for node_pattern in node_type_list_pattern:
			# get node by type
			node_list = cmds.ls(type=node_pattern)

			if node_list:
			# delete it
				if and_remove:
					logger.info("==> sanity check : delete node : {n}".format(n=node_list))
					cmds.delete(node_list)
				else:
					good = False
					report_list.extend(node_list)

		self.result['no_unknown_node'] = {"result": good}
		if good:
			self.result['no_unknown_node']['detail'] = None
		else:
			self.result['no_unknown_node']['detail'] = " ".join(report_list)
		return good

	def no_unassociated_reference_node(self, and_remove=True):
		"""
		this func check a reference linked to reference file."""
		# init report
		report_list = ['nodes_found:']
		good = True

		# first let's look at maya references
		ref_nodes = cmds.ls(references=True)

		for node in ref_nodes:

			if not fnmatch.fnmatch(node, "*sharedReferenceNode*"):

				# get the path:
				try:
					ref_path = cmds.referenceQuery(node, filename=True)
				except:
					if and_remove:
						# check if node locked
						if cmds.lockNode(node, lock=True, query=True):
							cmds.lockNode(node, lock=False)

						# delete it
						if and_remove:
							logger.info("==> sanity check : delete node : {n}".format(n=node))
							cmds.delete(node)
						else:
							good = False
							report_list.append(node)

		self.result['no_unassociated_reference_node'] = {"result": good}
		if good:
			self.result['no_unassociated_reference_node']['detail'] = None
		else:
			self.result['no_unassociated_reference_node']['detail'] = " ".join(report_list)

		return good

	def remove_anim_curve_connected_to_reference_node(self):
		"""
		unfortunately in maya 2016 sometimes you could have animcurve connected to reference node.
		but when you re open the scene maya made mistake bad reconnect the anim curve to the controler.
		this func search animCurve connected to reference node and if the reference is not unloaded, the anim curve was delete.
		"""
		# init report
		report_list = ['nodes_found:']
		good = True

		logger.info("remove_animation_curve_connected_to_reference_node")

		# retrieve anim_curve
		anim_curves = cmds.ls(type="animCurve")

		for anim_curve in anim_curves:

			# check if the anim_curve is connected
			items = cmds.listConnections("{n}.output".format(n=anim_curve), d=True, s=False)
			logger.debug("output connection for node : {n} > {items}".format(n=anim_curve, items=items))

			if items:
				for item in items:
					# get node type
					if cmds.nodeType(item) == "reference":
						# check if the reference is unloaded
						if cmds.referenceQuery(item, isLoaded=True) and len(items) == 1:
							# delete item
							logger.info("\tdelete node : {n}".format(n=anim_curve))
							cmds.delete(anim_curve)

		self.result['remove_anim_curve_connected_to_reference_node'] = {"result": good}
		if good:
			self.result['remove_anim_curve_connected_to_reference_node']['detail'] = None
		else:
			self.result['remove_anim_curve_connected_to_reference_node']['detail'] = " ".join(report_list)

		return good


def sanity_check(step=None):
	"""
	do sanity check on scene
	"""

	sc = SanityCheck()
	sc.start_sanity_check(step=step)

	return sc


def remove_anim_curve_connected_to_reference_node():
	"""
	"""
	sc = SanityCheck()
	r = sc.remove_anim_curve_connected_to_reference_node()

	return r
