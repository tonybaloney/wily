Graph Command
=============

The graph command generates HTML graphs for metrics, trends and data in the wily cache. The wily cache must be built first using the :doc:`build`.

Examples
--------

By default, ``wily graph`` will create a file, ``wily-report.html`` in the current directory and open it using the browser configured in the $BROWSER environment variable (the default on the OS).
To save the output to a specific HTML file and not open it, provide the ``-o`` flag and the name of the output file.

.. code-block::

   $ wily report example.py raw.loc -o example.html


Command Line Usage
------------------

.. click:: wily.__main__:graph
   :prog: wily
   :show-nested: