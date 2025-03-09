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
        use_temp_dir = self.builder.get_object("use_temp_dir")
        temp_dir = self.builder.get_object("temp_dir")
        
        # Connect signals
        use_target_dir.connect("clicked", lambda x: self.on_target_change(True))
        extract_in_place.connect("clicked", lambda x: self.on_target_change(False))
        extract_torrent_root.connect("clicked", lambda x: self.on_target_change(False))
        auto_cleanup.connect("toggled", lambda x: self.on_auto_clean_change(auto_cleanup.get_active()))
        auto_cleanup.connect("toggled", self.on_auto_clean_changed)
        use_temp_dir.connect("toggled", lambda x: self.on_temp_dir_change(use_temp_dir.get_active()))
        
        # Register the force extract menu item
        self.add_context_menu()
        
        # Register for preference page
        self.plugin.register_hook('on_apply_prefs', self.on_apply_prefs)
        self.plugin.register_hook('on_show_prefs', self.on_show_prefs)
        
        # Register for torrent menu hook
        self.plugin.register_hook('on_torrent_menu_items', self.on_torrent_menu_items)
        
        self.on_show_prefs()

    def disable(self):
        component.get('Preferences').remove_page(_('ExtractorPlus'))
        self.plugin.deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        self.plugin.deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )
        self.plugin.deregister_hook(
            'on_torrent_menu_items', self.on_torrent_menu_items
        )
        
        # Deregister from torrent selection changes
        try:
            component.get("TorrentView").deregister_selection_callback(self._on_torrent_selection_changed)
        except Exception as e:
            log.error(f"Error deregistering selection callback: {e}")
        
        # Remove the menu item
        if hasattr(self, 'menu_item'):
            try:
                component.get('MenuBar').torrentmenu.remove(self.menu_item)
                self.menu_item = None
            except Exception as e:
                log.error(f"Error removing menu item: {e}")
            
        del self.builder

    def on_apply_prefs(self):
        log.debug('applying prefs for ExtractorPlus')
        if client.is_localhost():
            path = self.builder.get_object('folderchooser_path').get_filename()
        else:
            path = self.builder.get_object('extract_path').get_text()

        try:
            cleanup_time = int(self.builder.get_object('cleanup_time').get_text())
            if cleanup_time < 1:
                cleanup_time = 1
        except ValueError:
            cleanup_time = 2
            
        try:
            max_threads = int(self.builder.get_object('max_extract_threads').get_text())
            if max_threads < 1:
                max_threads = 1
        except ValueError:
            max_threads = 2

        config = {
            'extract_path': path,
            'extract_selected_folder': self.builder.get_object("extract_selected_folder").get_active(),
            'extract_in_place': self.builder.get_object("extract_in_place").get_active(),
            'extract_torrent_root': self.builder.get_object("extract_torrent_root").get_active(),
            'label_filter': self.builder.get_object("label_filter").get_text(),
            'use_temp_dir': self.builder.get_object("use_temp_dir").get_active(),
            'temp_dir': self.builder.get_object("temp_dir").get_text(),
            'append_matched_label': self.builder.get_object("append_matched_label").get_active(),
            'cleanup_time': cleanup_time,
            'auto_cleanup': self.builder.get_object("auto_cleanup").get_active(),
            'append_archive_name': self.builder.get_object('append_archive_name').get_active(),
            'max_extract_threads': max_threads
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

            # Setup temp directory field
            self.builder.get_object('temp_dir').set_text(config.get('temp_dir', ''))
            self.builder.get_object('temp_dir').set_sensitive(config.get('use_temp_dir', True))
            
            # Setup max threads field
            self.builder.get_object('max_extract_threads').set_text(str(config.get('max_extract_threads', 2)))
            
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

    def on_temp_dir_change(self, is_active):
        """Enable or disable the temp directory field based on the checkbox"""
        self.builder.get_object('temp_dir').set_sensitive(is_active)

    def add_context_menu(self):
        """Add the 'Force Extract' context menu item to the torrent menu"""
        log.debug("Adding force extract menu item")
        torrentmenu = component.get('MenuBar').torrentmenu
        self.menu_item = Gtk.MenuItem(label=_('Force Extract'))
        self.menu_item.connect('activate', self._on_menu_force_extract)
        self.menu_item.show()
        torrentmenu.append(self.menu_item)
        
        # Register for updates on torrent selection
        component.get("TorrentView").register_selection_callback(self._on_torrent_selection_changed)
        
    def _on_torrent_selection_changed(self, torrentids):
        """Called when torrent selection changes to update menu sensitivity"""
        if hasattr(self, "menu_item"):
            if torrentids:
                self.menu_item.set_sensitive(True)
            else:
                self.menu_item.set_sensitive(False)
        
    def _on_menu_force_extract(self, widget):
        """Handler for Force Extract context menu"""
        # Get selected torrents
        selected = component.get("TorrentView").get_selected_torrents()
        if selected:
            for torrent_id in selected:
                log.info(f"Force extracting {torrent_id}")
                client.extractorplus.force_extract(torrent_id)
                
    def on_torrent_menu_items(self, menu, selected_torrent_ids):
        """This is kept for compatibility with other hooks but not used"""
        pass
