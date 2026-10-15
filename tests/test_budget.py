"""Budget accounting (docs/validation/v0.3/wp2-acceptance.md, W2.8-W2.10a). Synthetic and
offline: a simulated meter stands in for the cgroup readings of WP3."""

import pytest

from refute.core.budget import (
    ATTACK_POOL_BASE_USEC,
    BASE_POOL_USEC,
    BUDGET_EXHAUSTED,
    PAPER_LIMIT_USEC,
    SETUP,
    Accountant,
    BudgetRefusedError,
    Phase,
    Pool,
    RecordRejectedError,
    attack,
    base,
    cpu_hours,
)

H = cpu_hours(1)
M = 1_000_000  # a 1 CPU-second margin for the plain accounting cases


def run(acc, account, cid, usage):
    """Grant one container to ``account`` and finish it with ``usage``."""
    (g,) = acc.grant(account, [cid])
    acc.finish(cid, account, usage)
    return g


def three_claims(setup_hours=30):
    acc = Accountant(["C1", "C2", "C3"], margin_usec=M)
    run(acc, SETUP, "build", cpu_hours(setup_hours))
    acc.end_setup()
    return acc


# W2.8: limits, pools, reserves ------------------------------------------------------------


def test_limits_are_384_192_192_in_microseconds():
    assert PAPER_LIMIT_USEC == 384 * 3_600_000_000
    assert BASE_POOL_USEC + ATTACK_POOL_BASE_USEC == PAPER_LIMIT_USEC


def test_plan_example_three_claims_s30_gives_54_hours_each():
    acc = three_claims(30)
    assert acc.setup_usec == cpu_hours(30)
    assert acc.base.reserve_usec == cpu_hours(54)


def test_charge_above_own_reserve_within_leftovers_is_allowed():
    acc = three_claims(30)
    run(acc, base("C1"), "c1", cpu_hours(30))
    acc.close_base("C1")
    d = acc.decide(base("C2"), cpu_hours(60))  # above 54, but 54 stays for C3
    assert d.allowed
    assert d.reserved_usec == cpu_hours(54)
    assert d.available_usec == cpu_hours(192 - 30 - 30 - 54)


def test_charge_above_balance_minus_reserves_is_refused():
    acc = three_claims(30)
    run(acc, base("C1"), "c1", cpu_hours(30))
    acc.close_base("C1")
    d = acc.decide(base("C2"), cpu_hours(79))  # 78 available
    assert not d.allowed
    assert d.reason == BUDGET_EXHAUSTED
    assert d.pool is Pool.BASE


def test_claims_run_in_the_drawn_order():
    acc = three_claims(30)
    d = acc.authorized(base("C2"))
    assert not d.allowed and "drawn order" in d.reason
    with pytest.raises(ValueError):
        acc.close_base("C2")


def test_setup_exhausting_the_base_pool_names_setup():
    acc = Accountant(["C1", "C2"], margin_usec=M)
    run(acc, SETUP, "build", BASE_POOL_USEC - 1)  # one microsecond left
    acc.end_setup()
    assert acc.base.reserve_usec == 0
    d = acc.authorized(base("C1"))
    assert d.allowed  # a few microseconds are left, not enough to run
    with pytest.raises(BudgetRefusedError) as refused:
        acc.grant(base("C1"), ["c1"])
    assert refused.value.decision.reason == BUDGET_EXHAUSTED
    acc2 = Accountant(["C1", "C2"], margin_usec=0, base_pool_usec=cpu_hours(10))
    run(acc2, SETUP, "build", cpu_hours(10))
    acc2.end_setup()
    assert acc2.setup_exhausted
    d2 = acc2.authorized(base("C1"))
    assert not d2.allowed and d2.reason == BUDGET_EXHAUSTED and d2.pool is Pool.SETUP


def test_attack_pool_frozen_after_base_runs_with_leftovers():
    acc = three_claims(30)
    for claim, used in (("C1", 30), ("C2", 60), ("C3", 40)):
        run(acc, base(claim), f"{claim}-base", cpu_hours(used))
        acc.close_base(claim)
    acc.freeze_attacks({"C1": True, "C2": False, "C3": True})
    leftovers = 192 - 30 - 30 - 60 - 40
    assert acc.attacks.total_usec == cpu_hours(192 + leftovers)
    assert acc.attacks.claims == ["C1", "C3"]  # drawn order kept
    assert acc.attacks.reserve_usec == cpu_hours(192 + leftovers) // 2
    assert acc.phase is Phase.ATTACKS


def test_attack_pool_is_frozen_only_after_every_base_run():
    acc = three_claims(30)
    with pytest.raises(ValueError):
        acc.freeze_attacks({"C1": True, "C2": True, "C3": True})


def test_n_attack_zero_is_no_distribution():
    acc = three_claims(30)
    for claim in ("C1", "C2", "C3"):
        acc.close_base(claim)
    acc.freeze_attacks({"C1": False, "C2": False, "C3": False})
    assert acc.no_distribution
    assert acc.phase is Phase.CLOSED
    assert any("no distribution" in line for line in acc.log)
    assert not acc.authorized(attack("C1")).allowed


