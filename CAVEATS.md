# Code42 Splunk App
## Notes & Caveats

There are a few important things to keep in mind with this Splunk app. They are
documented here.

### Changing API User Credentials

When changing the API User Splunk uses to connect to a Code42 Server, you'll
need to go through a few steps before going to the *Setup* page built-in to
Splunk (avaialble from *Manage Apps*) and saving new credentials.

Splunk expects us to add several username/password combinations to it's
configuration for encryption, while this app only allows one each time. When
you save a new username/password a new record is created, and you'll get an
error when you try to save a new password for an existing username.

This utility script will clear any existing credentials, so you can then save
a new username/password from the *Setup* page in Splunk.

```
$ splunk cmd python [...]/code42/utils/clear_credentials.py
```
