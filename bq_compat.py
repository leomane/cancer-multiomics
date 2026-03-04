"""Compatibility shim for running BQ Studio notebooks locally.

BQ Studio notebooks use google.colab.sql and google.colabsqlviz, which only
exist inside the BQ Studio runtime. This module installs lightweight shims
into sys.modules so the same notebook cells work unchanged in a local Jupyter
kernel.

Usage (in the notebook's first cell):
    try:
        from google.colab.sql import bigquery as _test  # BQ Studio
    except ImportError:
        import bq_compat
        bq_compat.install(client)  # client = bigquery.Client(...)
"""

import sys
import types


def install(client):
    """Patch sys.modules so google.colab.sql and google.colabsqlviz resolve."""

    # --- google.colab.sql shim -------------------------------------------
    class _BigQueryRunner:
        """Drop-in for google.colab.sql.bigquery with a .run(sql) method."""

        def run(self, sql):
            return client.query(sql).to_dataframe()

    colab_mod = types.ModuleType("google.colab")
    sql_mod = types.ModuleType("google.colab.sql")
    sql_mod.bigquery = _BigQueryRunner()

    sys.modules.setdefault("google.colab", colab_mod)
    sys.modules["google.colab.sql"] = sql_mod

    # --- google.colabsqlviz shim -----------------------------------------
    # Cells do:
    #   import google.colabsqlviz.explore_dataframe as _vizcell
    #   _vizcell.explore_dataframe(df_or_df_name='some_df', ...)

    def _explore_dataframe(df_or_df_name="", **kwargs):
        """No-op replacement that just displays the dataframe."""
        import inspect

        frame = inspect.currentframe().f_back
        df = frame.f_globals.get(df_or_df_name)
        if df is not None:
            try:
                from IPython.display import display
                display(df)
            except ImportError:
                print(df)

    viz_parent = types.ModuleType("google.colabsqlviz")
    viz_ed = types.ModuleType("google.colabsqlviz.explore_dataframe")
    viz_ed.explore_dataframe = _explore_dataframe
    viz_parent.explore_dataframe = viz_ed

    sys.modules["google.colabsqlviz"] = viz_parent
    sys.modules["google.colabsqlviz.explore_dataframe"] = viz_ed
