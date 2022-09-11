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

import datetime
import errno
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from shutil import which
from threading import Thread

import deluge.component as component
import deluge.configmanager
import pkg_resources
from deluge.common import windows_check
from deluge.configmanager import ConfigManager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

from extractorplus.RepeatedTimer import RepeatedTimer

log = logging.getLogger(__name__)

DEFAULT_PREFS = {'extract_path': '',
                 'extract_in_place': False,
                 'extract_selected_folder': False,
                 'extract_torrent_root': True,
                 'use_temp_dir': True,
                 'append_matched_label': False,
                 'label_filter': '',
                 'auto_cleanup': False,
                 'cleanup_time': 2,
                 'extracted': []
                 }

EXTRACTED_FILES = {}
EXTRACT_COMMANDS = {}
EXTRA_COMMANDS = {}

if windows_check():
    egg_path = pkg_resources.resource_filename(__name__, "7z.exe")
    log.debug("Local path %s" % egg_path)
    win_7z_exes = [
        egg_path,
        '7z.exe',
        'C:\\Program Files\\7-Zip\\7z.exe',
        'C:\\Program Files (x86)\\7-Zip\\7z.exe'
    ]

    ext_7z = ['.r00', '.rar', '.zip', '.tar', '.7z', '.xz', '.lzma']
    # 7-zip on windows cannot extract tar.* with single command, so we do some pipe magic to one-shot it
    ext_tar = ['.tar.bz2', '.tbz', '.tar.xz', '.txz', '.tar.gz', '.tgz', '.tar.lzma', '.tlz']
    for win_7z_exe in win_7z_exes:
        if which(win_7z_exe):
            l1_cmds = [win_7z_exe, 'x', '-y', '-aoa']
            l1t_cmds = [win_7z_exe, 'x', '-y', '-so', '-aoa']
            l2_cmds = [win_7z_exe, 'x', '-y', '-ttar', '-si', '-aoa']
            log.debug("Found 7z: %s" % win_7z_exe)
            cmds = dict.fromkeys(ext_7z, l1_cmds)
            EXTRACT_COMMANDS = {**cmds, **dict.fromkeys(ext_tar, l1t_cmds)}
            EXTRA_COMMANDS = dict.fromkeys(ext_tar, l2_cmds)
            break

else:
    required_cmds = ['unrar', 'unzip', 'tar', '7zr']

    EXTRACT_COMMANDS = {
        '.rar': ['unrar', 'x', '-o+', '-y'],
        '.r00': ['unrar', 'x', '-o+', '-y'],
        '.tar': ['tar', '-xf'],
        '.zip': ['unzip'],
        '.tar.gz': ['tar', '-xzf'],
        '.tgz': ['tar', '-xzf'],
        '.tar.bz2': ['tar', '-xjf'],
        '.tbz': ['tar', '-xjf'],
        '.tar.lzma': ['tar', '--lzma', '-xf'],
        '.tlz': ['tar', '--lzma', '-xf'],
        '.tar.xz': ['tar', '-Jf'],
        '.txz': ['tar', '--xJf'],
        '.7z': ['7zr', 'x']
    }
    # Test command exists and if not, remove.
    for command in required_cmds:
        if not which(command):
            for k, v in list(EXTRACT_COMMANDS.items()):
                if command in v[0]:
                    log.warning('%s not found, disabling support for %s' % (command, k))
                    del EXTRACT_COMMANDS[k]

if len(EXTRACT_COMMANDS) == 0:
    raise Exception('No archive extracting programs found, plugin will be disabled.')


