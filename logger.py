__author__ = 'valerio'

__all__ = ["Logger"]

from logging import basicConfig, DEBUG, info, error, exception
from os.path import basename

class Logger():
	def __init__(self, filename=None, log_filename=None, prefix=None, separator='  ', filler=' ', debug_mode=False, info_level=1, line_len=60):
		self.__filename__ = filename
		self.__line_len__ = line_len
		self.__log_filename__ = log_filename
		self.__prefix__ = prefix
		self.__separator__ = separator
		self.__filler__ = filler
		self.__debug_mode__ = debug_mode
		self.__info_level__ = info_level

	def __set_debug_mode__(self, value):
		self.__debug_mode__ = value

	def __get_debug_mode__(self):
		return self.__debug_mode__

	debug_mode = property(__get_debug_mode__, __set_debug_mode__)

	def __set_info_level__(self, value):
		self.__info_level__ = value
	def __get_info_level__(self):
		return self.__info_level__

	info_level = property(__get_info_level__, __set_info_level__)

	def __get_filename__(self):
		return self.__filename__

	def __set_filename__(self, value):
		self.__filename__ = value

	filename = property(__get_filename__, __set_filename__)

	def __get_log_filename__(self):
		return self.__log_filename__
	def __set_log_filename__(self, value):
		self.__log_filename__ = value
	log_filename = property(__get_log_filename__, __set_log_filename__)

	def __get_prefix__(self):
		return self.__prefix__
	def __set_prefix__(self, value):
		self.__prefix__ = value
	prefix = property(__get_prefix__, __set_prefix__)

	def __get_separator__(self):
		return self.__separator__
	def __set_separator__(self, value):
		self.__separator__ = value
	separator = property(__get_separator__, __set_separator__)

	def __get_filler__(self):
		return self.__filler__
	def __set_filler__(self, value):
		self.__filler__ = value
	filler = property(__get_filler__, __set_filler__)

	def info(self, msg, *args, **kwargs):
		if self.info_level > 0:
			info(msg, *args, **kwargs)

	def info_with_prefix(self, msg, *args, **kwargs):
		if self.info_level > 0:
			info((self.prefix if self.prefix else '') + msg, *args, **kwargs)

	def info_centered(self, msg='', sep=None, filler='-'):
		if self.info_level > 0:
			sep = self.separator if sep and len(sep) == 0 else sep
			fill = self.filler if len(filler) == 0 else filler
			info('{sep}{msg}{sep}'.format( msg=msg, sep='' if msg == '' or msg is None else ' ').center(self.__line_len__, fill))

	def debug(self, msg, *args, **kwargs):
		if self.__debug_mode__:
			debug((basename(self.filename) if self.filename else '') + ': ' + msg, *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		error(basename(self.filename) + ': ' + msg, *args, **kwargs)

	@staticmethod
	def exception(msg, *args, **kwargs):
		exception(msg, *args, **kwargs)

	def config(self, log_filename=None):
		logfile = log_filename if log_filename else self.log_filename
		basicConfig(filename=logfile, format='%(asctime)s %(levelname)-8s %(message)s', level=DEBUG)

