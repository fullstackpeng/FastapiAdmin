"""remove dept and position tables/columns

Revision ID: remove_dept_position_20251112
Revises: 
Create Date: 2025-11-12 00:00:00.000000

This migration only generates SQL to DROP dept/position related tables and the
`dept_id` column on `system_users`. It is intentionally destructive and will
NOT be run automatically by me. Review before applying on any environment.

Upgrade (apply):
  - DROP TABLE IF EXISTS system_role_depts
  - DROP TABLE IF EXISTS system_user_positions
  - DROP TABLE IF EXISTS system_positions
  - ALTER TABLE system_users DROP COLUMN IF EXISTS dept_id

Downgrade (rollback):
  - Recreate the dropped tables and the `dept_id` column with a reasonable
    structure and foreign keys. Adjust types/constraints to match your DB if
    you need exact original definitions.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_dept_position_20251112'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop dept/position related tables and user.dept_id column.

    WARNING: destructive. This only generates SQL — do NOT run until reviewed.
    """
    # Drop mapping tables and positions table if they exist
    op.execute("DROP TABLE IF EXISTS system_role_depts")
    op.execute("DROP TABLE IF EXISTS system_user_positions")
    op.execute("DROP TABLE IF EXISTS system_positions")

    # Drop dept_id column from users table if present (works on modern MySQL/Postgres)
    try:
        op.execute("ALTER TABLE system_users DROP COLUMN IF EXISTS dept_id")
    except Exception:
        # Some SQL flavors (older MySQL) don't support DROP COLUMN IF EXISTS;
        # try a safer approach: ignore errors to allow generation to succeed.
        pass


def downgrade() -> None:
    """Recreate dropped tables/column. Adjust types to match your DB engine.

    Note: This attempts to recreate reasonable defaults. If you need exact
    previous schema (indexes, comments, defaults), restore from a DB dump.
    """
    # Recreate positions table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_positions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            code VARCHAR(255),
            description TEXT,
            status TINYINT(1) DEFAULT 1,
            created_at DATETIME,
            updated_at DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # Recreate role <-> dept mapping table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_role_depts (
            role_id INT NOT NULL,
            dept_id INT NOT NULL,
            PRIMARY KEY (role_id, dept_id),
            KEY `dept_id` (dept_id),
            CONSTRAINT `fk_system_role_depts_dept` FOREIGN KEY (dept_id) REFERENCES system_dept(id) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # Recreate user <-> position mapping table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_user_positions (
            user_id INT NOT NULL,
            position_id INT NOT NULL,
            PRIMARY KEY (user_id, position_id),
            KEY `position_id` (position_id),
            CONSTRAINT `fk_system_user_positions_position` FOREIGN KEY (position_id) REFERENCES system_positions(id) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    # Add dept_id column back to users table (nullable) and restore index/foreign key
    op.execute(
        """
        ALTER TABLE system_users
        ADD COLUMN IF NOT EXISTS dept_id INT DEFAULT NULL,
        ADD INDEX IF NOT EXISTS ix_system_users_dept_id (dept_id)
        """
    )

    # Restore foreign key constraint (some DBs require different syntax)
    try:
        op.execute(
            """
            ALTER TABLE system_users
            ADD CONSTRAINT fk_system_users_dept FOREIGN KEY (dept_id) REFERENCES system_dept(id) ON DELETE SET NULL ON UPDATE CASCADE
            """
        )
    except Exception:
        # If adding FK fails (e.g., constraint already exists or DB flavor), ignore
        pass
