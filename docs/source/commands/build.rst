=============
Build Command
=============

The build command will iterate through each revision in the chosen archiver and run analytics on the target code base.

By default, `wily build <target>` will assume the directory is a `git` repository and will scan back through 50 revisions.

Updating the index
------------------

To update the wily cache with any recent commits, simply re-run the `wily build` command and it will


Ignoring `.wily`
----------------

Before you run the build command, it is strongly recommended the `.wily/` directory be ignored from the git index. This can be achieved by adding
`.wily/` to `.gitignore` and committing changes to `.gitignore` before running `wily build`.

Without this, you will receive an error when running wily build, this is to prevent uncomitted changes being lost when switching revisions.

Dirty repositories
------------------

If you run `wily build` with any uncommited files, wily will give an error to protect those files being lost, stash or commit them first.

.. code-block::

    $ wily build src/
    Failed to setup archiver: 'Dirty repository, make sure you commit/stash files first'

Command Line Usage
------------------

.. click:: wily.__main__:build
   :prog: wily
   :show-nested: