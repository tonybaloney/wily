Rank Command
==============

The rank command will show a CLI table of files in order of their respective metric values. It is useful for identifying e.g. complex files.

.. image:: ../_static/wily_rank.png
   :align: center

Examples
--------

To display a file ranking, simply provide the path to a file or directory or the name of it.

.. code-block:: none

  $ wily rank example.py

By default, wily will show the default metric (maintainability index).

To change the metric, provide the metric name (run ``wily list-metrics`` for a list) as argument.

.. code-block:: none

  $ wily rank example.py raw.loc

Wily rank will show the last revision by default. If you want to show a specific revision, you can provide the index of the revision via ``--revision``.

.. code-block:: none

  $ wily rank example.py --revision 2

Command Line Usage
------------------

.. click:: wily.__main__:rank
   :prog: wily
   :show-nested: