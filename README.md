## Introduction

This code is a solution to the following problem: Our codebase is git, and we have a in-house package repository used by
Pip, setuptools and buildout. Git lacks the easy versioning of svn, so this code does the following:

* Maintain a text file, windows ini format, with one section per package
* Create a package section when its first requested
* If present, the optional HTTP argument 'git_hash' is saved with the package, so that developers can see the
  last version, its associated git commit tag and the timestamp when it was generated.
* Presents an index page that displays the above without changing them
* Versions are simple post-increment, done when you pull the REST URL /package_name

## Run it

* Interactively: python setup.py
* As a daemonized service: twistd -y deploy.tac
* Foreground service: twistd -ny deploy.tac
