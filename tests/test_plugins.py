
from unittest import mock

import pkg_resources
import pytest

import yaki


class TestPlugins:
    """
    Test Plugins

    Tests for creating an instance of the yaki plugins utility.
    """

    def test_gets_package_distribution(self, mockgetdist):
        yaki.plugins("foo")

        mockgetdist.assert_called_once_with("foo")

    def test_returns_expected_for_valid_package(self, mockgetdist):
        mockdist = mock.MagicMock()
        mockdist.project_name = "mypackage"
        mockdist.version = "1.2.3"
        mockgetdist.return_value = mockdist

        plugins = yaki.plugins("mypackage")

        assert isinstance(plugins, yaki.Plugins)
        assert plugins.name == "mypackage"
        assert plugins.version == "1.2.3"

    def test_raises_value_error_for_invalid_package(self, mockgetdist):
        mockgetdist.side_effect = pkg_resources.DistributionNotFound
        with pytest.raises(ValueError):
            yaki.plugins("nonsense")

    @pytest.mark.parametrize("path", ["*", "123abc", "0", "", "."])
    def test_raises_value_error_for_invalid_package_name(self, path):
        with pytest.raises(ValueError):
            yaki.plugins(path)


class TestGetPluginGroups:
    """
    Test Get Plugin Groups

    Tests for getting the available plugin groups for a package.
    """

    def test_returns_expected_for_valid_package(self, mockgetdist):
        entries = {
            "console_scripts": {},
            "mypackage.readers": {},
            "mypackage.image.formats": {}
        }
        mockdist = mock.MagicMock()
        mockdist.project_name = "mypackage"
        mockdist.get_entry_map.return_value = entries
        mockgetdist.return_value = mockdist

        plugins = yaki.plugins("mypackage")

        assert plugins.groups == list(entries.keys())[1:]


class TestGetPlugin:
    """
    Test Get Plugin

    Tests for getting a plugin using yaki.
    """

    # Valid paths have three parts: ${package}.${group}.${name}
    # The first part is the name of the package the plugins belong to.
    # The second part is the name of the plugin group. The third part
    # is the name of the plugin itself. Each part is separated by a
    # period. However, the plugin group can contain periods.
    VALID_PATHS = [
        "mypackage.readers.yml",
        "mypackage.readers.csv",
        "mypackage.writers.yml",
        "mypackage.writers.csv",
        "mylib.types.date",
        "mylib.types.datetime",
        "mylib.types.email",
        "mylib.image.formats.jpg",
        "mylib.image.formats.png",
        "mylib.image.formats.tiff",
        "mylib.audio.formats.wav",
        "mylib.audio.formats.aiff",
        "mylib.video.formats.mov",
        "mylib.video.formats.mpeg",
        "myapp.middleware.auth",
        "myapp.middleware.json-logging",
        "myapp.backend.postgres",
        "myapp.backend.mysql",
        "foo.bar.baz",
        "package.group.group.group.group.name",
    ]

    # Invalid paths do not comply to the naming convention specified
    # above. These are paths that do not contain all three parts OR
    # the first part (i.e. the package name) does not comply to the
    # package name convention.
    INVALID_PATHS = [
        "mypackage",
        "mypackage-readers-xml",
        "mypackage.readers-yml",
        "writers.xml",
        "writers-yml",
        "mypackage.csv-reader",
        "mypackage.*",
        "*",
        "*.*",
        "*.*.*",
        "*.*.*.*"
        "*.foo.bar",
        "*.foo.*",
        "*.*.bar",
        "foo.*",
        "group.name"
    ]

    @pytest.mark.parametrize("path", VALID_PATHS)
    def test_returns_plugin_when_plugin_exists(self, path, mockgetdist):
        entrypoint = mock.MagicMock()
        mockdist = mock.MagicMock()
        mockdist.get_entry_info.return_value = entrypoint
        mockgetdist.return_value = mockdist

        plugin = yaki.get_plugin(path)

        assert isinstance(plugin, yaki.Plugin)
        assert plugin.entrypoint == entrypoint

    @pytest.mark.parametrize("path", VALID_PATHS)
    def test_returns_none_when_plugin_does_not_exist(self, path, mockgetdist):
        mockdist = mock.MagicMock()
        mockdist.get_entry_info.return_value = None
        mockgetdist.return_value = mockdist

        plugin = yaki.get_plugin(path)

        assert plugin is None

    @pytest.mark.parametrize("path", INVALID_PATHS)
    def test_raises_value_error_with_invalid_path(self, path, mockgetdist):
        mockdist = mock.MagicMock()
        mockdist.project_name = path.split(".")[0]
        mockgetdist.return_value = mockdist
        with pytest.raises(ValueError):
            yaki.get_plugin(path)


