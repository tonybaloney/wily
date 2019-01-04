=============
Build Command
=============

The build command will iterate through each revision in the chosen archiver and run analytics on the target code base.

By default, ``wily build <target>`` will assume the directory is a `git` repository and will scan back through 50 revisions.

.. image:: ../_static/wily_build.png
   :align: center

Examples
--------

Building a basic cache
~~~~~~~~~~~~~~~~~~~~~~

The most basic example takes the path to the source code and compiles a cache with the complexity of the last 50 commits

.. code-block:: none

   $ wily build src/

You can specify multiple source directories by simply adding additional paths to the command


.. code-block:: none

   $ wily build src/ test/

You can override the maximum number of commits recursed by using the ``-n`` or ``--max-revisions`` flags

.. code-block:: none

   $ wily build src/ test/ -n 100

By default, wily will compile the cyclomatic complexity, maintainability and raw metrics. If you only want a subset of those, you can specify with comma-seperate ``--operator`` or ``-o`` flag

.. code-block:: none

   $ wily build src/ test/ -n 100 -o raw,maintainability

Changing the default path
-------------------------

All of the wily commands support a ``--path`` flag to set the home path (defaults to the current working directory).

Updating the index
------------------

To update the wily cache with any recent commits, simply re-run the ``wily build`` command and it will

Dirty repositories
------------------

If you run ``wily build`` with any uncommited files, wily will give an error to protect those files being lost, stash or commit them first.

.. code-block:: none

    $ wily build src/
    Failed to setup archiver: 'Dirty repository, make sure you commit/stash files first'

Command Line Usage
------------------

.. click:: wily.__main__:build
   :prog: wily
   :show-nested: