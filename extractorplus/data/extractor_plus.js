/*!
 * extractor_plus.js
 *
 * Copyright (C) 2019-2022 Digitalhigh <donate.to.digitalhigh@gmail.com>
 *
 * Based on Simple Extractor and Extractor Plugins:
 * Copyright (C) 2015 Chris Yereaztian <chris.yereaztian@gmail.com>
 * Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
 * Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
 *
 */

Ext.ns('Deluge.ux.preferences');

/**
 * @class Deluge.ux.preferences.ExtractorPlusPage
 * @extends Ext.Panel
 */


Deluge.ux.preferences.ExtractorPlusPage = Ext.extend(Ext.Panel, {

    title: _('Extractor Plus'),
    header: false,
    layout: 'fit',
    border: false,

    initComponent: function () {
        Deluge.ux.preferences.ExtractorPlusPage.superclass.initComponent.call(this);
        
        // Create the main container with vertical layout and scrolling capability
        this.scrollContainer = this.add({
            xtype: 'panel',
            layout: 'anchor',
            autoScroll: true,
            border: false,
            bodyStyle: 'padding: 5px;'
        });
        
        // Add the form to the scrollable container
        this.form = this.scrollContainer.add({
            xtype: 'form',
            layout: 'form',
            border: false,
            autoHeight: true,
            anchor: '100%'
        });
       this.behaviorSet = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Extraction Behavior'),
            autoHeight: true,
            labelAlign: 'top',
            labelWidth: 80,
            defaultType: 'radiogroup',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
        });

        // Add radio group for extract behavior
        this.extractBehavior = this.behaviorSet.add({
            xtype: 'radiogroup',
            style: 'margin-top: 0px; margin-bottom: 0px; padding-bottom: 0px;',
            columns: 1,
            colspan: 2,
            labelWidth: 80,
            fieldLabel: 'Extract To',
            items: [
                {
                    boxLabel: _('Selected Folder'),
                    name: 'extract_behavior',
                    inputValue: "extract_selected_folder",
                    checked: false,
                    listeners: {
                        render: function (c) {
                            Ext.QuickTips.register({
                                target: c,
                                text: 'All archives will be extracted to the selected folder below.'
                            });
                        }
                    }
                },
                {
                    boxLabel: _('Torrent Root'),
                    name: 'extract_behavior',
                    inputValue: "extract_torrent_root",
                    checked: false,
                    listeners: {
                        render: function (c) {
                            Ext.QuickTips.register({
                                target: c,
                                text: 'All archives will be extracted to the root of the torrent directory.'
                            });
                        }
                    }
                },
                {
                    boxLabel: _('In-Place'),
                    name: 'extract_behavior',
                    inputValue: "extract_in_place",
                    checked: false,
                    listeners: {
                        render: function (c) {
                            Ext.QuickTips.register({
                                target: c,
                                text: 'All archives will be extracted in-place within the torrent directory structure.'
                            });
                        }
                    }
                }
            ],
            listeners: {
                change: function (radioGroup, checkedRadio) {
                    if (checkedRadio && checkedRadio.inputValue) {
                        console.log("Radio selection changed to:", checkedRadio.inputValue);
                        this.setDestEnabled(checkedRadio.inputValue === "extract_selected_folder");
                    }
                },
                scope: this,
            },
        });

        // Add "Use Temp Directory" checkbox
        this.useTemp = this.behaviorSet.add({
            xtype: 'checkbox',
            name: "use_temp_dir",
            fieldLabel: _('Use Temporary Directory'),
            labelSeparator: '',
            boxLabel: _('Extract to a temporary directory first, then move to the final destination.'),
        });
        
        // Add temp directory field in a separate container
        this.tempDirContainer = this.behaviorSet.add({
            xtype: 'container',
            layout: 'form',
            hideLabel: true,
            style: 'margin-left: 25px; margin-bottom: 5px;'
        });
        
        this.tempDir = this.tempDirContainer.add({
            xtype: 'textfield',
            name: 'temp_dir',
            fieldLabel: _('Temp Directory'),
            labelSeparator: '',
            width: 300
        });
        
        // Add max threads field
        this.maxThreadsContainer = this.behaviorSet.add({
            xtype: 'container',
            layout: 'form',
            hideLabel: false
        });
        
        this.maxThreads = this.maxThreadsContainer.add({
            xtype: 'spinnerfield',
            name: 'max_extract_threads',
            fieldLabel: _('Max Concurrent Extractions'),
            labelSeparator: '',
            minValue: 1,
            maxValue: 10,
            value: 2,
            width: 100
        });

        // Link the temp directory field to be enabled only when useTemp is checked
        this.useTemp.on('check', function(checkbox, checked) {
            this.tempDir.setDisabled(!checked);
            this.tempDirContainer.setVisible(checked);
        }, this);

        this.appendArchive = this.behaviorSet.add({
            xtype: 'checkbox',
            columns: 1,
            colspan: 2,
            labelStyle: 'display: none',
            boxLabel: _('Append Archive Name to Destination'),
            name: "append_archive_name",
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'When enabled, a directory will be created in the extraction destination named after the torrent being extracted.'
                    });
                }
            }
        });

        this.destinationSet = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Destination'),
            autoHeight: true,
            labelAlign: 'top',
            labelWidth: 80,
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;'
        });

        // Destination label
        this.extractPath = this.destinationSet.add({
            fieldLabel: _('<b>Destination Folder:</b>'),
            name: 'extract_path',
            labelSeparator: '',
            width: '97%',
            style: 'margin-bottom: 0px; padding-top: 0px; padding-bottom: 0px',
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'All archives will be extracted to this directory, with the optional matched label name if enabled.'
                    });
                }
            }
        });

        this.appendLabel = this.destinationSet.add({
            xtype: 'checkbox',
            columns: 1,
            colspan: 2,
            boxLabel: _('Append Matched Label to Destination'),
            name: "append_matched_label",
            labelStyle: 'display: none',
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'Appends the first matched label to the destination path when enabled and "Extract Behavior" is set to "Selected Folder"'
                    });
                }
            }
        })


        this.cleanupSet = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Cleanup'),
            autoHeight: true,
            labelAlign: 'top',
            labelWidth: 80,
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;'
        });

        this.autoCleanup = this.cleanupSet.add({
            xtype: 'checkbox',
            columns: 1,
            colspan: 2,
            labelStyle: 'display: none',
            boxLabel: _('Auto-Delete Extracted Files'),
            name: "auto_cleanup",
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'Auto-Delete Extracted Files After a Specified Period of Time (In Hours).'
                    });
                },
                change: function (radio, newValue, oldValue) {
                    console.log("CHG: ", newValue);
                    this.showCleanupTime(newValue);
                },
                scope: this,
                click: function (radio, newValue, oldValue) {
                    console.log("CHG: ", newValue);
                    this.showCleanupTime(newValue);
                }
            },
        });

        this.autoCleanupTime = this.cleanupSet.add({
            fieldLabel: _('Cleanup Time (Hours):'),
            name: 'cleanup_time',
            labelSeparator: '',
            width: '97%',
            style: 'margin-bottom: 0px; padding-top: 0px; padding-bottom: 0px',
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'Number of hours before deleting an extracted file.'
                    });
                }
            }
        });

        this.labelSet = this.form.add({
            xtype: 'fieldset',
            border: false,
            title: _('Label Filtering'),
            autoHeight: true,
            labelAlign: 'top',
            labelWidth: 80,
            defaultType: 'textfield',
            style: 'margin-top: 3px; margin-bottom: 0px; padding-bottom: 0px;',
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'The target label(s) to match for extraction. Separate with commas for multiple values, ' +
                            'leave blank for all.'
                    });
                }
            }
        });

        // Label Filter Label
        this.labelFilter = this.labelSet.add({
            name: 'label_filter',
            labelSeparator: '',
            labelStyle: 'display: none',
            width: '97%'
        });

        // Label Filter Input
        this.labelSet.add({
            xtype: 'label',
            fieldLabel: _('(Comma-separated, leave blank for all.)'),
            labelSeparator: '',
            name: '',
            width: '97%'
        });

        // Make sure we load the config as soon as the component is rendered
        this.on('afterrender', this.updateConfig, this);
        // Also update when shown
        this.on('show', this.updateConfig, this);
    },

    onApply: function () {
        // Build up config from form values
        var config = {};
        config['extract_path'] = this.extractPath.getValue();
        
        // Initialize all extraction options to false
        config['extract_selected_folder'] = false;
        config['extract_torrent_root'] = false;
        config['extract_in_place'] = false;
        
        // Find which radio button is selected
        var selectedValue = null;
        var items = this.extractBehavior.items.items;
        for (var i = 0; i < items.length; i++) {
            if (items[i].checked) {
                selectedValue = items[i].inputValue;
                break;
            }
        }
        
        console.log("Selected radio value:", selectedValue);
        
        // Set the appropriate option based on selection
        if (selectedValue === "extract_selected_folder") {
            config['extract_selected_folder'] = true;
        } else if (selectedValue === "extract_torrent_root") {
            config['extract_torrent_root'] = true;
        } else if (selectedValue === "extract_in_place") {
            config['extract_in_place'] = true;
        } else {
            // Default to selected folder if nothing is selected
            console.warn("No extraction location selected, defaulting to Selected Folder");
            config['extract_selected_folder'] = true;
        }
        
        // Set the rest of the config options
        config['label_filter'] = this.labelFilter.getValue();
        config['use_temp_dir'] = this.useTemp.getValue();
        config['temp_dir'] = this.tempDir.getValue();
        config['append_matched_label'] = this.appendLabel.getValue();
        config['append_archive_name'] = this.appendArchive.getValue();
        config['auto_cleanup'] = this.autoCleanup.getValue();
        config['cleanup_time'] = this.autoCleanupTime.getValue();
        config['max_extract_threads'] = this.maxThreads.getValue();
        
        console.log("Saving config:", config);
        
        // Save the config to the server
        deluge.client.extractorplus.set_config(config);
    },

    onOk: function () {
        this.onApply();
    },

    updateConfig: function () {
        deluge.client.extractorplus.get_config({
            success: function (config) {
                this.extractPath.setValue(config['extract_path']);
                
                // Determine which extraction behavior is active from the config
                var behavior = null;
                
                console.log("Config values:", {
                    in_place: config['extract_in_place'],
                    torrent_root: config['extract_torrent_root'],
                    selected_folder: config['extract_selected_folder']
                });
                
                // Priority: in-place > torrent-root > selected-folder
                if (config['extract_in_place']) {
                    behavior = "extract_in_place";
                } else if (config['extract_torrent_root']) {
                    behavior = "extract_torrent_root";
                } else {
                    behavior = "extract_selected_folder";
                }
                
                console.log("Selected behavior from config:", behavior);
                
                // Properly set the radio button
                var items = this.extractBehavior.items.items;
                for (var i = 0; i < items.length; i++) {
                    var item = items[i];
                    if (item.inputValue === behavior) {
                        item.setValue(true);
                    } else {
                        item.setValue(false);
                    }
                }
                
                // Update UI visibility based on selection
                this.setDestEnabled(behavior === "extract_selected_folder");
                
                // Set all other fields
                this.showCleanupTime(config['auto_cleanup']);
                this.labelFilter.setValue(config['label_filter']);
                this.useTemp.setValue(config['use_temp_dir']);
                this.tempDir.setValue(config['temp_dir'] || '');
                this.tempDir.setDisabled(!config['use_temp_dir']);
                this.tempDirContainer.setVisible(config['use_temp_dir']);
                this.appendLabel.setValue(config['append_matched_label']);
                this.appendArchive.setValue(config['append_archive_name']);
                this.autoCleanup.setValue(config['auto_cleanup']);
                this.autoCleanupTime.setValue(config['cleanup_time']);
                this.maxThreads.setValue(config['max_extract_threads'] || 2);
            },
            scope: this
        });
    },

    setDestEnabled: function (enable) {
        console.log("SetDest: ", enable);
        this.destinationSet.setVisible(enable);
    },

    showCleanupTime: function(enable) {
        this.autoCleanupTime.setVisible(enable);
    }
});