class TestFindPlugins:
    """
    Test Find Plugins

    Tests for finding a set of plugins based on a given path.
    """

    @pytest.fixture(autouse=True)
    def wraps(self, mockgetdist):
        self.yml_reader = mock.MagicMock()
        self.yml_reader.name = "yml"
        self.csv_reader = mock.MagicMock()
        self.csv_reader.name = "csv"
        self.yml_writer = mock.MagicMock()
        self.yml_writer.name = "yml"
        self.csv_writer = mock.MagicMock()
        self.csv_writer.name = "yml"

        self.entries = {
            "mypackage.readers": {
                "yml": self.yml_reader,
                "csv": self.csv_reader,
            },
            "mypackage.writers": {
                "yml": self.yml_writer,
                "csv": self.csv_writer,
            }
        }

        def get_entry_info(group, name):
            return self.entries[group][name]

        mockdist = mock.MagicMock()
        mockdist.project_name = "mypackage"
        mockdist.get_entry_map.return_value = self.entries
        mockdist.get_entry_info.side_effect = get_entry_info
        mockgetdist.return_value = mockdist

    def test_returns_expected_with_full_path(self):
        plugins = yaki.get_plugins("mypackage.readers.yml")

        expected = [yaki.Plugin("mypackage.readers", self.yml_reader)]
        assert plugins == expected

    def test_returns_expected_with_name_wildcard(self):
        plugins = yaki.get_plugins("mypackage.writers")

        expected = [
            yaki.Plugin("mypackage.writers", self.yml_writer),
            yaki.Plugin("mypackage.writers", self.csv_writer),
        ]
        assert plugins == expected

    def test_returns_expected_with_group_wildcard(self):
        plugins = yaki.get_plugins("mypackage.*.yml")

        expected = [
            yaki.Plugin("mypackage.readers", self.yml_reader),
            yaki.Plugin("mypackage.writers", self.yml_writer),
        ]
        assert plugins == expected

    def test_returns_all_plugins_for_package_name(self):
        plugins = yaki.get_plugins("mypackage")

        expected = [
            yaki.Plugin("mypackage.readers", self.yml_reader),
            yaki.Plugin("mypackage.readers", self.csv_reader),
            yaki.Plugin("mypackage.writers", self.yml_writer),
            yaki.Plugin("mypackage.writers", self.csv_writer),
        ]
        assert plugins == expected

    def test_returns_empty_list_when_there_are_no_matches(self):
        plugins = yaki.get_plugins("mypackage.formats.yml")

        assert plugins == []


class TestLoadPlugin:
    """
    Test Load Plugin

    Tests for loading a plugin.
    """

    @pytest.fixture(autouse=True)
    def wraps(self, mockgetdist):
        self.entrypoint = mock.MagicMock()
        self.entrypoint.load.return_value = "loaded"
        self.entries = {"foo.bar": {"baz": self.entrypoint}}

        def get_entry_info(group, name):
            return self.entries.get(group, {}).get(name)

        mockdist = mock.MagicMock()
        mockdist.project_name = "foo"
        mockdist.get_entry_map.return_value = self.entries
        mockdist.get_entry_info.side_effect = get_entry_info
        mockgetdist.return_value = mockdist

    def test_loads_plugin_with_valid_path(self):
        loaded = yaki.load_plugin("foo.bar.baz")

        assert loaded == "loaded"

    def test_raises_value_error_with_invalid_path(self):
        with pytest.raises(ValueError):
            yaki.load_plugin("some.bogus.nonsense")


class TestPluginGroup:
    """
    Test Plugin Group

    Tests for the plugin group object.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.dist = mock.MagicMock()
        self.dist.project_name = "mypackage"
        self.dist.version = "1.2.3"

        self.entrypoint = mock.MagicMock()
        self.entrypoint.dist = self.dist
        self.entrypoint.name = "baz"
        self.entrypoint.module_name = "mymodule"

        entries = {"mypackage.foo.bar": {"baz": self.entrypoint}}
        self.dist.get_entry_map.return_value = entries

    def test_properties(self):
        group = yaki.PluginGroup("mypackage.foo.bar", self.dist)

        assert group.name == "mypackage.foo.bar"
        assert group.dist == self.dist

    def test_get_returns_expected_plugin_with_valid_name(self):
        group = yaki.PluginGroup("mypackage.foo.bar", self.dist)

        baz = group.get("baz")

        assert isinstance(baz, yaki.Plugin)
        assert baz.name == "baz"
        assert baz.path == "mypackage.foo.bar.baz"
        assert baz.entrypoint == self.entrypoint

    def test_get_returns_none_with_invalid_name(self):
        group = yaki.PluginGroup("mypackage.foo.bar", self.dist)

        assert group.get("nonsense") is None

    def test_load_valid_plugin_loads_plugin(self):
        group = yaki.PluginGroup("mypackage.foo.bar", self.dist)
        mockplugin = mock.MagicMock()
        mockplugin.load.return_value = "loaded"
        group.get = mock.MagicMock()
        group.get.return_value = mockplugin

        value = group.load("baz")

        assert value == "loaded"
        group.get.assert_called_once_with("baz")
        mockplugin.load.assert_called_once()

    def test_load_invalid_plugin_raises_value_error(self):
        group = yaki.PluginGroup("mypackage.foo.bar", self.dist)
        group.get = mock.MagicMock()
        group.get.return_value = None

        with pytest.raises(ValueError):
            group.load("nonsense")


class TestPlugin:
    """
    Test Plugin

    Tests for the plugin object.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        dist = mock.MagicMock()
        dist.project_name = "mypackage"
        dist.version = "1.2.3"

        entrypoint = mock.MagicMock()
        entrypoint.dist = dist
        entrypoint.name = "baz"
        entrypoint.module_name = "mymodule"
        self.entrypoint = entrypoint

    def test_properties(self, mockmetadata):
        plugin = yaki.Plugin("mypackage.foo.bar", self.entrypoint)

        assert plugin.name == "baz"
        assert plugin.group == "mypackage.foo.bar"
        assert plugin.version == "1.2.3"
        assert plugin.author == "Jane Doe <jane.doe@mail.com>"
        assert plugin.package == "mypackage"
        assert plugin.module == "mymodule"
        assert plugin.path == "mypackage.foo.bar.baz"

        mockmetadata.assert_called_once_with("mypackage")

    def test_object_representation(self):
        plugin = yaki.Plugin("mypackage.foo.bar", self.entrypoint)

        expected = "Plugin(mypackage.foo.bar.baz)"
        assert repr(plugin) == expected
