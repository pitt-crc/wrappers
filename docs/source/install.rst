Installation
------------

The CRC wrapper applications are a suite of command line applications installable via the
`pip <https://pip.pypa.io/en/stable/>`_ (or `pipx <https://pypa.github.io/pipx/>`_)
package manager:

.. code-block::

   pipx install git+https://github.com/pitt-crc/wrappers.git

.. note::
   The ``pipx`` utility is recommended for system administrators working in
   environments with conflicting package managers
   (like `lmod <https://lmod.readthedocs.io/en/latest/>`_).

All command line applications are installed

.. code-block::

   pipx install git+https://github.com/pitt-crc/wrappers.git --install-option="--nocrc"
