"""LaminDB: Manage R&D data & analyses.

Import the package::

   import lamindb as ln
   import lamindb.schema as lns

The central class of the API is `DObject`, a wrapper for files, on-disk (`zarr`, etc.)
and in-memory data objects (`DataFrame`, `AnnData`, etc.).

.. autosummary::
   :toctree: .

   DObject
   DFolder

Data objects are transformed by runs:

.. autosummary::
   :toctree: .

   Run

Tracking data by features:

.. autosummary::
   :toctree: .

   Features

Query & manipulate data:

.. autosummary::
   :toctree: .

   select
   add
   delete

Manipulate data with open session:

.. autosummary::
   :toctree: .

   Session

View DB content:

.. autosummary::
   :toctree: .

   view

Schema - entities and their relations:

.. autosummary::
   :toctree: .

   schema

Setup:

.. autosummary::
   :toctree: .

   setup

Developer API:

.. autosummary::
   :toctree: .

   context
   settings
   dev
"""

__version__ = "0.32.0"  # denote a release candidate for 0.1.0 with 0.1rc1

# prints warning of python versions
from lamin_logger import logger as _logger
from lamin_logger import py_version_warning as _py_version_warning

_py_version_warning("3.8", "3.10")

from lndb import settings as _setup_settings
from lndb._migrate import check_deploy_migration as _check_migrate
from lndb.dev._settings_store import (
    current_instance_settings_file as _current_settings_file,
)

from . import _check_versions  # executes checks during import

_instance_setup = False
if (
    not _current_settings_file().exists()
    or _setup_settings.instance.storage.root is None
):
    _logger.warning(
        "You haven't yet setup an instance using the CLI. Please call"
        " `lamindb.setup.init()` or `lamindb.setup.load()`."
    )
else:
    try:
        _check_migrate(
            usettings=_setup_settings.user, isettings=_setup_settings.instance
        )
        _instance_setup = True
    except Exception:
        _logger.warning(
            "Your current instance cannot be reached, init or load a connectable"
            " instance."
        )

from lnschema_core import DFolder, DObject, Features, Run  # noqa

dobject_doc = """Data objects in storage & memory.

- Guide: :doc:`/guide/track`
- FAQ: :doc:`/faq/ingest`

A `DObject` is typically instantiated from data using the arguments below.
It can also be instantiated like any other SQLModel by passing all required
fields directly.

Args:
   data: Filepath or in-memory data.
   name: Name of the data object, required if an in-memory object is passed.
   source: The source of the data object (a :class:`~lamindb.Run`).
   id: The id of the dobject.
   format: Whether to use `h5ad` or `zarr` to store an `AnnData` object.

Data objects (`dobjects`) represent atomic datasets in object storage:
jointly measured observations of variables (features).
They are generated by running code, instances of :class:`~lamindb.Run`.

A `dobject` may contain a single observation, for instance, a single image.

Data objects often have canonical on-disk and in-memory representations. If
choices among these representations are made, a one-to-one mapping can be
achieved, which means that any given `dobject` has a default in-memory and
on-disk representation.

LaminDB offers meaningful default choices. For instance,

- It defaults to pandas DataFrames for in-memory representation of tables
  and allows you to configure loading tables into polars DataFrames.
- It defaults to the `.parquet` format for tables, but allows you to
  configure `.csv` or `.ipc`.

Some datasets do not have a canonical in-memory representation, for
instance, `.fastq`, `.vcf`, or files describing QC of datasets.

.. note:: Examples for storage ⟷ memory correspondence:

   - Table: `.csv`, `.tsv`, `.parquet`, `.ipc` (`.feather`) ⟷ `pd.DataFrame`, `polars.DataFrame`
   - Annotated matrix: `.h5ad`, `.h5mu`, `.zarrad` ⟷ `anndata.AnnData`, `mudata.MuData`
   - Image: `.jpg`, `.png` ⟷ `np.ndarray`, ...
   - Tensor: zarr directory, TileDB store ⟷ zarr loader, TileDB loader
   - Fastq: `.fastq` ⟷ /
   - VCF: `.vcf` ⟷ /
   - QC: `.html` ⟷ /

"""
DObject.__doc__ = dobject_doc


from . import dev  # noqa
from . import schema  # noqa
from . import setup  # noqa
from ._context import context  # noqa
from ._delete import delete  # noqa
from ._nb import nb  # noqa
from ._settings import settings
from ._subset import subset
from ._view import view  # noqa
from .dev.db import Session  # noqa
from .dev.db._add import add  # noqa
from .dev.db._select import select  # noqa
from .dev.object._lazy_field import lazy
