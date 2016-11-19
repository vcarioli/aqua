# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------------------------------------------------
##	Name:		aquaerrors
##----------------------------------------------------------------------------------------------------------------------

# Internal errors
UNHANDLED_ERROR				= -1
UNKNOWN_FIELD_TYPE_ERROR	= 1
ARGUMENT_ERROR				= 2
ASSIGNMENT_ERROR			= 3
NO_FILE_ERROR				= 4
DATA_CONVERSION_ERROR		= 5
CLASSDEFS_PARSE_ERROR		= 6

# User errors

USER_ERROR_BASE = 100

COST_CODE_MISSING_ERROR		= USER_ERROR_BASE + 1	# 101
DATA_MISSING_ERROR			= USER_ERROR_BASE + 2	# 102
INVALID_DATA_ERROR			= USER_ERROR_BASE + 3	# 103



##======================================================================================================================

__all__ = [
	"UnknownFieldTypeError",
	"ArgumentError",
	"AssignmentError",
	"NoFileError",
	"DataConversionError"
	"CostCodeMissingError",
	"DataMissingError",
	"InvalidDataError",
	"ClassDefsParseError"
]

##======================================================================================================================

class AquaException(Exception):
	def __init__(self):
		self.exit_code = 0

	def __str__(self):
		pass

##======================================================================================================================

class UnknownFieldTypeError(AquaException):
	"""An error from creating or using an argument (optional or positional)."""

	def __init__(self, field_name, field_type):
		self.fieldname, self.fieldtype = field_name, field_type
		self.exit_code = UNKNOWN_FIELD_TYPE_ERROR

	def __str__(self):
		return 'field {0}: "{1}" unknown field type'.format(self.fieldname, self.fieldtype)


class ArgumentError(AquaException):
	"""
	An error from creating or using an argument (optional or positional).
	"""

	def __init__(self, argument, message):
		self.argname, self.msg = argument, argument + ": " + message
		self.exit_code = ARGUMENT_ERROR

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)


class AssignmentError(AquaException):
	"""An error from assigning a wrong type or value to a field."""

	def __init__(self, fieldname, message):
		self.fieldname, self.msg = fieldname, message
		self.exit_code = ARGUMENT_ERROR

	def __str__(self):
		return 'field {0}: {1}'.format(self.fieldname, self.msg)


class NoFileError(AquaException):
	"""An error from referencing a file that does not exists"""

	def __init__(self, filename, message=None):
		self.argname, self.msg = filename, message if message else "does not exist"
		self.exit_code = NO_FILE_ERROR

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)


class DataConversionError(AquaException):
	"""An error from assigning a wrong type or value to a field."""

	def __init__(self, fieldname, message):
		self.fieldname, self.msg = fieldname, message
		self.exit_code = DATA_CONVERSION_ERROR

	def __str__(self):
		return 'field {0}: {1}'.format(self.fieldname, self.msg)


class CostCodeMissingError(AquaException):
	"""
	Relevant input-data is missing.
	"""

	def __init__(self, cls_name, message):
		self.cls_name, self.msg = cls_name, message
		self.exit_code = COST_CODE_MISSING_ERROR

	def __str__(self):
		return self.msg


class DataMissingError(AquaException):
	"""
	Relevant input-data is missing.
	"""

	def __init__(self, cls_name, message):
		self.cls_name, self.msg = cls_name, message
		self.exit_code = DATA_MISSING_ERROR

	def __str__(self):
		return self.msg


class InvalidDataError(AquaException):
	"""
	Relevant input-data is inconsistent.
	"""

	def __init__(self, cls_name, message):
		self.cls_name, self.msg = cls_name, message
		self.exit_code = INVALID_DATA_ERROR

	def __str__(self):
		return self.msg

class ClassDefsParseError(AquaException):
	"""
	Erro parsing classdefs.txt
	"""

	def __init__(self, cls_name, message):
		self.cls_name, self.msg = cls_name, message
		self.exit_code = CLASSDEFS_PARSE_ERROR

	def __str__(self):
		return self.msg
