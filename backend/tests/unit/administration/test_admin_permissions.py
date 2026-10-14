from __future__ import annotations

from datetime import UTC, datetime

from davos.modules.administration.domain.entities.admin_user import AdminUser
from davos.modules.administration.domain.enums.admin_permission import AdminPermission as P
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.modules.administration.domain.services.permission_catalog import PermissionCatalog

NOW = datetime(2026, 10, 14, tzinfo=UTC)


def user(role: AdminRole, permissions: frozenset[P] | None = None) -> AdminUser:
    return AdminUser.create(
        username="reza", display_name="رضا", password_hash="x", role=role, now=NOW, permissions=permissions
    )


def test_every_permission_is_described_exactly_once() -> None:
    keys = [entry.permission for entry in PermissionCatalog.ENTRIES]
    assert len(keys) == len(set(keys)) and set(keys) == set(P)
    assert all(entry.label and entry.description for entry in PermissionCatalog.ENTRIES)


def test_managing_a_section_includes_looking_at_it() -> None:
    assert PermissionCatalog.closure({P.SETTINGS_MANAGE}) == {P.SETTINGS_MANAGE, P.SETTINGS}
    assert PermissionCatalog.closure({P.ASSISTANT_MANAGE, P.SMS}) == {P.ASSISTANT_MANAGE, P.ASSISTANT, P.SMS}
    assert PermissionCatalog.closure(set()) == frozenset()


def test_the_owner_can_do_everything_whatever_is_stored() -> None:
    owner = user(AdminRole.OWNER, frozenset({P.SMS}))
    assert owner.effective_permissions() == PermissionCatalog.everything()


def test_staff_start_with_the_defaults_and_can_be_given_exactly_what_the_owner_picks() -> None:
    staff = user(AdminRole.STAFF)
    assert staff.effective_permissions() == PermissionCatalog.STAFF_DEFAULTS
    assert P.ACCOUNTING not in staff.effective_permissions() and P.SETTINGS_MANAGE not in staff.effective_permissions()
    staff.set_permissions(frozenset({P.ACCOUNTING}))
    assert staff.effective_permissions() == {P.ACCOUNTING}
    staff.set_permissions(frozenset({P.SETTINGS_MANAGE}))
    assert staff.effective_permissions() == {P.SETTINGS_MANAGE, P.SETTINGS}
    staff.set_permissions(None)
    assert staff.effective_permissions() == PermissionCatalog.STAFF_DEFAULTS


def test_presets_only_use_known_permissions_and_the_defaults_keep_the_old_staff_behaviour() -> None:
    for preset in PermissionCatalog.PRESETS:
        assert preset.permissions <= PermissionCatalog.everything() and preset.permissions == PermissionCatalog.closure(
            preset.permissions
        )
    assert PermissionCatalog.closure(PermissionCatalog.STAFF_DEFAULTS) == PermissionCatalog.STAFF_DEFAULTS
