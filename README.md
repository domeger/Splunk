# Code42 App for Splunk

### Disclaimer
This repo is pushed to the public [Code42 Github repo](https://github.com/code42/Splunk)

The Code42 App for Splunk connects to a Code42 server for importing and syncing
event data between Code42 and Splunk.

## Getting Started

You must have an installed and configured Code42 server to complete the Code42
App for Splunk setup process. Splunk guides you through the setup process, but
you may also read the Code42 App for Splunk installation article at the
[Code42 Support site][support].

### Install App

#### Install via Splunk Package

First, you'll need to export a Splunk Package by cloning the repo and exporting
the contents.

```
$ git clone https://github.com/code42/Splunk.git Code42-Splunk
$ cd Code42-Splunk
$ git archive \
    --format=tar.gz \
    --prefix=code42/ \
    --output=code42.tar.gz \
    HEAD
$ mv code42.tar.gz code42.spl
```

After exporting the Splunk Package `.spl`, you can install the package using
Splunk's built-in Apps page.

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
$ git clone https://github.com/code42/Splunk.git code42
```

Restart Splunk after cloning the repository, then open the Setup page from the
Manage Apps page to configure your Code42 server info. From the Manage Apps page
you can also enable and disable the Code42 app for Splunk.

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

## Data Imported

Data is automatically imported to a custom `code42` index once the app is
enabled. The different structured data formats described below are automatically
imported to the Code42 index using cron scripts and file monitors.

The Code42 app for Splunk does contain some pre-built dashboards, but you can
also write your own queries using Splunk's *Search & Reporting* app. You can see
example queries in the [EXAMPLES.md][examples] file.

## Contributing

Contributions are welcome for new and updated data types imported to Splunk
using the Code42 App for Splunk. Each event should be saved to the `code42`
index, and should have it's own `sourcetype` namespace.

<!--
## URL References
-->
[support]: https://code42.com/r/support/splunk-app
[pip]: https://pip.pypa.io/en/latest/index.html
[examples]: EXAMPLES.md
