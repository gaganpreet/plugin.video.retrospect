#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import sys

import xbmc
import xbmcgui

# we need to import the initializer
addOnPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(addOnPath)

# setup some initial stuff
from initializer import Initializer
Initializer.set_unicode()
Initializer.setup_python_paths()
sys.path.remove(addOnPath)

from config import Config
from logger import Logger
Logger.CreateLogger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                    Config.appName,
                    append=True,
                    dualLogger=lambda x, y=4: xbmc.log(x, y))

from helpers.htmlentityhelper import HtmlEntityHelper
from addonsettings import AddonSettings, LOCAL
from favourites import Favourites
from paramparser import ParameterParser
from helpers.channelimporter import ChannelIndex
from helpers.languagehelper import LanguageHelper
from locker import LockWithDialog
from cloaker import Cloaker
from xbmcwrapper import XbmcWrapper
Logger.Instance().minLogLevel = AddonSettings.GetLogLevel()


class Menu(ParameterParser):

    def __init__(self, action):
        Logger.Info("**** Starting menu '%s' for %s add-on version %s ****",
                    action, Config.appName, Config.version)

        # noinspection PyUnresolvedReferences
        self.kodiItem = sys.listitem

        params = self.kodiItem.getPath()
        if not params:
            self.channelObject = None
            return

        name, params = params.split("?", 1)
        params = "?{0}".format(params)

        # Main constructor parses
        super(Menu, self).__init__(name, params)

        self.channelObject = self.__get_channel()
        Logger.Debug("Plugin Params: %s (%s)\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params), self.pluginName, params)

        if self.keywordPickle in self.params:
            self.mediaItem = self._pickler.DePickleMediaItem(self.params[self.keywordPickle])
        else:
            self.mediaItem = None

    def hide_channel(self):
        """ Hides a specific channel """

        Logger.Info("Hiding channel: %s", self.channelObject)
        AddonSettings.SetChannelVisiblity(self.channelObject, False)
        self.refresh()

    def select_channels(self):
        """ Selects the channels that should be visible.

        @return: None
        """

        valid_channels = ChannelIndex.get_register().get_channels(include_disabled=True)
        channels_to_show = filter(lambda c: c.visible, valid_channels)

        selected_channels = filter(lambda c: c.enabled, channels_to_show)
        selected_indices = map(lambda c: channels_to_show.index(c), selected_channels)
        Logger.Debug("Currently selected channels: %s", selected_indices)

        channel_to_show_names = map(lambda c: HtmlEntityHelper.convert_html_entities(c.channelName),
                                    channels_to_show)

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.get_localized_string(LanguageHelper.ChannelSelection)[:-1]
        selected_channels = dialog.multiselect(heading, channel_to_show_names,
                                               preselect=selected_indices)
        if selected_channels is None:
            return

        selected_channels = list(selected_channels)
        Logger.Debug("New selected channels:       %s", selected_channels)

        indices_to_remove = filter(lambda i: i not in selected_channels, selected_indices)
        indices_to_add = filter(lambda i: i not in selected_indices, selected_channels)
        for i in indices_to_remove:
            Logger.Info("Hiding channel: %s", channels_to_show[i])
            AddonSettings.SetChannelVisiblity(channels_to_show[i], False)
            pass

        for i in indices_to_add:
            Logger.Info("Showing channel: %s", channels_to_show[i])
            AddonSettings.SetChannelVisiblity(channels_to_show[i], True)

        self.refresh()
        return

    def show_country_settings(self):
        """ Shows the country settings page where channels can be shown/hidden based on the
        country of origin. """

        if AddonSettings.is_min_version(18):
            AddonSettings.ShowSettings(-99)
        else:
            AddonSettings.ShowSettings(101)
        self.refresh()

    def show_settings(self):
        """ Shows the add-on settings page and refreshes when closing it. """

        AddonSettings.ShowSettings()
        self.refresh()

    def channel_settings(self):
        """ Shows the channel settings for the selected channel. Refreshes the list after closing
        the settings. """

        AddonSettings.ShowChannelSettings(self.channelObject)
        self.refresh()

    def favourites(self, all_favorites=False):
        """ Shows the favourites, either for a channel or all that are known.

        @param all_favorites: if True the list will return all favorites. Otherwise it will only
                              only return the channel ones.

        """

        # it's just the channel, so only add the favourites
        cmd_url = self._CreateActionUrl(
            None if all_favorites else self.channelObject,
            action=self.actionAllFavourites if all_favorites else self.actionFavourites
        )

        xbmc.executebuiltin("XBMC.Container.Update({0})".format(cmd_url))

    @LockWithDialog(logger=Logger.Instance())
    def add_favourite(self):
        """ Adds the selected item to the favourites. The opens the favourite list. """

        # remove the item
        item = self._pickler.DePickleMediaItem(self.params[self.keywordPickle])
        # no need for dates in the favourites
        # item.ClearDate()
        Logger.Debug("Adding favourite: %s", item)

        f = Favourites(Config.favouriteDir)
        if item.IsPlayable():
            action = self.actionPlayVideo
        else:
            action = self.actionListFolder

        # add the favourite
        f.Add(self.channelObject,
              item,
              self._CreateActionUrl(self.channelObject, action, item))

        # we are finished, so just open the Favorites
        self.favourites()

    @LockWithDialog(logger=Logger.Instance())
    def remove_favourite(self):
        """ Remove the selected favourite and then refresh the favourite list. """

        # remove the item
        item = self._pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Debug("Removing favourite: %s", item)
        f = Favourites(Config.favouriteDir)
        f.Remove(item)

        # refresh the list
        self.refresh()

    def refresh(self):
        """ Refreshes the current Kodi list """
        xbmc.executebuiltin("XBMC.Container.Refresh()")

    def toggle_cloak(self):
        """ Toggles the cloaking (showing/hiding) of the selected folder. """

        item = self._pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Info("Cloaking current item: %s", item)
        c = Cloaker(self.channelObject, AddonSettings.store(LOCAL), logger=Logger.Instance())

        if c.IsCloaked(item.url):
            c.UnCloak(item.url)
            self.refresh()
            return

        first_time = c.Cloak(item.url)
        if first_time:
            XbmcWrapper.ShowDialog(LanguageHelper.get_localized_string(LanguageHelper.CloakFirstTime),
                                   LanguageHelper.get_localized_string(LanguageHelper.CloakMessage))

        del c
        self.refresh()

    def set_bitrate(self):
        """ Sets the bitrate for the selected channel via a specific dialog. """

        if self.channelObject is None:
            raise ValueError("Missing channel")

        # taken from the settings.xml
        bitrate_options = "Retrospect|100|250|500|750|1000|1500|2000|2500|4000|8000|20000"\
            .split("|")

        current_bitrate = AddonSettings.GetMaxChannelBitrate(self.channelObject)
        Logger.Debug("Found bitrate for %s: %s", self.channelObject, current_bitrate)
        current_bitrate_index = 0 if current_bitrate not in bitrate_options \
            else bitrate_options.index(current_bitrate)

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.get_localized_string(LanguageHelper.BitrateSelection)
        selected_bitrate = dialog.select(heading, bitrate_options,
                                         preselect=current_bitrate_index)
        if selected_bitrate < 0:
            return

        Logger.Info("Changing bitrate for %s from %s to %s",
                    self.channelObject,
                    bitrate_options[current_bitrate_index],
                    bitrate_options[selected_bitrate])

        AddonSettings.SetMaxChannelBitrate(self.channelObject,
                                           bitrate_options[selected_bitrate])
        return

    def __get_channel(self):
        chn = self.params.get(self.keywordChannel, None)
        code = self.params.get(self.keywordChannelCode, None)
        if not chn:
            return None

        Logger.Debug("Fetching channel %s - %s", chn, code)
        channel = ChannelIndex.get_register().get_channel(chn, code, info_only=True)
        Logger.Debug("Created channel: %s", channel)
        return channel

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            Logger.Critical("Error in menu handling: %s", exc_val.message, exc_info=True)

        # make sure we leave no references behind
        AddonSettings.clear_cached_addon_settings_object()
        # close the log to prevent locking on next call
        Logger.Instance().CloseLog()
        return False
