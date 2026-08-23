from src.core.servers import ServerEligibility


MAIN_SERVER_ID = 123456789


def test_server_with_twenty_humans_is_eligible():
    eligibility = ServerEligibility()

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=20,
    ) is True


def test_server_with_more_than_twenty_humans_is_eligible():
    eligibility = ServerEligibility()

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=100,
    ) is True


def test_server_with_nineteen_humans_is_not_eligible():
    eligibility = ServerEligibility()

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=19,
    ) is False


def test_server_with_zero_humans_is_not_eligible():
    eligibility = ServerEligibility()

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=0,
    ) is False


def test_bots_are_not_part_of_the_count():
    eligibility = ServerEligibility()

    # The caller supplies the number of actual human members.
    # 50 total members with only 3 humans therefore means 3.
    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=3,
    ) is False


def test_main_server_bypasses_human_requirement():
    eligibility = ServerEligibility(
        main_server_id=MAIN_SERVER_ID,
    )

    assert eligibility.is_eligible(
        server_id=MAIN_SERVER_ID,
        human_member_count=0,
    ) is True


def test_other_server_cannot_use_main_server_bypass():
    eligibility = ServerEligibility(
        main_server_id=MAIN_SERVER_ID,
    )

    assert eligibility.is_eligible(
        server_id=999999999,
        human_member_count=0,
    ) is False


def test_server_id_is_exact():
    eligibility = ServerEligibility(
        main_server_id=MAIN_SERVER_ID,
    )

    assert eligibility.is_eligible(
        server_id=MAIN_SERVER_ID + 1,
        human_member_count=19,
    ) is False


def test_requirement_can_be_configured():
    eligibility = ServerEligibility(
        minimum_human_members=50,
    )

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=49,
    ) is False

    assert eligibility.is_eligible(
        server_id=1,
        human_member_count=50,
    ) is True