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
      this.form = this.add({
            xtype: 'form',
            layout: 'form',
            border: false,
            autoHeight: true,
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
                change: function (radio, newValue, oldValue) {
                    console.log("CLICK: ", newValue['inputValue']);
                    this.setDestDisabled(newValue['inputValue'] !== "extract_selected_folder");
                },
                scope: this,
            },
        });

        // Use temp dir setting
        this.useTemp = this.behaviorSet.add({
            xtype: 'checkbox',
            columns: 1,
            colspan: 2,
            labelStyle: 'display: none',
            boxLabel: _('Extract to Temp and Move'),
            name: "use_temp_dir",
            listeners: {
                render: function (c) {
                    Ext.QuickTips.register({
                        target: c,
                        text: 'Extract file(s) to a temporary directory first, then move them to specified destination.'
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
        this.on('show', this.updateConfig, this);
    },

    onApply: function () {
        // build settings object
        var config = {};
        config['extract_path'] = this.extractPath.getValue();
        var eBehavior = this.extractBehavior.getValue();
        config['extract_in_place'] = false;
        config['extract_torrent_root'] = false;
        config['extract_selected_folder'] = false;
        config[eBehavior] = true;
        config['label_filter'] = this.labelFilter.getValue();
        config['use_temp_dir'] = this.useTemp.getValue();
        this.setDestDisabled(eBehavior !== "extract_selected_folder");
        deluge.client.extractorplus.set_config(config);
    },

    onOk: function () {
        this.onApply();
    },

    updateConfig: function () {
        deluge.client.extractorplus.get_config({
            success: function (config) {
                this.extractPath.setValue(config['extract_path']);
                var behavior = "extract_selected_folder";
                if (config['extract_in_place']) {
                    behavior = 'extract_in_place';
                }
                if (config['extract_torrent_root']) {
                    behavior = 'extract_torrent_root';
                }
                this.setDestDisabled(behavior !== "extract_selected_folder");
                this.extractBehavior.setValue(behavior);
                this.labelFilter.setValue(config['label_filter']);
                this.useTemp.setValue(config['use_temp_dir']);
            },
            scope: this
        });
    },

    setDestDisabled: function (disable) {
        console.log("SetDest: ", disable);
        if (disable) {
            this.destinationSet.setVisible(false);
        } else {
            this.destinationSet.setVisible(true);
        }
    }
});


Deluge.plugins.ExtractorPlusPlugin = Ext.extend(Deluge.Plugin, {
    name: 'Extractor Plus',
    onDisable: function () {
    console.log("Extractor plus disabled.");
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function () {
        console.log("Extractor plus enabled.");
        this.prefsPage = deluge.preferences.addPage(
        new Deluge.ux.preferences.ExtractorPlusPage()
        );
    }
});
Deluge.registerPlugin('Extractor Plus', Deluge.plugins.ExtractorPlusPlugin);
