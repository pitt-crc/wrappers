Installation
------------

The CRC wrapper applications are installable via the `pipx <https://pypa.github.io/pipx/>`_ package manager:

.. code-block::

   pipx install git+https://github.com/pitt-crc/quota_notifier.git

The above command will install the full suite of command line utilities plus any required dependencies.
Extra installation options are also provided for developers requiring additional dependencies:

.. code-block:: bash

    git clone https://github.com/pitt-crc/quota_notifier
    pip install quota_notifier.[docs]

To install a specific subset of extras, chose from the options below.

+----------------------+----------------------------------------------------------+
| Install Option       | Description                                              |
+======================+==========================================================+
| ``[docs]``           | Dependencies required for building the documentation.    |
+----------------------+----------------------------------------------------------+
| ``[tests]``          | Dependencies required for running tests (with coverage). |
+----------------------+----------------------------------------------------------+
