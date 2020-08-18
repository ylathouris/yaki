import dataclasses
import importlib.metadata
import re
from typing import Any, Dict, Generator, List, Optional, Tuple

import pkg_resources


def get_plugin(path: str):
    name = path.split(".")[0]
    return plugins(name).get(path)


def get_plugins(path: str):
    name = path.split(".")[0]
    return list(plugins(name).find(path))


def load_plugin(path: str) -> Any:
    name = path.split(".")[0]
    return plugins(name).load(path)


def plugins(name: str):
    return Plugins.create(name)


@dataclasses.dataclass()
class Plugin:
    """
    Plugin

    This class represents a plugin.
    """

    group: str
    entrypoint: pkg_resources.EntryPoint

    @property
    def name(self) -> str:
        return self.entrypoint.name

    @property
    def path(self) -> str:
        return f"{self.group}.{self.name}"

    @property
    def module(self) -> str:
        return self.entrypoint.module_name

    @property
    def dist(self) -> pkg_resources.Distribution:
        return self.entrypoint.dist  # type: ignore

    @property
    def package(self) -> str:
        return self.dist.project_name

    @property
    def version(self) -> str:
        return self.dist.version

    @property
    def author(self) -> str:
        meta = importlib.metadata.metadata(self.package)
        name = meta["Author"]
        mail = meta["Author-email"]
        return f"{name} <{mail}>"

    def load(self, *args, **kwargs) -> Any:
        """
        Load plugin

        Load the plugin and return the result.
        """
        return self.entrypoint.load(*args, **kwargs)

    def __repr__(self) -> str:
        return f"Plugin({self.path})"


class Plugins:
    """
    Plugins

    This class represents a set of plugins for a package.
    """

    NAME_PATTERN = "^[a-z_][a-z0-9_]{1,50}$"

    @classmethod
    def create(cls, name: str):
        cls.validate_package_name(name)
        try:
            dist = pkg_resources.get_distribution(name)
        except pkg_resources.DistributionNotFound as err:
            raise ValueError(f"Cannot find packge: {name}")

        return cls(dist)

    @classmethod
    def validate_package_name(cls, name):
        match = re.match(cls.NAME_PATTERN, name)
        if not match:
            raise ValueError(f"Invalid package name: {name}")

    def __init__(self, dist) -> None:
        self.dist = dist

    @property
    def name(self) -> str:
        return self.dist.project_name

    @property
    def version(self):
        return self.dist.version

    @property
    def groups(self) -> List[str]:
        entries = self.dist.get_entry_map()
        return [i for i in entries if i.startswith(self.name)]

    def parse(self, path: str, filler: bool = False) -> Tuple[str, str]:
        """
        Parse plugin path

        Split the given plugin path into parts and return each part.
        """
        parts = path.split(".")
        if parts[:1] == [self.name]:
            parts.pop(0)

        if filler:
            multiplier = 2 - len(parts)
            parts += list("*" * multiplier)

        if len(parts) < 2:
            msg = f"Invalid plugin path: {path}"
            raise ValueError(msg)

        plugin = parts.pop()
        group = self.name + "." + ".".join(parts)

        return group, plugin

    def get(self, path: str) -> Optional[Plugin]:
        """
        Get plugin

        Get plugin with the given path.
        """
        group, name = self.parse(path)
        plugin = self._get(group, name)
        return plugin

    def _get(self, group: str, name: str) -> Optional[Plugin]:
        plugin = None
        entrypoint = self.dist.get_entry_info(group, name)
        if entrypoint:
            plugin = Plugin(group, entrypoint)

        return plugin

    def find(self, pattern: str) -> List[Plugin]:
        """
        Find plugins

        Find plugins that match the given pattern.
        """
        group, name = self.parse(pattern, filler=True)
        return list(self._find(group, name))

    def _find(self, group_pattern: str, name_pattern: str) -> Generator:
        group_regex = self._regexify(group_pattern)
        name_regex = self._regexify(name_pattern)
        entries = self.dist.get_entry_map()
        for group, entrypoints in self._match(entries, group_regex):
            for name, _ in self._match(entrypoints, name_regex):
                yield self._get(group, name)

    def _match(self, items: Dict, regex: re.Pattern) -> Generator:
        for key, value in items.items():
            match = regex.match(key)
            if match:
                yield key, value

    @staticmethod
    def _regexify(path: str) -> re.Pattern:
        pattern = path.replace(".", "\\.").replace("*", ".+")
        return re.compile(pattern)

    def load(self, path: str) -> Any:
        """
        Load plugin

        Load plugin with the given path.
        """
        plugin = self.get(path)
        if not plugin:
            raise ValueError(f"Cannot find plugin: {path}")

        return plugin.load()
