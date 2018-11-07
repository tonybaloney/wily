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

Command Line Usage
------------------

.. click:: wily.__main__:cli
   :prog: wily
   :show-nested:


"cute animal doing dabbing" [Designed by Freepik](https://www.freepik.com/free-vector/cute-animal-doing-dabbing_2462508.htm)