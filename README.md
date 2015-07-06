# Code42 Splunk App

This Splunk App connects to a Code42 Enterprise server for importing and syncing
event data between Code42 and Splunk.

## Getting Started

You'll need a Code42 Server when you go through the setup process during the
install for this app. Splunk will automatically guide you through the setup
process.

### Install Prerequisites

The Python scripts embedded inside this app have several required dependencies
that need to be installed for events to import successfully.

1. Check your Splunk server's system Python path.
	- For stability, you should ensure that `python3` is installed on your
	system&mdash;this will be used automatically by the Code42 app. The embedded
	Python included with Splunk does not support all the requirements of this app.
	- System `python` will be used if `python3` is not found in your `$PATH`, but
	if Python is not located at `/usr/bin/python` you will need to update the
	contents of `bin/_base.py` with the correct path.
1. Install Python dependencies using [pip][pip] (see below).

```
$ sudo pip3 install requests
$ sudo pip3 install python-dateutil
```

These dependencies are required regardless of your Python version. You can opt
to install them using `easy_install`.

### Install App

#### Install via Splunk Package

First, you'll need to export a Splunk Package by cloning the repo and exporting
the contents.

```
$ git clone [clone-url] Code42-Splunk
$ cd Code42-Splunk
$ git archive \
	--format=tar.gz \
	--prefix=code42/ \
	--output=code42.tar.gz \
	HEAD
$ mv code42.tar.gz code42.spl
```

After exporting the Splunk Package `.spl`, you can then install the package
using Splunk's built-in Apps page.

1. Select "Manage Apps" from the Apps dropdown.
1. Select the "Install app from file" button.
1. Select the generated `code42.spl` package.
1. Splunk will walk you through all required setup.

#### Install via Git Clone

You can install the git repository directly into your Splunk app contents and
keep the scripts updated.

```
$ export SPLUNK_HOME="/path/to/Splunk"
$ cd $SPLUNK_HOME/etc/apps
$ git clone [clone-url] code42
```

Just make sure to restart Splunk after cloning the repository. You'll need to
open the Setup page from the Manage Apps page to configure your Code42 Server
info. From the Manage Apps page you can also enable and disable the Code42 app.

### Testing Installation

After the installation, you can test the Splunk scripts by running them using
the embedded Splunk python enviornment.

```
$ export SPLUNK_HOME="/path/to/Splunk"
$ $SPLUNK_HOME/bin/splunk login # Enter username & password
$ $SPLUNK_HOME/bin/splunk cmd \
	python $SPLUNK_HOME/etc/apps/code42/bin/splunk-test.py <<< \
	$(xmllint --xpath "//auth/sessionkey/text()" "$(find ~/.splunk -type f)")
```

The script should run successfully.

## Notes & Caveats

See [CAVEATS.md][caveats] for information about a few caveats in the Splunk
app, like changing your API User Credentials. 

## Data Imported

Data is automatically imported to a custom `code42` index once the app is
enabled. The different structured data formats described below are automatically
imported to the Code42 index using cron scripts and file monitors.

The Code42 App does contain some pre-built dashboards, but you are able to write
your own queries using Splunk's *Search & Reporting* app. You can see example
queries in the [EXAMPLES.md][examples] file.

## Contributing

Contributions are welcome for new and updated data types imported to Splunk
using the Code42 Splunk app. Each event should be saved to the `code42` index,
and should have it's own `sourcetype` namespace.

<!--
## URL References
-->
[pip]: https://pip.pypa.io/en/latest/index.html
[examples]: https://stash.corp.code42.com/projects/spyd/repos/splunk/browse/EXAMPLES.md
[caveats]: https://stash.corp.code42.com/projects/spyd/repos/splunk/browse/CAVEATS.md
