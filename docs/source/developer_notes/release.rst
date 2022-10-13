Release Procedures
==================

In this document, the words *shall*, *will*, and *must* refer to hard requirements.
The words *should* and *are expected to* refer to general objectives.

Generating a Release
--------------------

Follow the steps below to release a new package version.
Releases are expected to be performed using the default repository branch.
Refer to later sections in this document for additional guidelines and requirements.

1. Update the version number in the package ``__init__`` file.
2. Ensure all tests and CI checks are passing on the branch being used to generate the release
3. Create the new tag and release on GitHub. Include a useful/descriptive note on changes made in the new release.

Selecting Release Names
-----------------------

The following requirements **must** be met when generating a new release.

- Variation between release names and the associated tag names causes confusion.
  Release tags and release names must be the same.
- Naming conventions should be consistent across successive releases.
  Unless there is strong reasons to proceed otherwise, releases and tags will be named starting with
  a lowercase `v` followed by a PEP 440 compliant version number (see additional details below).

Selecting Version Numbers
-------------------------

The following requirements **must** be met when updating the package version.

- Package versions numbers must be `PEP 440 <https://peps.python.org/pep-0440/>`_ compliant.
  Deviation from the 440 standard can cause packaging issues and/or downstream complications.
- Custom versioning for individual commandline utilities is not allowed.
  All commandline utilities provided by the package must share the same version number.
- The official package version number must be defined in the ``__init__`` file and nowhere else.
  All other utilities/workflows should reference this value.
