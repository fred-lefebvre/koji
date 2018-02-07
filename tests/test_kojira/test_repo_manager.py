from __future__ import absolute_import
import mock
import time
import unittest

import koji

from . import loadkojira
kojira = loadkojira.kojira


class OurException(Exception):
    pass


class RepoManagerTest(unittest.TestCase):

    def setUp(self):
        self.session = mock.MagicMock()
        self.options = mock.MagicMock()
        self.mgr = kojira.RepoManager(self.options, self.session)

    def tearDown(self):
        mock.patch.stopall()

    def test_check_tasks_none(self):
        self.mgr.tasks = {}
        self.mgr.other_tasks = {}
        self.session.listTasks.return_value = []

        self.mgr.checkTasks()

        self.session.getTaskInfo.assert_not_called()
        self.assertEqual(self.mgr.tasks, {})
        self.assertEqual(self.mgr.other_tasks, {})

    def test_check_tasks_other(self):
        self.mgr.tasks = {}
        self.mgr.other_tasks = {}
        self.session.listTasks.return_value = [
                {
                    'id': 1294,
                    'method': 'newRepo',
                    'state': 0,
                    'waiting': None,
                },
            ]
        self.mgr.logger = mock.MagicMock()
        self.mgr.checkTasks()

        self.session.getTaskInfo.assert_not_called()
        self.assertEqual(self.mgr.tasks, {})
        self.assertEqual(len(self.mgr.other_tasks), 1)
        self.mgr.logger.info.assert_called_once()

        # the extra task should not be logged if we run again
        self.mgr.logger.reset_mock()
        self.mgr.checkTasks()
        self.mgr.logger.info.assert_not_called()

    def test_check_tasks_ours(self):
        tasks = [
                {'id': 101, 'state': koji.TASK_STATES['FREE']},
                {'id': 102, 'state': koji.TASK_STATES['OPEN']},
                {'id': 103, 'state': koji.TASK_STATES['CLOSED']},
                {'id': 104, 'state': koji.TASK_STATES['CANCELED']},
                {'id': 105, 'state': koji.TASK_STATES['FAILED']},
            ]
        task_idx = dict([(t['id'], t) for t in tasks])
        order = []
        def getTaskInfo(task_id):
            # record the order of calls in multicall
            order.append(task_id)
        def multiCall(strict):
            return [[task_idx[tid]] for tid in order]
        self.session.getTaskInfo.side_effect = getTaskInfo
        self.session.multiCall.side_effect = multiCall
        self.mgr.tasks = dict([
            (t['id'], {'taskinfo': t, 'tag_id': 'TAG'})
                for t in tasks])
        self.mgr.other_tasks = {}
        self.session.listTasks.return_value = []

        self.mgr.checkTasks()
        # should have removed the close tasks
        self.assertEqual(self.mgr.tasks.keys(), [101, 102])

    @mock.patch('time.sleep')
    def test_regen_loop(self, sleep):
        subsession = mock.MagicMock()
        self.mgr.regenRepos = mock.MagicMock()
        self.mgr.regenRepos.side_effect = [None] * 10 + [OurException()]
        # we need the exception to terminate the infinite loop

        with self.assertRaises(OurException):
            self.mgr.regenLoop(subsession)

        self.assertEqual(self.mgr.regenRepos.call_count, 11)
        subsession.logout.assert_called_once()

    def test_set_tag_score(self):
        self.mgr.tagUseStats = mock.MagicMock()
        self.mgr.tagUseStats.return_value = {
                'n_recent': 5
                }
        self.mgr.needed_tags = {}
        entry = {
                'taginfo': {
                    'id': 'TAGID',
                    'name': 'TAGNAME',
                    },
                'expire_ts': time.time() - 300
                }
        self.mgr.setTagScore(entry)
        score = entry['score']
        if score < 0.0:
            raise Exception('score too low')

        _entry = entry.copy()
        _entry['expire_ts'] -= 300
        self.mgr.setTagScore(_entry)
        if score > entry['score']:
            raise Exception('score should have increased')

        self.mgr.tagUseStats.return_value = {
                'n_recent': 10
                # higher than before
                }
        self.mgr.setTagScore(entry)
        if score > entry['score']:
            raise Exception('score should have increased')
