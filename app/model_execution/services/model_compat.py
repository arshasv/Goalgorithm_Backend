import pickle
import importlib
import warnings

_MODULE_ALIASES = {
    "_loss": "sklearn._loss",
    "sklearn.metrics._loss": "sklearn._loss._loss",
}

_FALLBACK_CHAINS = {
    "_loss": ["sklearn._loss.loss", "sklearn._loss._loss", "sklearn._loss"],
    "sklearn.metrics._loss": ["sklearn._loss._loss", "sklearn._loss.loss"],
}

class CompatUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except ModuleNotFoundError:
            if module in _MODULE_ALIASES:
                try:
                    actual = _MODULE_ALIASES[module]
                    return super().find_class(actual, name)
                except (ModuleNotFoundError, AttributeError):
                    pass
            if module in _FALLBACK_CHAINS:
                for candidate in _FALLBACK_CHAINS[module]:
                    try:
                        return super().find_class(candidate, name)
                    except (ModuleNotFoundError, AttributeError):
                        continue
            raise


def safe_load(file_obj):
    return CompatUnpickler(file_obj).load()