class Core(CorePluginBase):
    def __init__(self, plugin_name):
        super().__init__(plugin_name)
        self.EXTRACT_COUNT = 0
        self.EXTRACT_TOTAL = 0
        self.check_thread = None

    def enable(self):
        log.info("ExtractorPlus enabled.")
        self.config = deluge.configmanager.ConfigManager(
            'extractorplus.conf', DEFAULT_PREFS
        )
        if "auto_cleanup" not in self.config:
            self.config["auto_cleanup"] = False
            self.config.save()
        if "cleanup_time" not in self.config:
            self.config["cleanup_time"] = 2
            self.config.save()
        if self.config["cleanup_time"] < 1:
            self.config["cleanup_time"] = 1
            self.config.save()
        if not self.config['extract_path']:
            self.config['extract_path'] = deluge.configmanager.ConfigManager(
                'core.conf'
            )['download_location']
        self.check_thread = RepeatedTimer(30, self.check_cleanup)
        if self.config['auto_cleanup']:
            log.info("Starting check thread...")
            self.check_thread.start()
        else:
            try:
                self.check_thread.stop()
            except Exception as q:
                log.info("Exception stopping check thread: %s" % q)
        component.get('EventManager').register_event_handler(
            'TorrentFinishedEvent', self._on_torrent_finished
        )

    def disable(self):
        component.get('EventManager').deregister_event_handler(
            'TorrentFinishedEvent', self._on_torrent_finished
        )
        if self.check_thread is not None:
            log.info("Stopping check thread.")
            try:
                self.check_thread.stop()
            except Exception as ex:
                log.error("Exception stopping check thread: %s" % ex)

    def update(self):
        pass

    def check_cleanup(self):
        if not self.config['auto_cleanup']:
            return
        now = time.time()
        cleanup_time = self.config['cleanup_time']
        new_extracted = []
        extracted = self.config['extracted']
        save = False
        for f in extracted:
            if os.path.exists(f):
                file_time = os.path.getmtime(f)
                file_age = now - file_time
                if file_age / 3600 >= cleanup_time:
                    log.info("Auto-deleting %s after %s hour(s)." % (f, cleanup_time))
                    os.remove(f)
                    save = True
                else:
                    new_extracted.append(f)
            else:
                log.info("File %s no longer exists, removing from tracking." % f)
                save = True
        if save:
            self.config['extracted'] = new_extracted
            self.config.save()

    def _on_torrent_finished(self, torrent_id):
        """
        This is called when a torrent finishes and checks if any files to extract.
        """
        tid = component.get('TorrentManager').torrents[torrent_id]
        self.EXTRACT_TOTAL = 0
        t_status = tid.get_status([], False, False, True)
        do_extract = False
        tid.is_finished = False
        tid.update_state()
        torrent_name = t_status['name']
        log.info("Processing completed torrent: %s" % torrent_name)
        # Fetch our torrent's label
        labels = self.get_labels(torrent_id)
        log.debug("Labels collected for %s: %s" % (torrent_name, labels))
        # If we've set a label filter, process it
        filters = self.config['label_filter'].replace(" ", "")
        matched_label = None
        to_extract = []
        if filters != "":
            if len(labels) > 0:
                # Make the label list once, save needless processing.
                if "," in self.config['label_filter']:
                    label_list = filters.split(",")
                else:
                    label_list = [filters]
                log.debug("Filters collected: %s" % label_list)

                # Make sure there's actually a label
                for label in labels:
                    if label in label_list:
                        log.info("Label match (%s), checking %s for archives." % (label, torrent_name))
                        matched_label = label
                        do_extract = True
                        break
                    # We don't need to keep checking labels if we've found a match
                    if do_extract:
                        break
        # Otherwise, we just extract everything
        else:
            log.info("No label filters, extracting: %s" % torrent_name)
            do_extract = True

        if do_extract:
            extract_in_place = self.config["extract_in_place"]
            extract_selected_folder = self.config["extract_selected_folder"]
            append_label = self.config["append_matched_label"]
            extract_torrent_root = self.config["extract_torrent_root"]
            dest = Path(self.config["extract_path"])

            if extract_selected_folder and append_label and matched_label is not None:
                dest = dest.joinpath(matched_label)
            # Override destination if extract_torrent_root is set
            if extract_torrent_root:
                dest = Path(t_status['download_location']).joinpath(t_status['name'])

            files = tid.get_files()

            for f in files:
                file = f['path']
                # Override destination to file path if in_place set
                f_parent = Path(t_status['download_location']).joinpath(os.path.dirname(f['path']))
                if extract_in_place and ((not os.path.exists(f_parent)) or os.path.isdir(f_parent)):
                    dest = f_parent
                file_root, file_ext = os.path.splitext(f['path'])
                file_ext_sec = os.path.splitext(file_root)[1]
                if file_ext_sec == ".tar":
                    file_ext = file_ext_sec + file_ext
                    file_root = os.path.splitext(file_root)[0]
                    # IF it's not extractable, move on.
                if file_ext not in EXTRACT_COMMANDS:
                    continue

                    # Check to prevent double extraction with rar/r00 files
                if file_ext == '.r00' and any(x['path'] == file_root + '.rar' for x in files):
                    log.debug('Skipping file with .r00 extension because a matching .rar file exists: %s' % file)
                    continue

                    # Check for RAR archives with PART in the name
                if file_ext == '.rar' and 'part' in file_root:
                    part_num = file_root.split('part')[1]
                    if part_num.isdigit() and int(part_num) != 1:
                        log.debug('Skipping remaining multi-part rar files: %s' % file)
                        continue
                eo = ExtractObject(f['path'], dest)
                to_extract.append(eo)

        if len(to_extract) > 0:
            thread = Thread(target=self.process_files, args=(to_extract, t_status, torrent_id, torrent_name))
            thread.start()
        else:
            tid.is_finished = True
            tid.update_state()
            log.info("Processing complete for torrent: %s" % torrent_name)

    """
    """

    def process_files(self, files: list, t_status: object, torrent_id: str, torrent_name: str) -> object:
        extract_objects = []
        torrent = component.get('TorrentManager').torrents[torrent_id]
        file: ExtractObject
        for file in files:
            full_command = None
            file_root, file_ext = os.path.splitext(file.path)
            file_ext_sec = os.path.splitext(file_root)[1]
            if file_ext_sec == ".tar":
                file_ext = file_ext_sec + file_ext
            log.info("Extracting %s" % file.path)
            fpath = os.path.normpath(os.path.join(t_status['download_location'], file.path))
            file.path = fpath
            # Get base commands
            full_command = EXTRACT_COMMANDS[file_ext].copy()
            # Append file path
            file.command1 = full_command
            # Check to see if we need two steps for windows/7z
            if file_ext in EXTRA_COMMANDS:
                file.command2 = EXTRA_COMMANDS[file_ext].copy()
            extract_objects.append(file)

        if len(extract_objects) > 0:
            use_temp = self.config["use_temp_dir"]
            ex_obj: ExtractObject
            for ex_obj in extract_objects:
                self.do_extract(ex_obj, torrent_id)
            if use_temp:
                ex_dir = Path(tempfile.gettempdir()).joinpath(str(torrent_id))
                os.rmdir(ex_dir)
        torrent.is_finished = True
        torrent.update_state()
        log.info("Processing complete for torrent: %s" % torrent_name)

    def do_extract(self, to_extract, torrent_id):
        """
        :param torrent_id:
        :type to_extract: ExtractObject
        """
        destination = to_extract.destination
        use_temp = self.config["use_temp_dir"]
        ex_dir = to_extract.destination
        if use_temp:
            ex_dir = Path(tempfile.gettempdir()).joinpath(str(torrent_id))
        try:
            if not (os.path.exists(ex_dir) and os.path.isdir(ex_dir) and use_temp):
                os.makedirs(ex_dir)
        except Exception as f:
            log.info("MKEX: %s" % f)
        try:
            commands = to_extract.command1
            commands.append(to_extract.path)
            existing_files = os.listdir(ex_dir)
            if to_extract.command2 is None:
                log.info('Extracting with command: "%s" to "%s"' % (" ".join(commands), str(ex_dir.name)))
                ps = subprocess.Popen(to_extract.command1, cwd=ex_dir, stdout=subprocess.PIPE)
                ps.wait()
                log.info("Extraction complete.")
            else:
                log.info("Extracting with commands: '%s' and '%s'" % (" ".join(commands), to_extract.command2))
                ps = subprocess.Popen(to_extract.command1, cwd=ex_dir, stdout=subprocess.PIPE)
                _ = subprocess.check_output(to_extract.command2, cwd=ex_dir, stdin=ps.stdout)
                ps.wait()
            if ps.returncode != 0:
                log.error(
                    'Extract failed for %s with code %s' % (ex_dir, ps.returncode)
                )
            else:
                now = datetime.datetime.now().timestamp()
                if use_temp:
                    log.debug("Moving files from temp...")
                    try:
                        allfiles = os.listdir(ex_dir)
                        try:
                            if not (os.path.exists(destination) and os.path.isdir(destination)):
                                os.makedirs(destination)
                        except OSError as ex:
                            if not (ex.errno == errno.EEXIST and os.path.isdir(destination)):
                                log.error("Error creating destination folder: %s" % ex)
                        log.debug("Moving files for %s from temp to %s." % (to_extract.path, destination))
                        extracted = self.config['extracted']
                        for f in allfiles:
                            src = ex_dir.joinpath(f)
                            dest = Path(destination).joinpath(f)
                            temp_dest = "%s.extplus" % dest
                            log.info("Moving %s to %s" % (src, temp_dest))
                            shutil.move(src, temp_dest)
                            log.info("Renaming %s to %s" % (temp_dest, dest))
                            shutil.move(temp_dest, dest)
                            os.utime(dest, (now, now))
                            extracted.append(str(dest))
                        self.config['extracted'] = extracted
                        self.config.save()
                    except OSError as e:
                        log.error("Error: %s : %s" % (ex_dir, e.strerror))
                else:
                    extracted = self.config['extracted']
                    new_files = os.listdir(ex_dir)
                    for new_file in new_files:
                        if new_file not in existing_files:
                            dest = Path(ex_dir).joinpath(new_file)
                            os.utime(dest, (now, now))
                            extracted.append(str(dest))
                    self.config['extracted'] = extracted
                    self.config.save()
        except Exception as e:
            log.error("Extract Exception: %s" % e)

    @staticmethod
    def get_labels(torrent_id):
        """
         Asking the system about the labels isn't very cool, so try this instead
        """
        labels = []
        label_config = ConfigManager('label.conf', defaults=False)
        if 'torrent_labels' in label_config:
            log.debug("We have a Label config.")
            if torrent_id in label_config['torrent_labels']:
                labels.append(label_config['torrent_labels'][torrent_id])

        label_plus_config = ConfigManager('labelplus.conf', defaults=False)
        if 'mappings' in label_plus_config:
            log.debug("We have a label plus config.")
            if torrent_id in label_plus_config['mappings']:
                mapping = label_plus_config['mappings'][torrent_id]
                labels.append(label_plus_config['labels'][mapping]['name'])

        return labels

    @export
    def set_config(self, config):
        """Sets the config dictionary."""
        auto_clean = self.config['auto_cleanup']
        for key in config:
            self.config[key] = config[key]
        if auto_clean != self.config['auto_cleanup']:
            auto_clean = self.config['auto_cleanup']
            if auto_clean:
                self.check_thread.start()
            else:
                self.check_thread.stop()
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary."""
        return self.config.config


class ExtractObject:
    def __init__(self, path, destination):
        self.path = path
        self.destination = destination
        self.command1 = None
        self.command2 = None
