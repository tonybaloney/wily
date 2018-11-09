.. wily documentation master file, created by
   sphinx-quickstart on Wed Nov  7 15:11:13 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/logo.png
   :align: center

A Python application for tracking, reporting on timing and complexity in tests and applications.

Wily uses git to go through each revision (commit) in a branch and run complexity and code-analysis metrics over the code. You can use this to limit your code or report on trends for complexity, length etc.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

What is wily?
-------------

Wily is a command-line tool for archiving, exploring and graphing the complexity of Python source code.

Wily supports iterating over a git repository and indexing the complexity of the Python source files using a number of algorithms. You can then report on those in the console or graph them to a browser.

Getting Started
---------------

You can install wily from PyPi using pip

.. code-block:: console

   $ pip install wily

Wily needs an index of the project before any of the commands can be used. `wily build` builds an index in a Git repository. Provide the path to your source code as the first argument.

.. code-block:: console

   $ wily build src/

You can provide multiple source directories, such as your test projects.

.. code-block:: console

   $ wily build src/ test/

Now that you have an index, you can run `wily report` or `wily graph` to see the data.

.. code-block:: console

   $ wily report



Command Line Usage
------------------

.. click:: wily.__main__:cli
   :prog: wily
   :show-nested:


"cute animal doing dabbing" [Designed by Freepik](https://www.freepik.com/free-vector/cute-animal-doing-dabbing_2462508.htm)