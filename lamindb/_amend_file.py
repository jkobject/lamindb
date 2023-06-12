from pathlib import Path
from typing import Optional

from anndata import AnnData
from anndata import __version__ as anndata_v
from lamin_logger import logger
from lamindb_setup import settings as setup_settings
from lnschema_core import File
from lnschema_core.types import DataLike
from packaging import version

from lamindb._context import context
from lamindb._file_access import filepath_from_file_or_folder
from lamindb.dev import LazyDataFrame
from lamindb.dev.storage import load_to_memory
from lamindb.dev.storage.object import _subset_anndata_file
from lamindb.dev.storage.object._anndata_accessor import AnnDataAccessor

from ._settings import settings

File.__doc__ = """Files: data artifacts.

Args:
   data: `Union[PathLike, DataLike]` A file path or an in-memory data
      object (`DataFrame`, `AnnData`) to serialize. Can be a cloud path, e.g.,
      `"s3://my-bucket/my_samples/my_file.fcs"`.
   key: `Optional[str] = None` A storage key: a relative filepath within the
      current default storage, e.g., `"my_samples/my_file.fcs"`.
   name: `Optional[str] = None` A name. Defaults to the filename.
   run: `Optional[Run] = None` The run that created the file.

Track where files come from by passing the generating :class:`~lamindb.Run`.

Often, files store jointly measured observations of features: track them
with :class:`~lamindb.FeatureSet`.

If files have corresponding representations in storage and memory, LaminDB
makes some configurable default choices (e.g., serialize a `DataFrame` as a
`.parquet` file).

.. admonition:: Examples for storage-memory correspondence

   Listed are typical `suffix` values & in memory data objects.

   - Table: `.csv`, `.tsv`, `.parquet`, `.ipc`
     ⟷ `pd.DataFrame`, `polars.DataFrame`
   - Annotated matrix: `.h5ad`, `.h5mu`, `.zrad` ⟷ `AnnData`, `MuData`
   - Image: `.jpg`, `.png` ⟷ `np.ndarray`, ...
   - Array: zarr directory, TileDB store ⟷ zarr loader, TileDB loader
   - Fastq: `.fastq` ⟷ /
   - VCF: `.vcf` ⟷ /
   - QC: `.html` ⟷ /

"""


def backed(file: File, is_run_input: Optional[bool] = None) -> AnnDataAccessor:
    """Return a cloud-backed AnnData object for streaming."""
    _track_run_input(file, is_run_input)
    if file.suffix not in (".h5ad", ".zrad", ".zarr"):
        raise ValueError("File should have an AnnData object as the underlying data")
    return AnnDataAccessor(file)


def subsetter(self: File) -> LazyDataFrame:
    """A subsetter to pass to ``.stream()``.

    Currently, this returns an instance of an
    unconstrained :class:`~lamindb.dev.LazyDataFrame`
    to be evaluated in ``.stream()``.

    In the future, this will be constrained by metadata of the file, it's
    feature- and sample-level descriptors, like `.obs`, `.var`, `.columns`, `.rows`.
    """
    return LazyDataFrame()


def stream(
    self: File,
    subset_obs: Optional[LazyDataFrame] = None,
    subset_var: Optional[LazyDataFrame] = None,
    is_run_input: Optional[bool] = None,
) -> AnnData:
    """Stream the file into memory. Allows subsetting an AnnData object.

    Args:
        subset_obs: ``Optional[LazyDataFrame] = None`` - A DataFrame query to
            evaluate on ``.obs`` of an underlying ``AnnData`` object.
        subset_var: ``Optional[LazyDataFrame] = None`` - A DataFrame query to
            evaluate on ``.var`` of an underlying ``AnnData`` object.

    Returns:
        The streamed AnnData object.

    Example:

    >>> file = ln.select(ln.File, ...).one()
    >>> obs = file.subsetter()
    >>> obs = (
    >>>     obs.cell_type.isin(["dendritic cell", "T cell")
    >>>     & obs.disease.isin(["Alzheimer's"])
    >>> )
    >>> file.stream(subset_obs=obs, is_run_input=True)

    """
    if self.suffix not in (".h5ad", ".zarr"):
        raise ValueError("File should have an AnnData object as the underlying data")
    _track_run_input(self, is_run_input)

    if subset_obs is None and subset_var is None:
        return load_to_memory(filepath_from_file_or_folder(self), stream=True)

    if self.suffix == ".h5ad" and subset_obs is not None and subset_var is not None:
        raise ValueError(
            "Can not subset along both subset_obs and subset_var at the same time"
            " for an AnnData object stored as a h5ad file."
            " Please resave your AnnData as zarr to be able to do this"
        )

    if self.suffix == ".zarr" and version.parse(anndata_v) < version.parse("0.9.1"):
        raise ValueError(
            f"anndata=={anndata_v} does not support `.subset` of zarr stored AnnData."
            " Please install anndata>=0.9.1"
        )

    return _subset_anndata_file(self, subset_obs, subset_var)  # type: ignore


def _track_run_input(file: File, is_run_input: Optional[bool] = None):
    if is_run_input is None:
        if context.run is not None:
            logger.hint("Track this file as a run input by passing `is_run_input=True`")
        track_run_input = settings.track_run_inputs_upon_load
    else:
        track_run_input = is_run_input
    if track_run_input:
        if context.run is None:
            raise ValueError(
                "No global run context set. Call ln.context.track() or link input to a"
                " run object via `run.inputs.append(file)`"
            )
        if not file.input_of.contains(context.run):
            context.run.save()
            file.input_of.add(context.run)


def load(file: File, is_run_input: Optional[bool] = None) -> DataLike:
    """Stage and load to memory.

    Returns in-memory representation if possible, e.g., an `AnnData` object
    for an `h5ad` file.
    """
    _track_run_input(file, is_run_input)
    return load_to_memory(filepath_from_file_or_folder(file))


def stage(file: File, is_run_input: Optional[bool] = None) -> Path:
    """Update cache from cloud storage if outdated.

    Returns a path to a locally cached on-disk object (say, a
    `.jpg` file).
    """
    if file.suffix in (".zrad", ".zarr"):
        raise RuntimeError("zarr object can't be staged, please use load() or stream()")
    _track_run_input(file, is_run_input)
    return setup_settings.instance.storage.cloud_to_local(
        filepath_from_file_or_folder(file)
    )


File.backed = backed
File.stage = stage
File.subsetter = subsetter
File.stream = stream
File.load = load
