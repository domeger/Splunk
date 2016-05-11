#Project Setup:
  - When you clone the repo, run `nosetests -verbose && pylint --max-line-length=120 utils/c42api`
    from the root. If it runs you're probably all set up with everything you
    need. More likely, you'll need to install some things.
  - Make sure you're using python 2.7.x
  - `pip install -r requirements.txt`
  - `pip install pylint`
  - Now try running the command from above.
  - It's strongly recommended that you install the git commit hook for the
    project
    - This can be found in the internal-utilities repo.
    - There are instructions in the pre-commit file in comments on how to add
      the git commit hook to the splunk repo.
  - This git hook is recommended as a first line of defense against bad code.
    - When you make a change, make sure you pylint your files and fix any issues
      that it tells you about.
    - Some issues are unavoidable and you can comment in the file for pylint to
      ignore them, but use that sparingly and only when you're certain it's
      necessary.
      - `# pylint: disable=import-error`
  - If you don't have a preferred editor for Python going into this, the ones
    currently used on the team are:
    - emacs
    - PyCharm IDE
    - Sublime


#Project Structure:
  - There are several subprojects that interact with each other in this project
  - in splunk/utils/c42api there are files with functions that use the Code42
    API to get data.
    - They are not meant to be run by themselves.
    - They typically yield the dictionaries represented by the returned json
    - There are also some utilities in here for writing the data out to a file
  - in splunk/scripts there are files that invoke the above scripts.
    - They are meant to be run by themselves.
    - They create, typically, json or csv
    - Some have custom output, some just download files.
  - in splunk/bin/c42splunk there are scripts that act as a bridge between
    Splunk and c42api.
    - They're used as wrappers around c42api, processing the resulting data
      in a way that's useful to Splunk.


#Code Reviews:
  - Before you put up a pull request:
    - Test your code on Windows unless the change is trivial.
    - Pylint your code.
    - Write unit tests if possible for all of your changes.
    - Run unit tests
      - `nosetests -verbose`
    - Pylint your code.
  - Reviewing code:
    - At least one reviewer should test on Windows.
      - Draw straws if you have to. No one wants to do it.
    - Run unit tests
      - `nosetests -verbose`
    - Pylint the code.
      - Do not approve anything until it scores a 10 or is justifiably slightly
        lower than a 10.


#Documentation Convention:
  - Pylint will complain if you don't have a doc for your:
    - File
    - Class
    - Function
  - You must document anything pylint wants you to.
  - Your doc should look something like this:

```python
"""
One line explanation.

More explanation if necessary. Can be multiple lines. All doc lines less than
80 characters wide.
:raise SomeError: explanation of the reason for the exception being raised
                   that can be more than one line and should be indented by a
                   space on each new line.
:param x:         explanation of the parameter, including type if not obvious
                   and lining up with the furthest left explanation.
:param y:         explanation of the parameter, as above.
:return:          what it returns, including type if not obvious.
"""
```


#Coding Style:
  - Testability is a big deal. When you write a function, keep in mind that
    you have to test that function too.
  - Write small, modular functions that do one thing very well.
    - If your function gets indented very far, or if it gets too long, it
      probably needs to be rewritten into smaller functions.
  - Follow PEP8. Pylint will enforce it pretty well, but the more you
    internalize the standards, the easier linting will be.
