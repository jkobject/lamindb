import lnschema_core as core
from lamin_logger import logger
from lndb_setup import settings

from .dev._core import filepath_from_dobject
from .dev.file import load_to_memory


def populate_runin(dobject: core.DObject, run: core.Run):
    settings.instance._cloud_sqlite_locker.lock()
    with settings.instance.session() as ss:
        result = ss.get(core.link.RunIn, (run.id, dobject.id))
        if result is None:
            ss.add(
                core.link.RunIn(
                    run_id=run.id,
                    dobject_id=dobject.id,
                )
            )
            ss.commit()
            logger.info(f"Added dobject ({dobject.id}) as input for run ({run.id}).")
            settings.instance._update_cloud_sqlite_file()
    settings.instance._cloud_sqlite_locker.unlock()


# this is exposed to the user as DObject.load
def load(dobject: core.DObject, stream: bool = False):
    if stream and dobject.suffix not in (".h5ad", ".zarr"):
        logger.warning(f"Ignoring stream option for a {dobject.suffix} object.")

    filepath = filepath_from_dobject(dobject)
    # TODO: better design to track run inputs and usage
    # from lamindb import nb

    # if nb.run is None:
    #     logger.warning(
    #         "Input tracking for runs through `load` is currently only implemented for"
    #         " notebooks."
    #     )
    # else:
    #     populate_runin(dobject, nb.run)
    # track_usage(dobject.id, "load")
    return load_to_memory(filepath, stream=stream)
