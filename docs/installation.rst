.. highlight:: shell

============
Installation
============


Stable release
--------------

To install adnipy, run this command in your terminal:

.. code-block:: console

    $ pip install adnipy

This is the preferred method to install adnipy, as it will always install the
most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for adnipy can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/mcsitter/adnipy

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/mcsitter/adnipy/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    # For a normal install, use pip
    $ pip install .

    # For development, the project provides Makefile targets that create
    # a virtual environment and install development dependencies. This is
    # the recommended workflow for contributors:
    $ make init

    # Alternatively install in editable mode with development extras:
    $ pip install -e .[dev]


.. _Github repo: https://github.com/mcsitter/adnipy
.. _tarball: https://github.com/mcsitter/adnipy/tarball/master
