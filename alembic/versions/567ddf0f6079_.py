"""Add import and export actions

Revision ID: 567ddf0f6079
Revises: 3bc33da5cbd2
Create Date: 2014-01-06 19:37:25.882521

"""

# revision identifiers, used by Alembic.
revision = '567ddf0f6079'
down_revision = '3bc33da5cbd2'

from alembic import op
import sqlalchemy as sa


INSERTS = """"""
DELETES = """
DELETE FROM actions where name = 'Import'
DELETE FROM actions where name = 'Export'
"""


def iter_statements(stmts):
    for st in stmts.split('\n'):
        op.execute(st)


def upgrade():
    conn = op.get_bind()
    res = conn.execute("select * from modules")
    results = res.fetchall()
    for r in results:
        stmnt = "INSERT into actions (mid, name, url, icon) VALUES (%s, 'Export', 'export/{id}', 'icon-export')" % r[0]
        op.execute(stmnt)
        stmnt = "INSERT into actions (mid, name, url, icon) VALUES (%s, 'Import', 'import', 'icon-import')" % r[0]
        op.execute(stmnt)
    iter_statements(INSERTS)


def downgrade():
    pass
    iter_statements(DELETES)
