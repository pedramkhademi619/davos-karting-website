"""The accounting ledger: chart of accounts, journal, counters, suppliers, assets, budgets and till counts.

Besides the tables, the database itself protects the books so no code path, manual query or bug can damage them:

* a deferred constraint trigger refuses to commit a journal entry whose debits and credits differ (or that has fewer
  than two lines);
* journal lines can never be updated or deleted, and an entry may only change its status to "reversed" (and point at
  its reversing entry): a mistake is undone by a new entry, never by editing history.
"""
from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0015'
down_revision: Union[str, Sequence[str], None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FUNCTIONS = """
CREATE OR REPLACE FUNCTION accounting_check_entry_balanced() RETURNS trigger AS $$
DECLARE
    diff bigint;
    line_count integer;
    target uuid;
BEGIN
    IF TG_TABLE_NAME = 'accounting_journal_entries' THEN
        target := NEW.id;
    ELSE
        target := NEW.entry_id;
    END IF;
    SELECT COALESCE(SUM(debit_irr), 0) - COALESCE(SUM(credit_irr), 0), COUNT(*)
      INTO diff, line_count
      FROM accounting_journal_lines
     WHERE entry_id = target;
    IF line_count < 2 THEN
        RAISE EXCEPTION 'journal entry % has fewer than two lines', target USING ERRCODE = '23514';
    END IF;
    IF diff <> 0 THEN
        RAISE EXCEPTION 'journal entry % is not balanced: debit minus credit = %', target, diff
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting_lines_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'journal lines cannot be changed or deleted; post a reversing entry instead'
        USING ERRCODE = '23514';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting_entries_guard() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'journal entries cannot be deleted; post a reversing entry instead' USING ERRCODE = '23514';
    END IF;
    IF NEW.id <> OLD.id OR NEW.fiscal_year <> OLD.fiscal_year OR NEW.number <> OLD.number
       OR NEW.entry_date <> OLD.entry_date OR NEW.description <> OLD.description OR NEW.source <> OLD.source
       OR NEW.source_ref IS DISTINCT FROM OLD.source_ref OR NEW.source_date IS DISTINCT FROM OLD.source_date
       OR NEW.reversal_of_id IS DISTINCT FROM OLD.reversal_of_id OR NEW.created_by <> OLD.created_by
       OR NEW.created_at <> OLD.created_at THEN
        RAISE EXCEPTION 'a posted journal entry cannot be edited' USING ERRCODE = '23514';
    END IF;
    IF OLD.status = 'reversed' AND (NEW.status <> 'reversed' OR NEW.reversed_by_id IS DISTINCT FROM OLD.reversed_by_id) THEN
        RAISE EXCEPTION 'a reversed journal entry cannot be changed back' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGERS = """
CREATE CONSTRAINT TRIGGER accounting_lines_balanced
    AFTER INSERT ON accounting_journal_lines
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION accounting_check_entry_balanced();
CREATE CONSTRAINT TRIGGER accounting_entries_have_lines
    AFTER INSERT ON accounting_journal_entries
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION accounting_check_entry_balanced();
CREATE TRIGGER accounting_lines_never_change
    BEFORE UPDATE OR DELETE ON accounting_journal_lines
    FOR EACH ROW EXECUTE FUNCTION accounting_lines_immutable();
CREATE TRIGGER accounting_entries_guard
    BEFORE UPDATE OR DELETE ON accounting_journal_entries
    FOR EACH ROW EXECUTE FUNCTION accounting_entries_guard();
"""


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('accounting_accounts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('type', sa.String(length=16), nullable=False),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('is_group', sa.Boolean(), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('is_system', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("type IN ('asset', 'liability', 'equity', 'revenue', 'expense')", name=op.f('ck_accounting_accounts_type_valid')),
    sa.ForeignKeyConstraint(['parent_id'], ['accounting_accounts.id'], name=op.f('fk_accounting_accounts_parent_id_accounting_accounts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_accounts')),
    sa.UniqueConstraint('code', name=op.f('uq_accounting_accounts_code')),
    sa.UniqueConstraint('role', name=op.f('uq_accounting_accounts_role'))
    )
    op.create_table('accounting_counters',
    sa.Column('key', sa.String(length=40), nullable=False),
    sa.Column('value', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_accounting_counters'))
    )
    op.create_table('accounting_journal_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('fiscal_year', sa.Integer(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('entry_date', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=300), nullable=False),
    sa.Column('source', sa.String(length=24), nullable=False),
    sa.Column('source_ref', sa.String(length=80), nullable=True),
    sa.Column('source_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('reversed_by_id', sa.UUID(), nullable=True),
    sa.Column('reversal_of_id', sa.UUID(), nullable=True),
    sa.Column('created_by', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_journal_entries')),
    sa.UniqueConstraint('fiscal_year', 'number', name='uq_accounting_entries_year_number')
    )
    op.create_index('ix_accounting_entries_date', 'accounting_journal_entries', ['entry_date'], unique=False)
    op.create_index('uq_accounting_entries_auto_source', 'accounting_journal_entries', ['source', 'source_ref'], unique=True, postgresql_where=sa.text("source_ref IS NOT NULL AND source IN ('online_sale', 'counter_sale', 'recognition', 'refund')"))
    op.create_table('accounting_settings',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('id = 1', name=op.f('ck_accounting_settings_single_row')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_settings'))
    )
    op.create_table('accounting_vendors',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('phone', sa.String(length=20), server_default='', nullable=False),
    sa.Column('note', sa.String(length=300), server_default='', nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_vendors'))
    )
    op.create_table('accounting_budgets',
    sa.Column('account_id', sa.UUID(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('amount_irr', sa.BigInteger(), nullable=False),
    sa.CheckConstraint('month BETWEEN 1 AND 12 AND amount_irr > 0', name=op.f('ck_accounting_budgets_valid')),
    sa.ForeignKeyConstraint(['account_id'], ['accounting_accounts.id'], name=op.f('fk_accounting_budgets_account_id_accounting_accounts')),
    sa.PrimaryKeyConstraint('account_id', 'year', 'month', name=op.f('pk_accounting_budgets'))
    )
    op.create_table('accounting_cash_closings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('expected_irr', sa.BigInteger(), nullable=False),
    sa.Column('counted_irr', sa.BigInteger(), nullable=False),
    sa.Column('entry_id', sa.UUID(), nullable=True),
    sa.Column('note', sa.String(length=300), server_default='', nullable=False),
    sa.Column('closed_by', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['entry_id'], ['accounting_journal_entries.id'], name=op.f('fk_accounting_cash_closings_entry_id_accounting_journal_entries')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_cash_closings')),
    sa.UniqueConstraint('day', name=op.f('uq_accounting_cash_closings_day'))
    )
    op.create_table('accounting_fixed_assets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('asset_account_id', sa.UUID(), nullable=False),
    sa.Column('cost_irr', sa.BigInteger(), nullable=False),
    sa.Column('salvage_irr', sa.BigInteger(), nullable=False),
    sa.Column('in_service_date', sa.Date(), nullable=False),
    sa.Column('life_months', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('note', sa.String(length=300), server_default='', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('active', 'disposed')", name=op.f('ck_accounting_fixed_assets_status_valid')),
    sa.CheckConstraint('cost_irr > 0 AND salvage_irr >= 0 AND salvage_irr < cost_irr', name=op.f('ck_accounting_fixed_assets_cost_valid')),
    sa.CheckConstraint('life_months BETWEEN 1 AND 600', name=op.f('ck_accounting_fixed_assets_life_valid')),
    sa.ForeignKeyConstraint(['asset_account_id'], ['accounting_accounts.id'], name=op.f('fk_accounting_fixed_assets_asset_account_id_accounting_accounts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_fixed_assets'))
    )
    op.create_table('accounting_journal_lines',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('entry_id', sa.UUID(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.UUID(), nullable=False),
    sa.Column('debit_irr', sa.BigInteger(), nullable=False),
    sa.Column('credit_irr', sa.BigInteger(), nullable=False),
    sa.Column('memo', sa.String(length=300), server_default='', nullable=False),
    sa.Column('party_id', sa.UUID(), nullable=True),
    sa.CheckConstraint('(debit_irr = 0) <> (credit_irr = 0)', name=op.f('ck_accounting_journal_lines_one_side_only')),
    sa.CheckConstraint('debit_irr >= 0 AND credit_irr >= 0', name=op.f('ck_accounting_journal_lines_amounts_non_negative')),
    sa.ForeignKeyConstraint(['account_id'], ['accounting_accounts.id'], name=op.f('fk_accounting_journal_lines_account_id_accounting_accounts')),
    sa.ForeignKeyConstraint(['entry_id'], ['accounting_journal_entries.id'], name=op.f('fk_accounting_journal_lines_entry_id_accounting_journal_entries')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounting_journal_lines'))
    )
    op.create_index('ix_accounting_lines_account', 'accounting_journal_lines', ['account_id', 'entry_id'], unique=False)
    op.create_index('ix_accounting_lines_entry', 'accounting_journal_lines', ['entry_id'], unique=False)
    op.create_index('ix_accounting_lines_party', 'accounting_journal_lines', ['party_id'], unique=False)
    op.create_table('accounting_depreciation_runs',
    sa.Column('asset_id', sa.UUID(), nullable=False),
    sa.Column('month_key', sa.String(length=7), nullable=False),
    sa.Column('amount_irr', sa.BigInteger(), nullable=False),
    sa.Column('entry_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['accounting_fixed_assets.id'], name=op.f('fk_accounting_depreciation_runs_asset_id_accounting_fixed_assets')),
    sa.ForeignKeyConstraint(['entry_id'], ['accounting_journal_entries.id'], name=op.f('fk_accounting_depreciation_runs_entry_id_accounting_journal_entries')),
    sa.PrimaryKeyConstraint('asset_id', 'month_key', name=op.f('pk_accounting_depreciation_runs'))
    )

    # asyncpg runs one statement per call
    for statement in _FUNCTIONS.strip().split("\n\nCREATE OR REPLACE FUNCTION "):
        op.execute(statement if statement.startswith("CREATE") else "CREATE OR REPLACE FUNCTION " + statement)
    for statement in _TRIGGERS.strip().split(";\n"):
        if statement.strip():
            op.execute(statement.strip().rstrip(";"))

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS accounting_entries_guard ON accounting_journal_entries")
    op.execute("DROP TRIGGER IF EXISTS accounting_lines_never_change ON accounting_journal_lines")
    op.execute("DROP TRIGGER IF EXISTS accounting_entries_have_lines ON accounting_journal_entries")
    op.execute("DROP TRIGGER IF EXISTS accounting_lines_balanced ON accounting_journal_lines")
    op.execute("DROP FUNCTION IF EXISTS accounting_entries_guard()")
    op.execute("DROP FUNCTION IF EXISTS accounting_lines_immutable()")
    op.execute("DROP FUNCTION IF EXISTS accounting_check_entry_balanced()")
    op.drop_table('accounting_depreciation_runs')
    op.drop_index('ix_accounting_lines_party', table_name='accounting_journal_lines')
    op.drop_index('ix_accounting_lines_entry', table_name='accounting_journal_lines')
    op.drop_index('ix_accounting_lines_account', table_name='accounting_journal_lines')
    op.drop_table('accounting_journal_lines')
    op.drop_table('accounting_fixed_assets')
    op.drop_table('accounting_cash_closings')
    op.drop_table('accounting_budgets')
    op.drop_table('accounting_vendors')
    op.drop_table('accounting_settings')
    op.drop_index('uq_accounting_entries_auto_source', table_name='accounting_journal_entries', postgresql_where=sa.text("source_ref IS NOT NULL AND source IN ('online_sale', 'counter_sale', 'recognition', 'refund')"))
    op.drop_index('ix_accounting_entries_date', table_name='accounting_journal_entries')
    op.drop_table('accounting_journal_entries')
    op.drop_table('accounting_counters')
    op.drop_table('accounting_accounts')
