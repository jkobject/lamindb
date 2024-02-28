import lamindb as ln
from lamindb.dev._run_context import get_transform_kwargs_from_stem_uid


def test_track_with_multi_parents():
    parent1 = ln.Transform(name="parent 1")
    parent1.save()
    parent2 = ln.Transform(name="parent 2")
    parent2.save()
    child = ln.Transform(name="Child")
    child.save()
    child.parents.set([parent1, parent2])
    ln.track(child, reference="my address", reference_type="url")
    # unset to remove side effects
    ln.dev.run_context.run = None
    ln.dev.run_context.transform = None


def test_track_with_reference():
    transform = ln.Transform(name="test")
    ln.track(transform, reference="my address", reference_type="url")
    assert ln.dev.run_context.run.reference == "my address"
    assert ln.dev.run_context.run.reference_type == "url"
    # unset to remove side effects
    ln.dev.run_context.run = None
    ln.dev.run_context.transform = None


def test_track_notebook_colab():
    notebook_path = "/fileId=1KskciVXleoTeS_OGoJasXZJreDU9La_l"
    ln.dev.run_context._track_notebook(path=notebook_path)


def test_get_transform_kwargs_from_stem_uid():
    title = "title"
    transform, uid, version = get_transform_kwargs_from_stem_uid(
        stem_uid="NJvdsWWbJlZS",
        version="0",
    )
    assert transform is None
    assert uid == "NJvdsWWbJlZS6K79"
    assert version == "0"
    ln.Transform(uid=uid, version=version, name=title).save()
    transform, uid, version = get_transform_kwargs_from_stem_uid(
        stem_uid="NJvdsWWbJlZS",
        version="0",
    )
    assert transform is not None
    transform, uid, version = get_transform_kwargs_from_stem_uid(
        stem_uid="NJvdsWWbJlZS",
        version="1",
    )
    assert transform is None
    assert uid.startswith("NJvdsWWbJlZS")
    assert version == "1"
