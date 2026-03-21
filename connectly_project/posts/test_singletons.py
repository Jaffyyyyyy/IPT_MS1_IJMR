from django.test import TestCase
from singletons.config_manager import ConfigManager
from singletons.logger_singleton import LoggerSingleton


class ConfigManagerSingletonTestCase(TestCase):
    """Verify ConfigManager follows the Singleton pattern."""

    def test_same_instance(self):
        """Two instantiations return the exact same object."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2)

    def test_shared_state(self):
        """Mutations via one reference are visible through the other."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        config1.set_setting("DEFAULT_PAGE_SIZE", 50)
        self.assertEqual(config2.get_setting("DEFAULT_PAGE_SIZE"), 50)
        # Reset to default so other tests are unaffected
        config1.set_setting("DEFAULT_PAGE_SIZE", 20)


class LoggerSingletonTestCase(TestCase):
    """Verify LoggerSingleton follows the Singleton pattern."""

    def test_same_instance(self):
        """Two instantiations return the exact same object."""
        logger1 = LoggerSingleton()
        logger2 = LoggerSingleton()
        self.assertIs(logger1, logger2)

    def test_logger_returns_same_logger(self):
        """get_logger() returns the same underlying logger."""
        log_a = LoggerSingleton().get_logger()
        log_b = LoggerSingleton().get_logger()
        self.assertIs(log_a, log_b)
