# -*- Mode: Python; tab-width: 4 -*-
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:		aquaerrors
#-------------------------------------------------------------------------------

__all__ = [
	"UnknownFieldTypeError",
	"ArgumentError",
	"AssignmentError",
	"NoFileError",
	"AquaClassesGenerationError",
	"DataMissingError"
]

UNKNOWN_FIELD_TYPE_ERROR = 1
ARGUMENT_ERROR = 2
ASSIGNMENT_ERROR = 3
NO_FILE_ERROR = 4
AQUACLASSES_GENERATION_ERROR = 5
DATA_MISSING_ERROR = 6


#=##############################################################################
class NoFileError(Exception):
	"""An error from referencing a file that does not exists"""

	def __init__(self, filename, message=None):
		self.argname, self.msg = filename, message if message else "does not exist"
		self.exit_code = NO_FILE_ERROR

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)


#=##############################################################################
class UnknownFieldTypeError(Exception):
	"""An error from creating or using an argument (optional or positional)."""

	def __init__(self, field_name, field_type):
		self.fieldname, self.fieldtype = field_name, field_type
		self.exit_code = UNKNOWN_FIELD_TYPE_ERROR

	def __str__(self):
		return 'field {0}: "{1}" unknown field type'.format(self.fieldname, self.fieldtype)


#=##############################################################################
class ArgumentError(Exception):
	"""
	An error from creating or using an argument (optional or positional).
	"""

	def __init__(self, argument, message):
		self.argname, self.msg = argument, argument + ": " + message
		self.exit_code = ARGUMENT_ERROR

	def __str__(self):
		return 'argument {0}: {1}'.format(self.argname, self.msg)

	# =##############################################################################


#=##############################################################################
class AssignmentError(Exception):
	"""An error from assigning a wrong type or value to a field."""

	def __init__(self, fieldname, message):
		self.fieldname, self.msg = fieldname, message
		self.exit_code = ARGUMENT_ERROR

	def __str__(self):
		return 'field {0}: {1}'.format(self.fieldname, self.msg)


#=##############################################################################
class AquaClassesGenerationError(Exception):
	"""Error generating the file aquaclasses.py."""

	def __init__(self):
		self.exit_code = AQUACLASSES_GENERATION_ERROR

	def __str__(self):
		return 'Error during generation of "aquaclasses.py"'


#=##############################################################################
class DataMissingError(Exception):
	"""
	Relevant input-data is missing.
	"""

	def __init__(self, cls_name, message):
		self.cls_name, self.msg = cls_name, message
		self.exit_code = DATA_MISSING_ERROR

	def __str__(self):
		return "Class {0}: {1}".format(self.cls_name, self.msg)
