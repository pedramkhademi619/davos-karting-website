import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.identity.application.use_cases.request_otp_command import RequestOtpCommand
from davos.modules.identity.application.use_cases.verify_otp_command import VerifyOtpCommand
from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.modules.identity.domain.errors.otp_verification_failed_error import OtpVerificationFailedError
from davos.modules.identity.domain.errors.session_not_found_error import SessionNotFoundError
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway

pytestmark = pytest.mark.integration

MOBILE = "09123456789"


async def _sign_in(container: ApplicationContainer, gateway: RecordingSmsGateway, mobile: str = MOBILE):
    await container.request_otp().execute(RequestOtpCommand(raw_mobile=mobile, client_ip="203.0.113.5"))
    code = gateway.sent[-1].parameters["code"]
    return await container.verify_otp().execute(
        VerifyOtpCommand(raw_mobile=mobile, code=code, client_ip="203.0.113.5", user_agent="pytest")
    )


async def test_full_sign_in_persists_user_session_and_outbox_event_atomically(
    container: ApplicationContainer, sms_gateway: RecordingSmsGateway, engine: AsyncEngine
) -> None:
    result = await _sign_in(container, sms_gateway)

    assert result.is_new_user
    async with engine.connect() as conn:
        users = (await conn.execute(text("SELECT mobile, status FROM identity_users"))).all()
        outbox = (await conn.execute(text("SELECT event_name, payload FROM outbox_messages"))).all()
        stored_digest = (await conn.execute(text("SELECT token_digest FROM identity_sessions"))).scalar_one()
        challenge = (await conn.execute(text("SELECT code_digest, consumed_at FROM identity_otp_challenges"))).one()

    assert users == [("+989123456789", "active")]
    assert [row[0] for row in outbox] == ["identity.UserRegistered"]
    assert outbox[0][1]["user_id"] == str(result.user_id)
    assert stored_digest != result.session_token
    assert challenge.consumed_at is not None
    assert sms_gateway.sent[-1].parameters["code"] not in challenge.code_digest


async def test_session_cookie_value_authenticates_and_logout_revokes(
    container: ApplicationContainer, sms_gateway: RecordingSmsGateway
) -> None:
    result = await _sign_in(container, sms_gateway)
    who = await container.authenticate_session().execute(result.session_token)
    assert who is not None and who.user_id == result.user_id

    await container.revoke_session().execute(user_id=result.user_id, session_id=result.session_id)
    assert await container.authenticate_session().execute(result.session_token) is None


async def test_another_customer_cannot_revoke_my_session(
    container: ApplicationContainer, sms_gateway: RecordingSmsGateway, clock
) -> None:
    mine = await _sign_in(container, sms_gateway)
    other = await _sign_in(container, sms_gateway, mobile="09129999999")
    with pytest.raises(SessionNotFoundError):
        await container.revoke_session().execute(user_id=other.user_id, session_id=mine.session_id)
    assert await container.authenticate_session().execute(mine.session_token) is not None


async def test_wrong_attempts_survive_in_the_database_and_lock_the_code(
    container: ApplicationContainer, sms_gateway: RecordingSmsGateway, engine: AsyncEngine
) -> None:
    await container.request_otp().execute(RequestOtpCommand(raw_mobile=MOBILE, client_ip="203.0.113.5"))
    real_code = sms_gateway.sent[-1].parameters["code"]
    wrong = "000000" if real_code != "000000" else "111111"
    for _ in range(3):
        with pytest.raises(OtpVerificationFailedError):
            await container.verify_otp().execute(
                VerifyOtpCommand(raw_mobile=MOBILE, code=wrong, client_ip="203.0.113.5", user_agent="t")
            )
    async with engine.connect() as conn:
        attempts = (await conn.execute(text("SELECT attempts FROM identity_otp_challenges"))).scalar_one()
    assert attempts == 3
    with pytest.raises(OtpVerificationFailedError) as info:
        await container.verify_otp().execute(
            VerifyOtpCommand(raw_mobile=MOBILE, code=real_code, client_ip="203.0.113.5", user_agent="t")
        )
    assert info.value.reason is OtpVerificationResult.LOCKED


async def test_concurrent_verification_of_one_code_yields_exactly_one_session(
    container: ApplicationContainer, sms_gateway: RecordingSmsGateway, engine: AsyncEngine
) -> None:
    await container.request_otp().execute(RequestOtpCommand(raw_mobile=MOBILE, client_ip="203.0.113.5"))
    code = sms_gateway.sent[-1].parameters["code"]

    async def attempt() -> object:
        return await container.verify_otp().execute(
            VerifyOtpCommand(raw_mobile=MOBILE, code=code, client_ip="203.0.113.5", user_agent="t")
        )

    outcomes = await asyncio.gather(*(attempt() for _ in range(8)), return_exceptions=True)
    successes = [o for o in outcomes if not isinstance(o, BaseException)]
    failures = [o for o in outcomes if isinstance(o, OtpVerificationFailedError)]
    assert len(successes) == 1
    assert len(failures) == 7
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM identity_sessions"))).scalar_one() == 1
        assert (await conn.execute(text("SELECT count(*) FROM identity_users"))).scalar_one() == 1


async def test_concurrent_first_logins_of_one_mobile_create_one_user(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    """Two different valid codes cannot exist at once, so drive the repository directly."""
    from davos.modules.identity.adapters.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
    from davos.modules.identity.domain.entities.user import User
    from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber

    mobile = MobileNumber.parse(MOBILE)

    async def register() -> bool:
        uow = container.new_unit_of_work()
        async with uow:
            _, created = await SqlAlchemyUserRepository(uow).add_or_get(
                User.register(mobile=mobile, now=container.clock.now())
            )
            await uow.commit()
            return created

    created = await asyncio.gather(*(register() for _ in range(10)))
    assert sum(created) == 1
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM identity_users"))).scalar_one() == 1


async def test_rolled_back_transaction_leaves_no_outbox_rows(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    from davos.modules.identity.domain.entities.user import User
    from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber

    user = User.register(mobile=MobileNumber.parse(MOBILE), now=container.clock.now())
    uow = container.new_unit_of_work()

    async def fail_before_commit() -> None:
        async with uow:
            uow.collect_events(user.pull_events())
            raise RuntimeError("boom")  # never committed

    with pytest.raises(RuntimeError, match="boom"):
        await fail_before_commit()
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM outbox_messages"))).scalar_one() == 0
