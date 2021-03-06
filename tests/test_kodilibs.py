# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import unittest


class TestKodiLibs(unittest.TestCase):
    def test_calling_id(self):
        import xbmcaddon
        a = xbmcaddon.Addon()
        add_on_id = a.getAddonInfo("id")
        self.assertEqual("plugin.video.retrospect", add_on_id)

    def test_other_id(self):
        import xbmcaddon
        a = xbmcaddon.Addon("plugin.video.youtube")
        add_on_id = a.getAddonInfo("id")
        self.assertEqual("plugin.video.youtube", add_on_id)
