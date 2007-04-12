# -*- test-case-name: nevow.test.test_athena -*-

"""
twistd subcommand plugin for launching an athena widget server.
"""

from twisted.scripts.mktap import _tapHelper

widgetServiceMaker = _tapHelper(
    "Widget Mathingwhathuh",
    "nevow._widget_plugin",
    """
    Create a service which starts a NevowSite with a single page with a single
    widget.
    """,
    "athena-widget")
