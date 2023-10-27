from typing import Type

from lnschema_core import Dataset, File, Registry

from lamindb._query_set import QuerySet


def filter(Registry: Type[Registry], **expressions) -> QuerySet:
    """See :meth:`~lamindb.dev.Registry.filter`."""
    if Registry in {File, Dataset}:
        # visibility is set to 0 by default
        visibility = "visibility"
        if not any([e.startswith(visibility) for e in expressions]):
            expressions[visibility] = 0
        # if visibility is None, do not apply a filter
        # otherwise, it would mean filtering for NULL values, which doesn't make
        # sense for a non-NULLABLE column
        elif visibility in expressions and expressions[visibility] is None:
            expressions.pop(visibility)
    qs = QuerySet(model=Registry)
    if len(expressions) > 0:
        return qs.filter(**expressions)
    else:
        return qs
