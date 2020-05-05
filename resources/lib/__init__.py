# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import sys

lib_dir = os.path.dirname(__file__)

sys.path.append(os.path.join(lib_dir, 'pysrt') )
sys.path.append(os.path.join(lib_dir, 'translate'))

__all__ = ["addon", "addonsettings", "backtothefuture", "channelinfo", "chn_class", "cloaker",
           "contextmenu", "envcontroller", "environments", "favourites", "initializer", "locker",
           "logger", "mediaitem", "menu", "parserdata", "pickler", "plugin",
           "proxyinfo", "regexer", "retroconfig", "translate", "updater", "urihandler", "vault", "version",
           "xbmcwrapper", "player"]
