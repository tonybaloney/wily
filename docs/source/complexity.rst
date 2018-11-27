Simplifying Python code
=======================

Using the maintainability-index
-------------------------------

The maintainability index of a file is measured by a calculation of its size and complexity `See detail`_

Long files with a lot of complexity are the hardest to maintain.


"If Python 2 do this, if Python 3 do this"
------------------------------------------

Python 2/3 specific imports start small but slowly get more and more complex, take this example:

.. code-block:: python

  import sys

  if sys.version_info[0] == 3:
     import new_module
  else:
     import old_module


Or, even worse, dealing with the unicode v.s. byte string types by putting statements all over your codebase

.. code-block:: python

    if sys.version_info[0] == 3:
       return data.encode('utf-8')
    else:
       return data

Alternatives
************

The six package can be used with import redirects in `six.moves`.

Overly-nested if statements
---------------------------

.. code-block:: python

  if x is not None:
     if len(x) > 0:
        if x[0] is not None:
           if 'attribute' in x[0]:
              return x[0]['attribute']
  return None

This complexity is unnecessary when it gets to 4+ levels deep.

In the PEP8 style guide for Python, the maximum line-length was chosen to help avoid some of this nesting.

Also, "simple is better than nested".

Alternatives
************

There are some alternatives, it is a perfectly acceptable pattern to catch IndexError and NameError (which both inherit from LookupError), and also TypeError (for trying to access x[0] if x is None). The exception statement accepts a tuple for matching exception types. Check out the `exception hierarchy`_ for a concept of where each one inherits.

.. code-block:: python

   try:
    return x[0]['attribute']
   except (LookupError, TypeError):
    return None

This code is easier to read, easier to understand.

If you're working with highly-nested Python dictionaries, `Jmes path`_ is an option for searching and indexing dictionaries.

"The function that does everything"
-----------------------------------

One obvious sign for refactoring is a single function that does "too-much".

Leveraging comprehensions
-------------------------

Python comes with a great piece of syntax - the comprehension. Sets, Lists and Dictionaries can all be "comprehended" by placing an expression within the {} or [] symbols.

Take these examples:

.. code-block:: python

  list_of_trees = ["birch", "lemon", "oak", "pine", "birch", "pine", "partridge in a pear"]

  # A set comprehension is a simple way to get unique values
  unique_trees = {tree for tree in list_of_trees}
  # sets are iterable, so there is no need to cast this back to a list!

  # you can filter values in a list and set comprehension
  unique_trees = {tree for tree in list_of_trees if "partridge" not in tree}
  # as a list comprehension
  real_trees = [tree for tree in list_of_trees if "partridge" not in tree]

  # you can even nest list comprehensions
  all_the_letters = [letter for tree in list_of_trees for letter in tree]

I don't recommend the last one. Nested list-comprehensions should be used rarely, and if so, separate them across lines.

Dictionary comprehensions are a useful replacement for the map command.

.. code-block:: python

  list_of_trees = [("birch", "silver"), ("lemon", "yellow"), ("oak", "green"), ("pine", "brown")]

  # as a dictionary comprehension
  {tree:color for tree,color in list_of_trees}

  # or with the color as the key
  {color:tree for tree,color in list_of_trees}

Then looking up values can be as simple as checking for the key in the dictionary.

.. code-block:: python

  if "birch" in list_of_trees:
    print("yes!")

.. _exception hierarchy: https://docs.python.org/3/library/exceptions.html#exception-hierarchy
.. _Jmes path: https://github.com/jmespath/jmespath.py
.. _See detail: https://radon.readthedocs.io/en/latest/intro.html