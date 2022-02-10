Using Wily in a CI/CD pipeline
==============================

Wily can be used in a CI/CD workflow to compare the complexity of the current files against a particular revision.

By default wily will compare against the previous revision (for a git-pre-commit hook) but you can also give a Git ref, for example `HEAD^1` is the commit before the HEAD reference.

.. code-block:: console

    $ wily build src/
    $ wily diff src/ -r HEAD^1

Or, to compare against

.. code-block:: shell

    $ wily build src/
    $ wily diff src/ -r master

.. image:: _static/diff_ref.png
   :align: center

The `wily diff` command takes additional arguments, such as a list of metrics, if you want to see a specific metric.

Examples
---------

Tox
+++

Wily can be run as a separate test environment:

.. code-block:: ini

    [testenv:wily]
    deps =
        wily
    commands =
        wily build src/
        wily diff src/ -r HEAD^1

Azure Pipelines
+++++++++++++++

Wily can be called as two separate tasks within a job:

.. code-block:: yaml

  - script: |
    pip install wily
    wily build src/
    displayName: Install Wily and compile cache

  - script: "wily diff src/ -r HEAD^1"
    displayName: Compare previous commit

Travis CI
+++++++++

Wily can be called after your tests have completed.

.. code-block:: yaml

  after_success:
    - pip install wily
    - wily build src/
    - wily diff src/ -r HEAD^1


GitHub Workflows
+++++++++

When using Wily in a Github Workflows, you need to specify to the checkout step to check out the head of the branch and not the merge commit

.. code-block:: yaml



  name: Example Wily Pipeline on PR

  on:
    pull_request:
  

  jobs:

    evaluate-complexity:
      name: Evaluate Code complexity
      runs-on: ubuntu-latest

      steps:
        - name: Checkout repository
          uses: actions/checkout@v2
          with:
            fetch-depth: 0
            ref: ${{ github.event.pull_request.head.ref }}
        - name: Set up Python
          uses: actions/setup-python@v2
          with:
            python-version: 3.10.0
        - name: Install Wily
          run: pip install wily==1.20.0
        - name: Build cache and diff
          id: wily
          run: |
            wily build my_package/ tests/
            DIFF=$(wily diff my_package/ tests/ --no-detail -r origin/${{ github.event.pull_request.base.ref }})
            echo "$DIFF"

            # Build multine output
            DIFF="${DIFF//'%'/'%25'}"
            DIFF="${DIFF//$'\n'/'%0A'}"
            DIFF="${DIFF//$'\r'/'%0D'}"
            echo "::set-output name=diff::$DIFF"
        - name: Find current PR
          uses: jwalton/gh-find-current-pr@v1
          id: findPr
        - name: Add Wily PR Comment
          uses: marocchino/sticky-pull-request-comment@v2
          if: steps.findPr.outputs.number && steps.wily.outputs.diff != ''
          with:
            recreate: true
            number: ${{ steps.findPr.outputs.number }}
            message: |
              ```
              ${{ steps.wily.outputs.diff }}
              ```
        - name: Add Wily PR Comment
          uses: marocchino/sticky-pull-request-comment@v2
          if: steps.findPr.outputs.number && steps.wily.outputs.diff == ''
          with:
            recreate: true
            number: ${{ steps.findPr.outputs.number }}
            message: |
              ```
              Wily: No changes in complexity detected.
              ```