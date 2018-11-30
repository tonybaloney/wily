Report Command
==============

The report command will show a CLI table of metrics for the list of files provided. It is useful for comparing differences and trends between revisions.

.. image:: ../_static/wily_report.png
   :align: center

Examples
--------

To show a report, simply give the name or path to the file you want to report on

.. code-block:: none

  $ wily report example.py

By default, wily will show the default metrics (typically Lines-of-code, cyclomatic complexity and maintainability index)

To change the metrics, provide the metric names (run ``wily list-metrics`` for a list) as arguments.

.. code-block:: none

  $ wily report example.py raw.loc raw.sloc raw.comments

Wily report will show all available revisions, to only show a set number, add the ``-n`` or ``--number`` flag

.. code-block:: none

  $ wily report example.py -n 10

Similar to the index command, ``wily report`` will not show the commit message. To add the message to the output, add the ``--message`` flag.

.. code-block:: none

  $ wily report example.py --message

Command Line Usage
------------------

.. click:: wily.__main__:report
   :prog: wily
   :show-nested: