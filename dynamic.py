__author__ = 'denislavrov'
import importlib
from importlib.machinery import SourceFileLoader, ExtensionFileLoader, SourcelessFileLoader


def load_module(modulename, code_path=""):
	try:
		return importlib.import_module(modulename)
	except ImportError as e:
		print(e)
		if (code_path).endswith(".py"):
			return SourceFileLoader(modulename, code_path).load_module()
		if (code_path).endswith(".pyc") or code_path.endswith(".pyo"):
			return SourcelessFileLoader(modulename, code_path).load_module()
		if (code_path).endswith(".pyd") or code_path.endswith(".so"):
			return ExtensionFileLoader(modulename, code_path).load_module()
