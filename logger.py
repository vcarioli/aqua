# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		logger
##----------------------------------------------------------------------------------------------------------------------

__all__ = ["Logger"]

##======================================================================================================================

from logging import basicConfig, DEBUG, info, debug, error, exception, warning
from os.path import basename


##======================================================================================================================


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

	def __set_debug_mode(self, value):
		self.__debug_mode__ = value

	def __get_debug_mode(self):
		return self.__debug_mode__

	debug_mode = property(__get_debug_mode, __set_debug_mode)

	def __set_info_level(self, value):
		self.__info_level__ = value

	def __get_info_level(self):
		return self.__info_level__

	info_level = property(__get_info_level, __set_info_level)

	def __get_filename(self):
		return self.__filename__

	def __set_filename(self, value):
		self.__filename__ = value

	filename = property(__get_filename, __set_filename)

	def __get_log_filename(self):
		return self.__log_filename__

	def __set_log_filename(self, value):
		self.__log_filename__ = value

	log_filename = property(__get_log_filename, __set_log_filename)

	def __get_prefix(self):
		return self.__prefix__

	def __set_prefix(self, value):
		self.__prefix__ = value

	prefix = property(__get_prefix, __set_prefix)

	def __get_separator(self):
		return self.__separator__

	def __set_separator(self, value):
		self.__separator__ = value

	separator = property(__get_separator, __set_separator)

	def __get_filler(self):
		return self.__filler__

	def __set_filler(self, value):
		self.__filler__ = value

	filler = property(__get_filler, __set_filler)

	def info(self, msg, *args, **kwargs):
		if self.info_level > 0:
			info(msg, *args, **kwargs)

	def prefix_info(self, msg, *args, **kwargs):
		"""
		Aggiunge un log 'INFO' con il prefisso se presente
		"""
		if self.info_level > 0:
			info((self.prefix if self.prefix else '') + msg, *args, **kwargs)

	def center_info(self, msg='', sep='', filler='-'):
		if self.info_level > 0:
			sep = self.separator if len(sep) == 0 else sep
			fill = self.filler if len(filler) == 0 else filler
			info('{sep}{msg}{sep}'.format(msg=msg, sep='' if msg == '' or msg is None else sep).center(self.__line_len__, fill))

	@staticmethod
	def warn(msg, *args, **kwargs):
		warning(msg, *args, **kwargs)

	def prefix_warn(self, msg, *args, **kwargs):
		"""
		Aggiunge un log 'WARNING' con il prefisso se presente
		"""
		warning((self.prefix if self.prefix else '') + msg, *args, **kwargs)

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

