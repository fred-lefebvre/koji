import os
import sys
import unittest

import StringIO as stringio

import mock

import loadcli
cli = loadcli.cli


class TestListCommands(unittest.TestCase):

    def setUp(self):
        self.options = mock.MagicMock()
        self.session = mock.MagicMock()
        self.args = mock.MagicMock()
        self.original_parser = cli.OptionParser
        cli.OptionParser = mock.MagicMock()
        self.parser = cli.OptionParser.return_value

    def tearDown(self):
        cli.OptionParser = self.original_parser

    # Show long diffs in error output...
    maxDiff = None

    @mock.patch('sys.stdout', new_callable=stringio.StringIO)
    def test_list_commands(self, stdout):
        cli.list_commands()
        actual = stdout.getvalue()
        actual = actual.replace('nosetests', 'koji')
        filename = os.path.dirname(__file__) + '/data/list-commands.txt'
        with open(filename, 'rb') as f:
            expected = f.read().decode('ascii')
        self.assertMultiLineEqual(actual, expected)

    @mock.patch('sys.stdout', new_callable=stringio.StringIO)
    def test_handle_admin_help(self, stdout):
        options, arguments = mock.MagicMock(), mock.MagicMock()
        options.admin = True
        self.parser.parse_args.return_value = [options, arguments]
        cli.handle_help(self.options, self.session, self.args)
        actual = stdout.getvalue()
        actual = actual.replace('nosetests', 'koji')
        filename = os.path.dirname(__file__) + '/data/list-commands-admin.txt'
        with open(filename, 'rb') as f:
            expected = f.read().decode('ascii')
        self.assertMultiLineEqual(actual, expected)
