CRC Wrapper Applications
========================

Command applications built by the Center for Research Computing (CRC) for
wrapping common HPC tasks.

The CRC wrapper applications provide a simplified interface for running common
HPC tasks on Slurm based clusters. They are designed as a stepping stone for
users who are new to working on HPC systems and still unfamiliar with the complex
functionality provided by Slurm.

A Note to External HPC Teams
----------------------------

Most of the applications documented here will work out of the box on a generic
Slurm cluster systems. However, some applications are built specifically for
the CRC and depend on internal CRC systems.

The applications are designed to be modular and can be installed independently.
See the :ref:`install` page for more details.


.. toctree::
   :hidden:

   Overview<self>
   install

.. toctree::
   :hidden:
   :caption: Developer Notes:
   :glob:

   developer_notes/new_app

.. Source files for documenting individual applications are generated
   dynamically by the sphinx-autoapi plugin. These files are added below.

.. toctree::
   :hidden:
   :caption: Applications:
   :glob:

   autoapi/apps/index
   autoapi/apps/[!_]**/*

.. toctree::
   :hidden:
   :caption: Utility Modules:
   :glob:

   autoapi/apps/_**/*