// Create the proper plugin namespace
Ext.ns('Deluge.plugins');

// Define the plugin
Deluge.plugins.ExtractorPlusPlugin = Ext.extend(Deluge.Plugin, {
    name: 'ExtractorPlus',

    onDisable: function() {
        // Clean up menus
        if (this.tmSep) {
            deluge.menus.torrent.remove(this.tmSep);
        }
        
        if (this.tm) {
            deluge.menus.torrent.remove(this.tm);
        }
        
        // Remove preference page
        if (this.prefsPage) {
            deluge.preferences.removePage(this.prefsPage);
        }
    },

    onEnable: function() {
        // Add the preference page
        this.prefsPage = deluge.preferences.addPage(
            new Deluge.ux.preferences.ExtractorPlusPage()
        );

        // Add a menu separator
        this.tmSep = deluge.menus.torrent.add(new Ext.menu.Separator());
        
        // Add the menu item
        this.tm = deluge.menus.torrent.add({
            text: _('Force Extract'),
            iconCls: 'icon-extract', // Use a CSS class for the icon
            handler: this.onForceExtract,
            scope: this
        });
    },
    
    onForceExtract: function() {
        var torrentIds = deluge.torrents.getSelectedIds();
        if (!torrentIds || torrentIds.length === 0) return;
        
        // Call the force_extract method for each selected torrent
        Ext.each(torrentIds, function(torrentId) {
            deluge.client.extractorplus.force_extract(torrentId, {
                success: function(result) {
                    if (result) {
                        deluge.ui.notify(_('Force Extract'), _('Started extraction for selected torrent(s)'));
                    } else {
                        deluge.ui.notify(_('Force Extract'), _('Error: Could not extract selected torrent(s)'), 'error');
                    }
                }
            });
        });
    }
});

// Register the plugin
Deluge.registerPlugin('ExtractorPlus', Deluge.plugins.ExtractorPlusPlugin);
