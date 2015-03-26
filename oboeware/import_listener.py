import sys

if sys.version_info >= (3, 1, 0):
    import collections
    import importlib

    class ListeningFinder:
        def __init__(self):
            self.searching = set()
            self.listeners = collections.defaultdict(list)

        def find_module(self, module_name, path=None):
            if module_name in self.searching:
                return
            self.searching.add(module_name)
            return ListeningLoader(self)

        def listen(self, module_name, on_load):
            self.listeners[module_name].append(on_load)

        def load(self, module_name, module):
            self.searching.remove(module_name)
            if module_name in self.listeners:
                for listener in self.listeners[module_name]:
                    listener(module)

    class ListeningLoader:
        def __init__(self, finder):
            self.finder = finder

        def load_module(self, module_name):
            module = importlib.import_module(module_name)
            self.finder.load(module_name, module)
            return module

    finder = ListeningFinder()
    sys.meta_path.insert(0, finder)

    def listen(module_name, on_load):
        finder.listen(module_name, on_load)

# Python 2
else:
    import imports

    def listen(module_name, on_load):
        imports.whenImported(module_name, on_load)
