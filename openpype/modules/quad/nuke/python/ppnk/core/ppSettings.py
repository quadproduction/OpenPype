import nuke
import os
import logging
import ppSgtkLibs.ppSgtkUtils
import ppSgtkLibs.ppProjectUtils

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppSettings')
logger.setLevel(logging.INFO)


class Settings(ppSgtkLibs.ppSgtkUtils.InitTk):
	"""docstring for ClassName"""
	def __init__(self, arg=None):
		super(Settings, self).__init__()

		# retrieve project settings from shotgun
		self.ps = ppSgtkLibs.ppProjectUtils.Project_Settings()

	def _load_ocio(self):
		if os.environ.get('OCIO'):
			logger.info("OCIO env var detected, change color management.")
			root = nuke.root()
			root['colorManagement'].setValue('1.0')
		else:
			logger.info("OCIO env var not detected.")

	def _get_project_settings(self):
		"""
		this functions retiev from shotgun tle project resolution declared.
		"""

	def _get_project_resolutions(self):
		"""
		this functions retiev from shotgun tle project resolution declared.
		"""
		self.ps.get_resolutions()

	def _set_project_resolutions(self):
		"""
		"""
		if not self.ps.resolutions:
			self._get_project_resolutions()

		if not self.ps.resolutions:
			logger.info("No Project Resolution for this Project.")
			return
		# except_resolution
		except_resolution= ['same as source']

		# get current format
		formats = nuke.formats()
		# save formats as dict like describe in ppProjectUtils.Project_Settings resolutions
		nuke_resolutions = {}
		for f in formats:
			item = {
				"name": f.name(),
				"width": f.width(),
				"height": f.height(),
				"pixel_aspect_ratio": f.pixelAspect()
			}
			nuke_resolutions[f.name()] = item

		# for each project resolution create it in Nuke.
		for k in sorted(self.ps.resolutions.keys()):
			res = self.ps.resolutions.get(k)

			# check if resolution not already exist in nuke.
			if res.get('name') not in nuke_resolutions.keys() and res.get('name') not in except_resolution:
				nuke_res_description = "{width} {height} {x} {y} {r} {t} {pixel_aspect_ratio} {name}".format(
					width=res.get('width'),
					height=res.get('height'),
					x=0,
					y=0,
					r=res.get('width'),
					t=res.get('height'),
					pixel_aspect_ratio=res.get('pixel_aspect_ratio'),
					name=res.get('name'),
				)
				logger.info("Add Resolution : {name}".format(name=res.get('name')))
				nuke.addFormat(nuke_res_description)
			else:
				logger.info("Resolution : {name} already exist in Nuke. Do not update.".format(name=res.get('name')))


	def init_script(self):
		"""
		"""
		
		# load OCIO
		self._load_ocio()

		# load project resolution aka nuke format
		self._get_resolutions_format()

