"""Runnable hook entry points.

Each submodule is invocable as ``python -m harnex_memory.hooks.<agent>`` and is
what the installed UserPromptSubmit hook calls. Using ``-m`` (with the active
interpreter) keeps the hook command stable for both pip and editable installs,
avoiding fragile absolute script paths.
"""
