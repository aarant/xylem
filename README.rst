.. |pypi| image:: https://img.shields.io/pypi/v/xylem.svg
.. _pypi: https://pypi.python.org/pypi/xylem
.. |license| image:: https://img.shields.io/github/license/arantonitis/xylem.svg
.. _license: https://github.com/arantonitis/xylem/tree/master/LICENSE

Xylem
*****
|pypi|_ |license|_

Convert Python Abstract Syntax Trees (ASTs) to readable source code.

Xylem is useful for when you want to make dynamic changes to Python code/ASTs, but also need to write those changes back as source code.

It's also very small (<500 lines), pure-Python, and produces (mostly) readable source code.

In writing this, I made heavy use of the unofficial AST documentation at `Green Tree Snakes`_.

.. _Green Tree Snakes: https://greentreesnakes.readthedocs.io

Installation
============
Xylem will work on Python 3.4 or later. I'll eventually get around to testing it on Python 2.7-3.3.

From PyPI
---------
Install Xylem by running ``pip3 install xylem`` from the command line.

.. note::

   On some Linux systems, installation may require running pip with root permissions, or running ``pip3 install xylem --user``. The latter may require exporting `~/.local/bin` to PATH.
   
From GitHub
-----------
Clone or download the `git repo`_, navigate to the directory, and run::

    python3 setup.py sdist
    cd dist
    pip3 install xylem-<version>.tar.gz
    
.. _git repo: https://github.com/arantonitis/xylem

Usage
=====
``to_source`` is likely the only method you'll need to use:

.. code-block:: python

    >>> from xylem import to_source
    >>> import ast
    >>> tree = ast.parse("print('hello world')")
    >>> ast.dump(tree)
    "Module(body=[Expr(value=Call(func=Name(id='print', ctx=Load()), args=[Str(s='Hello world')], keywords=[]))])"
    >>> to_source(tree)
    "print('hello world')"

``compare_ast`` may also be useful for determining if two ASTs are functionally equivalent.

Development
===========
Xylem versioning functions on a ``MAJOR.MINOR.PATCH.[DEVELOP]`` model. Only stable, non development releases will be published to PyPI. Because Xylem is still a beta project, the ``MAJOR`` increment will be 0. Minor increments represent new features. Patch increments represent problems fixed with existing features.