def test_no_transfer_from_attacks_to_base():
    acc = three_claims(30)
    for claim in ("C1", "C2", "C3"):
        acc.close_base(claim)
    acc.freeze_attacks({"C1": True, "C2": True, "C3": True})
    d = acc.authorized(base("C1"))
    assert not d.allowed and "no transfer" in d.reason
    with pytest.raises(BudgetRefusedError):
        acc.grant(base("C3"), ["late"])


def test_attack_reserve_and_sharing_rule():
    acc = three_claims(30)
    for claim in ("C1", "C2", "C3"):
        acc.close_base(claim)
    acc.freeze_attacks({"C1": True, "C2": True, "C3": True})
    pool = acc.attacks.total_usec
    d = acc.authorized(attack("C1"))
    assert d.available_usec == pool - 2 * acc.attacks.reserve_usec
    assert not acc.authorized(attack("C2")).allowed  # not its turn


# W2.9: decisions and refusals ---------------------------------------------------------------


def test_every_refusal_names_the_pool():
    acc = three_claims(30)
    run(acc, base("C1"), "c1", cpu_hours(30))
    acc.close_base("C1")
    with pytest.raises(BudgetRefusedError) as refused:
        acc.grant(base("C2"), [f"c2-{i}" for i in range(10**6)])  # threshold below zero
    assert refused.value.decision.reason == BUDGET_EXHAUSTED
    assert "(base)" in str(refused.value)


# W2.10: records ------------------------------------------------------------------------------


def test_record_with_unknown_account_is_rejected():
    acc = Accountant(["C1"], margin_usec=M)
    acc.grant(SETUP, ["build"])
    with pytest.raises(RecordRejectedError):
        acc.finish("build", base("C9"), 10)


def test_same_container_twice_is_rejected():
    acc = Accountant(["C1"], margin_usec=M)
    run(acc, SETUP, "build", 10)
    with pytest.raises(RecordRejectedError):
        acc.finish("build", SETUP, 10)
    with pytest.raises(ValueError):
        acc.grant(SETUP, ["build"])


def test_negative_usage_and_ungranted_container_are_rejected():
    acc = Accountant(["C1"], margin_usec=M)
    acc.grant(SETUP, ["build"])
    with pytest.raises(RecordRejectedError):
        acc.finish("build", SETUP, -1)
    with pytest.raises(RecordRejectedError):
        acc.finish("ghost", SETUP, 1)
    acc.finish("build", SETUP, 5)
    assert acc.total_charged() == 5


def test_records_matching_the_parent_cgroup_are_complete():
    acc = Accountant(["C1"], margin_usec=M)
    run(acc, SETUP, "builder", 700)
    run(acc, SETUP, "build-rung-1-failed", 300)
    assert acc.check_completeness(parent_usage_usec=1_005, tolerance_usec=10)
    assert acc.accounting_valid


def test_records_differing_from_the_parent_cgroup_make_the_accounting_invalid():
    acc = Accountant(["C1"], margin_usec=M)
    run(acc, SETUP, "build-rung-1-failed", 300)  # the builder's record is left out
    assert not acc.check_completeness(parent_usage_usec=1_000, tolerance_usec=10)
    assert not acc.accounting_valid


def test_container_without_final_record_makes_the_accounting_invalid():
    acc = Accountant(["C1"], margin_usec=M)
    acc.grant(SETUP, ["build"])
    assert not acc.check_completeness(parent_usage_usec=0, tolerance_usec=0)


# W2.10a: control during execution, with a simulated meter -----------------------------------


class Meter:
    """Simulated containers in ticks of one CPU quota period.

    Each container consumes ``rate`` usec of CPU per tick and never stops on its own.
    The runner reads usage every ``read_every`` ticks; a reading shows the usage of
    ``delay`` ticks earlier. When a reading reaches F the runner stops the container,
    which keeps consuming for ``stop_latency`` more ticks."""

    def __init__(self, acc, grants, rate, read_every=1, delay=0, stop_latency=0, burst=None):
        self.acc, self.grants = acc, grants
        self.rate, self.read_every, self.delay, self.stop_latency = (
            rate,
            read_every,
            delay,
            stop_latency,
        )
        self.burst = burst  # (tick, usec): one tick that uses a whole extra quota period
        self.history = {g.container_id: [0] for g in grants}

    def run(self, check):
        stopping = {}
        tick = 0
        live = {g.container_id: True for g in self.grants}
        while any(live.values()):
            tick += 1
            for g in self.grants:
                cid = g.container_id
                if not live[cid]:
                    continue
                used = self.history[cid][-1] + self.rate
                if self.burst and self.burst[0] == tick:
                    used += self.burst[1]
                self.history[cid].append(used)
                if cid in stopping:
                    stopping[cid] -= 1
                    if stopping[cid] < 0:
                        live[cid] = False
                        self.history[cid].pop()  # stopped before this tick's work
                        self.acc.finish(cid, g.account, self.history[cid][-1])
                    continue
                if tick % self.read_every == 0:
                    seen = self.history[cid][max(0, len(self.history[cid]) - 1 - self.delay)]
                    if seen >= g.threshold_usec:
                        stopping[cid] = self.stop_latency
            check({cid: self.history[cid][-1] for cid in live if live[cid]})
        return {cid: h[-1] for cid, h in self.history.items()}


