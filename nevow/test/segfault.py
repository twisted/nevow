#!/usr/bin/python

"""
Generate an unhandled SIGSEGV for this process immediately upon import.

@see: L{nevow.test.test_testutil.JavaScriptTests.test_signalledExit}.
"""

import os, signal

os.kill(os.getpid(), signal.SIGSEGV)
