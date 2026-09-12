"""Chargement explicite des applications du monorepo pour les contrats et les tests."""
import importlib
import importlib.util
from pathlib import Path
import sys


def load_service(name: str):
    root = Path(__file__).resolve().parents[1] / "services"
    if name not in {directory.name for directory in root.iterdir() if directory.is_dir()}:
        raise ValueError("Unknown service")
    directory = root / name / "app"
    package = "edu_" + name.replace("-", "_")
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(package, directory / "__init__.py", submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    return importlib.import_module(package + ".main")