def margin_for(rate, read_every, delay, stop_latency, burst=0):
    """M derived from the quota period, the reading interval, the reading delay and the
    stopping latency (the WP3 acceptance revision derives the real values)."""
    return rate * (read_every + delay + stop_latency + 1) + burst


def checked(acc, account_pool, claim):
    """A check, at every simulated step, that charged usage plus the live usage of the
    running containers stays within the authorized balance, so the reserves of the
    claims not yet run stay intact."""

    def check(live):
        assert acc.invariant_holds()
        dist = acc.base if account_pool is Pool.BASE else acc.attacks
        authorized = acc._pool_total(account_pool) - acc._waiting_reserves(dist, claim)
        charged = sum(u for a, u in acc.charged.items() if acc._pool_of(a) is account_pool)
        assert charged + sum(live.values()) <= authorized

    return check


SCENARIOS = {
    "two concurrent containers, no stop of their own": dict(read_every=1, delay=0, stop=0),
    "a burst that uses a whole quota period at once": dict(read_every=2, delay=0, stop=0, burst=1),
    "a reading delayed by the maximum sampling delay": dict(read_every=2, delay=3, stop=0),
    "a slow stop": dict(read_every=1, delay=0, stop=4),
}


@pytest.mark.parametrize("name", SCENARIOS)
def test_in_run_control_keeps_the_invariant_and_the_reserves(name):
    s = SCENARIOS[name]
    rate = cpu_hours(1) + 1_234_567  # not a divisor of F, so a step crosses F
    burst = rate if s.get("burst") else 0
    margin = margin_for(rate, s["read_every"], s["delay"], s["stop"], burst)
    acc = Accountant(["C1", "C2", "C3"], margin_usec=margin)
    run(acc, SETUP, "build", cpu_hours(30))
    acc.end_setup()
    grants = acc.grant(base("C1"), ["seed-1", "seed-2"])  # two containers in parallel
    assert all(g.threshold_usec > 0 for g in grants)
    # the burst falls on the last tick below F, between two readings
    burst_tick = grants[0].threshold_usec // rate
    meter = Meter(
        acc,
        grants,
        rate,
        s["read_every"],
        s["delay"],
        s["stop"],
        (burst_tick, burst) if burst else None,
    )
    final = meter.run(checked(acc, Pool.BASE, "C1"))
    assert acc.accounting_valid, acc.invalid_reasons
    assert all(final[g.container_id] <= g.reservation_usec for g in grants)
    # the case is exercised: each container went past F, into its margin
    assert all(final[g.container_id] > g.threshold_usec for g in grants)
    if burst:  # the burst is part of the final usage
        assert all(final[g.container_id] >= burst_tick * rate + burst for g in grants)
    assert acc.base.reserve_usec * 2 <= acc._pool_balance(Pool.BASE)  # C2, C3 intact


def test_both_concurrent_containers_using_their_whole_margin():
    acc = three_claims(30)
    grants = acc.grant(base("C1"), ["a", "b"])
    for g in grants:  # each stops exactly at F + M = R
        acc.finish(g.container_id, g.account, g.reservation_usec)
    assert acc.accounting_valid and acc.invariant_holds()
    acc.close_base("C1")
    assert acc.authorized(base("C2")).reserved_usec == acc.base.reserve_usec


def test_claim_at_its_limit_with_claims_after_it():
    acc = three_claims(30)
    (g,) = acc.grant(base("C1"), ["c1"])
    assert g.reservation_usec == cpu_hours(192 - 30 - 2 * 54)  # all but C2 and C3 reserves
    acc.finish("c1", base("C1"), g.reservation_usec)
    acc.close_base("C1")
    assert acc.authorized(base("C2")).available_usec == cpu_hours(54)


def test_usage_above_the_reservation_is_a_breach():
    rate = cpu_hours(1)
    acc = Accountant(["C1", "C2"], margin_usec=rate)  # too small for a stop latency of 4
    acc.end_setup()
    grants = acc.grant(base("C1"), ["c1"])
    Meter(acc, grants, rate, stop_latency=4).run(lambda live: None)
    assert not acc.accounting_valid
    assert "breach" in acc.invalid_reasons[0]


def test_grant_whose_reservation_exceeds_what_is_available_is_refused():
    acc = three_claims(30)
    big_margin = Accountant(["C1", "C2", "C3"], margin_usec=cpu_hours(100))
    run(big_margin, SETUP, "build", cpu_hours(30))
    big_margin.end_setup()
    with pytest.raises(BudgetRefusedError):  # F = 54 - 100 is not positive
        big_margin.grant(base("C1"), ["c1"])
    assert not big_margin.running
    assert acc.grant(base("C1"), ["c1"])  # the same claim with a small margin
