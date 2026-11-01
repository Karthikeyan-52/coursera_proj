"""Keep the legacy nose 1 test runner usable on newer Python versions."""

import collections
import collections.abc
import importlib.machinery
import importlib.util
import os
import sys
import threading
import types
import unittest
import unittest.runner


if not hasattr(collections, "Callable"):
    collections.Callable = collections.abc.Callable
if not hasattr(unittest.runner, "_TextTestResult"):
    unittest.runner._TextTestResult = unittest.runner.TextTestResult
if not hasattr(unittest, "_TextTestResult"):
    unittest._TextTestResult = unittest.runner.TextTestResult


if "imp" not in sys.modules:
    imp_compat = types.ModuleType("imp")
    import_lock = threading.RLock()

    def find_module(name, path=None):
        """Return the file information expected by nose's legacy importer."""
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None or spec.origin is None:
            raise ImportError("No module named {}".format(name))
        module_type = 5 if spec.submodule_search_locations else 2
        return (
            open(spec.origin, "rb"),
            spec.origin,
            (None, None, module_type),
        )

    def load_module(name, file_handle, filename, description):
        """Load a module using the modern importlib API."""
        is_package = os.path.basename(filename) == "__init__.py"
        locations = [os.path.dirname(filename)] if is_package else None
        spec = importlib.util.spec_from_file_location(
            name,
            filename,
            submodule_search_locations=locations,
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    imp_compat.find_module = find_module
    imp_compat.load_module = load_module
    imp_compat.acquire_lock = import_lock.acquire
    imp_compat.release_lock = import_lock.release
    sys.modules["imp"] = imp_compat
