import numpy as np
import importlib.util
import sys

from src.settings import SETTINGS


def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class ModelProxy:
    def __init__(self, model_name: str = None):
        if not model_name:
            self._enable = False
            return

        self._enable = True
        self.model_name = model_name

        # Load the Python Module containg the Model declaration
        self._module = load_module(
            f"{SETTINGS.AI_MODELS_FOLDER}{self.model_name}/model.py", "external_module"
        )
        self._model = self._module.Model()

    def infer(self, audios: list) -> np.ndarray:
        if not self._enable:
            return np.zeros(len(audios), dtype=int)

        predictions = self._model.infer(audios)
        return predictions
