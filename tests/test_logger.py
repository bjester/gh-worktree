import logging
from unittest import TestCase

from treefort.logger import ColorFormatter


class ColorFormatterTestCase(TestCase):
    def test_does_not_prefix_message_for_base_logger_namespace(self):
        formatter = ColorFormatter(
            "%(message)s",
            use_color=False,
            base_logger_name="treefort",
        )
        record = logging.LogRecord(
            name="treefort.gh",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        self.assertEqual(formatter.format(record), "hello")

    def test_prefixes_message_for_external_logger(self):
        formatter = ColorFormatter(
            "%(message)s",
            use_color=False,
            base_logger_name="treefort",
        )
        record = logging.LogRecord(
            name="urllib3.connectionpool",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        self.assertEqual(formatter.format(record), "urllib3.connectionpool | hello")
