# Extractor Plus
## (Formerly SimpleExtractor V2)


Extractor Plus is a plugin for the [deluge V2](http://deluge-torrent.org/) torrent client.

This is a spiritual successor to the [SimpleExtractor V1](https://github.com/cvarta/deluge-extractor/releases/tag/v.0.4.1) plugin...
with *numerous* fixes, modifications, and additional features added. 

With the most recent update, it has become so far removed from the [original project](https://github.com/d8ahazard/deluge-extractor), that I felt it was appropriate to
change the name and re-release it as "Extractor Plus".

And so, here we are!

<img src="https://user-images.githubusercontent.com/1633844/169893033-1012f628-93aa-41f6-95fe-a3f37dbbf7b2.png" width="400">

# Features
#### Specify download locations:
* In-place: Extract each .rar file to it's exact location. If a file is in /downloads/TORRENTNAME/subs/subs.rar, it will be extracted to /downloads/TORRENTNAME/subs/.
* Torrent root: Extract each rar to the root of the torrent download. If a file is in /downloads/TORRENTNAME/sub/subs.rar, it will be extracted to /downloads/TORRENTNAME/.
* Selected Folder: Extract to a directory that you specify.

<img src="https://user-images.githubusercontent.com/1633844/169892976-d339e735-8111-48a2-9eea-43c994020927.png" width="400">

#### (New) Automatic Cleanup:
When enabled, extracted files will automatically be deleted after a specified period of time. Useful for cases
where you only need the extracted files to exist long enough to be copied by other applications.


#### (New) Temp directory support:
If a download is being monitored by other software, issues can often arise when extraction begins and the "other"
software tries to copy the extracted file(s) before extraction is complete. By extracting to a temporary directory and
then moving the completed file, these issues can be avoided. This can be disabled in settings.

#### Label filtering:
Enter a comma-separated list of labels, only those labels will be extracted. Works with the default labels plugin, as well as labelplus.

#### (New) "Append Label" support:
Allows appending a matched label to the extraction path when using "Selected Folder" as the download location.
IE: If you are extracting files to /downloads/extracted and a torrent has the label "Movies", the contents of the torrent
will be extracted to /downloads/extracted/Movies/

#### (New) Full cross-platform archive support:
Previous versions of this plugin were unable to handle tar.* archives due to requiring two separate commands.
This is no longer the case.

#### Zero dependencies:
For *nix users, the required software should be present in 99% of distributions. For Windows users, 7z.exe has been bundled
with the plugin, and should be all you need for the majority of use-cases.

The plugin now also use only "native" Python packages, and doesn't require anything extra in order to function.

#### Updated UI:
Now with tooltips and settings sections that only appear when needed. :D 

<img src="https://user-images.githubusercontent.com/1633844/169893196-52d2b252-6dfa-4e32-b7c2-52a12e05a840.png" width="300">


## Has been tested on:

* Deluge 2.0.5 (Docker, Windows)
* Python versions 3.9, 3.10


## Supported File formats:

Linux/Windows:
* .rar, .tar, .zip, .7z .tar.gz, .tgz, .tar.bz2, .tbz .tar.lzma, .tlz, .tar.xz, .txz


# Build Instructions
To build the python egg file for a different version that is available, install the version
of python you want to build for, and then run the following command from the root of the project directory:
```
  python setup.py bdist_egg
```

Alternatively, if you're using Windows, execute the "build.ps1" powershell script to automagically build eggs for any
installed version of Python from 3.5-3.14(future).

Compiled egg files will appear in the /dist folder of the project root.

# Installation Instructions

Download the [egg file](https://github.com/d8ahazard/deluge-extractorplus-plugin/releases/latest) of the plugin, or 
package your own (see above).

#### Notes
* Plugin eggs have the Python version encoded in the filename and will only load in Deluge if the versions match.
* (e.g. Plugin-1.0-py3.7.egg is a Python 3.7 egg, etc.)

* On *nix systems, you can verify Python version with: ```python --version```

* The bundled Python version for Windows executable at the time of this writing is 3.9 and for MacOSX Deluge.app it is ?.

* If a plugin does not have a Python version available, it's usually possible to rename it to match your installed version.
* (e.g. Plugin-1.0-py3.7.egg to Plugin-1.0-py3.8.egg) and it will still run normally, although this shouldn't be necessary.

### GUI-Install:

Preferences -> Plugins -> Install plugin

Locate the downloaded egg file and select it.

### Manual Install:

Copy the egg file into the ```plugins``` directory in Deluge config:

Linux/*nix:

``` ~/.config/deluge/plugins ```

Windows:

``` %APPDATA%\deluge\plugins ```

### Client-Server Setups:

When running the Deluge daemon, ``` deluged ``` and the Deluge client on separate computers, the plugin must be installed on both of them. When installing the egg through the GTK client it will be placed in the plugins directory of your computer, as well as copied over to the computer running the daemon.

#### Note: If the Python versions on the server and desktop computer do not match, you will have to copy the egg file to the server manually.

For example in the setup below you will have to install the py2.6 egg on the desktop as you normal would do but then manually install the py2.7 egg onto the server.

* Windows desktop with Python 3.9 running GTK client.
* Linux server with Python 3.10 running deluged

#### Note: The Windows installer comes bundled with python: either python 2.6 or 2.7 depending on the intstaller you used.


### Support my work?

If you dig this plugin and want to say thanks, the best way to do it is by sending a paypal donation to donate.to.digitalhigh@gmail.com

All donations are appreciated...but none are required :D
