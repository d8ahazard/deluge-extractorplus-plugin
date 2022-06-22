# -*- coding: utf-8 -*-
# Copyright (C) 2019-2022 Digitalhigh <donate.to.digitalhigh@gmail.com>
#
# Based on Simple Extractor and Extractor Plugins:
# Copyright (C) 2015 Chris Yereaztian <chris.yereaztian@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of the Extractor Plus plugin and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402

# isort:imports-thirdparty
from gi.repository import Gtk

# isort:imports-firstparty
import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

# isort:imports-localfolder
from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.plugin = component.get('PluginManager')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('extractorplus_prefs.ui'))

        component.get('Preferences').add_page(
            _('Extractor Plus'), self.builder.get_object('extractor_prefs_box')
        )
        use_target_dir = self.builder.get_object("extract_selected_folder")
        extract_in_place = self.builder.get_object("extract_in_place")
        append_dest_label = self.builder.get_object("append_matched_label")
        extract_torrent_root = self.builder.get_object("extract_torrent_root")
        auto_cleanup = self.builder.get_object("auto_cleanup")
        auto_cleanup_time = self.builder.get_object("auto_cleanup_time")
        auto_cleanup.connect("clicked", lambda x: self.on_auto_clean_changed())
        use_target_dir.connect("clicked", lambda x: self.on_target_change(True))
        extract_in_place.connect("clicked", lambda x: self.on_target_change(False))
        extract_torrent_root.connect("clicked", lambda x: self.on_target_change(False))
        self.plugin.register_hook('on_apply_prefs', self.on_apply_prefs)
        self.plugin.register_hook('on_show_prefs', self.on_show_prefs)
        self.on_show_prefs()

    def disable(self):
        component.get('Preferences').remove_page(_('Extractor Plus'))
        self.plugin.deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        self.plugin.deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )
        del self.builder

    def on_apply_prefs(self):
        log.debug('applying prefs for Extractor Plus')
        if client.is_localhost():
            path = self.builder.get_object('folderchooser_path').get_filename()
        else:
            path = self.builder.get_object('extract_path').get_text()

        cleanup_time = self.builder.get_object('cleanup_time').get_text()
        use_selected = self.builder.get_object("extract_selected_folder").get_active()
        self.on_target_change(use_selected)

        config = {
            'extract_path': path,
            'extract_selected_folder': self.builder.get_object("extract_selected_folder").get_active(),
            'extract_in_place': self.builder.get_object("extract_in_place").get_active(),
            'extract_torrent_root': self.builder.get_object("extract_torrent_root").get_active(),
            'label_filter': self.builder.get_object("label_filter").get_text(),
            'use_temp_dir': self.builder.get_object("use_temp_dir").get_active(),
            'append_matched_label': self.builder.get_object("append_matched_label").get_active(),
            'cleanup_time': cleanup_time,
            'auto_cleanup': self.builder.get_object("auto_cleanup").get_active(),
            'append_archive_name': self.builder.get_object('append_archive_name').get_active()
        }

        client.extractorplus.set_config(config)

    def on_show_prefs(self):
        def on_get_config(config):
            if client.is_localhost():
                self.builder.get_object('folderchooser_path').set_current_folder(config['extract_path'])
                self.builder.get_object('folderchooser_path').show()
                self.builder.get_object('extract_path').hide()
            else:
                self.builder.get_object('extract_path').set_text(config['extract_path'])
                self.builder.get_object('folderchooser_path').hide()
                self.builder.get_object('extract_path').show()

            use_selected = config['extract_selected_folder']
            cleanup_time = config['cleanup_time']
            auto_cleanup = config['auto_cleanup']
            append_archive_name = config['append_archive_name']
            self.on_target_change(use_selected)
            self.builder.get_object('auto_cleanup').set_active(auto_cleanup)
            self.builder.get_object('append_archive_name').set_active(append_archive_name)
            self.builder.get_object('cleanup_time').set_text(str(cleanup_time))
            self.on_auto_clean_change(auto_cleanup)
            self.builder.get_object('extract_selected_folder').set_active(
                use_selected
            )
            self.builder.get_object('extract_torrent_root').set_active(
                config['extract_torrent_root']
            )
            self.builder.get_object('extract_in_place').set_active(
                config['extract_in_place']
            )
            self.builder.get_object('label_filter').set_text(config['label_filter'])
            self.builder.get_object('use_temp_dir').set_active(config['use_temp_dir'])
            self.builder.get_object('append_matched_label').set_active(config['append_matched_label'])

        client.extractorplus.get_config().addCallback(on_get_config)

    def on_target_change(self, show):
        if show:
            self.builder.get_object('destination_frame').show()
            self.builder.get_object('append_matched_label').show()
        else:
            self.builder.get_object('destination_frame').hide()
            self.builder.get_object('append_matched_label').hide()

    def on_auto_clean_change(self, show):
        if show:
            self.builder.get_object('cleanup_time_box').show()
        else:
            self.builder.get_object('cleanup_time_box').hide()

    def on_auto_clean_changed(self):
        show = self.builder.get_object("auto_cleanup").get_active()
        if show:
            self.builder.get_object('cleanup_time_box').show()
        else:
            self.builder.get_object('cleanup_time_box').hide()
