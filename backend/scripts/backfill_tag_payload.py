"""一次性回填 Qdrant chunk payload 中的 tag_ids."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from storage.db_bootstrap import seed_default_data
from storage.models.file import File
from storage.mysql_db import get_db_session
from tag.tag_service import TagService


def main() -> None:
    seed_default_data()
    tag_service = TagService()
    with get_db_session() as session:
        files = list(session.scalars(select(File)).all())

    for record in files:
        tag_service.sync_tags_to_qdrant(record.id)
        print(f"Synced tags for {record.filename} ({record.id})")


if __name__ == "__main__":
    main()
