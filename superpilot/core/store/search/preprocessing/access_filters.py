from sqlalchemy.orm import Session

from super_store.access.access import get_acl_for_user
from super_store.db.models import User
from super_store.search.models import IndexFilters


def build_access_filters_for_user(user: User | None, session: Session) -> list[str]:
    user_acl = get_acl_for_user(user, session)
    return list(user_acl)


def build_user_only_filters(user: User | None, db_session: Session) -> IndexFilters:
    user_acl_filters = build_access_filters_for_user(user, db_session)
    return IndexFilters(
        source_type=None,
        document_set=None,
        time_cutoff=None,
        access_control_list=user_acl_filters,
    )
