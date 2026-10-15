"""Budget accounting of one paper (plan section 7.3).

Implements docs/validation/v0.3/wp2-acceptance.md, criteria W2.8 to W2.10a. The
accountant is deterministic and does no I/O. Every amount is an integer number of
microseconds of CPU time (cgroup ``usage_usec``), so no rounding enters a decision.

Pools and order:

- **setup**: the environment build and the shared downloads, charged first to the base
  pool (192 CPU-hours). ``end_setup()`` records S and fixes the base reserve per claim,
  ``(192 - S) // n_base``.
- **base**: the base reproduction of every claim, in the drawn order. A claim may use
  the balance of the pool minus the reserves of the claims that have not run yet.
- **attacks**: frozen by ``freeze_attacks()`` after all base runs. The pool is 192
  CPU-hours plus the base balance. Only the claims with the base obtained and at least
  one applicable attack take part (n_attack), in the drawn order, with the reserve
  ``pool // n_attack`` and the same sharing rule. n_attack = 0 is recorded as "no
  distribution". Nothing moves from the attacks back to the base.

Control during execution (W2.10a): before a container starts, ``grant()`` deducts its
reservation R = F + M from the authorized balance of its account. F is the stopping
threshold the runner enforces; M is the stopping margin, derived before the lock. At
every moment, charged usage plus the reservations of running containers stays within
the authorized balance. When a container ends, ``finish()`` replaces R by the real
usage. A usage above R is a breach, which makes the accounting invalid (a Refute error,
``INCONCLUSIVE``); a breach is never absorbed silently.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

USEC_PER_CPU_HOUR = 3_600 * 1_000_000
PAPER_LIMIT_USEC = 384 * USEC_PER_CPU_HOUR
BASE_POOL_USEC = 192 * USEC_PER_CPU_HOUR
ATTACK_POOL_BASE_USEC = 192 * USEC_PER_CPU_HOUR
BUDGET_EXHAUSTED = "budget_exhausted"


def cpu_hours(hours: int) -> int:
    """Whole CPU-hours in microseconds."""
    return hours * USEC_PER_CPU_HOUR


class Pool(enum.StrEnum):
    SETUP = "setup"
    BASE = "base"
    ATTACKS = "attacks"


class Phase(enum.StrEnum):
    SETUP = "setup"
    BASE = "base"
    ATTACKS = "attacks"
    CLOSED = "closed"


@dataclass(frozen=True)
class Account:
    pool: Pool
    claim: str | None = None

    def __str__(self) -> str:
        return self.pool.value if self.claim is None else f"{self.pool.value}:{self.claim}"


SETUP = Account(Pool.SETUP)


def base(claim: str) -> Account:
    return Account(Pool.BASE, claim)


def attack(claim: str) -> Account:
    return Account(Pool.ATTACKS, claim)


@dataclass(frozen=True)
class Decision:
    """The answer to a charge (W2.9)."""

    allowed: bool
    reason: str  # "" when allowed; "budget_exhausted", or why the account cannot charge
    pool: Pool
    available_usec: int  # what this account may still use now
    balance_usec: int  # what is left in the pool, after charges and reservations
    reserved_usec: int  # held for the claims of the pool that have not run yet


class BudgetRefusedError(Exception):
    """A grant was refused; ``decision`` holds the reason and the pool."""

    def __init__(self, decision: Decision, message: str) -> None:
        super().__init__(message)
        self.decision = decision


class RecordRejectedError(ValueError):
    """A usage record was rejected; the accountant is unchanged."""


@dataclass(frozen=True)
class Grant:
    container_id: str
    account: Account
    threshold_usec: int  # F: the runner stops the container when its usage reaches F
    margin_usec: int  # M: the usage allowed between the last reading and the stop
    reservation_usec: int  # R = F + M


@dataclass
class _Distribution:
    claims: list[str]
    total_usec: int
    reserve_usec: int
    done: list[str] = field(default_factory=list)


class Accountant:
    """The budget of one paper. Claims are given in the drawn order."""

    def __init__(
        self,
        claims: Sequence[str],
        *,
        margin_usec: int,
        base_pool_usec: int = BASE_POOL_USEC,
        attack_pool_base_usec: int = ATTACK_POOL_BASE_USEC,
    ) -> None:
        claims = list(claims)
        if not claims:
            raise ValueError("a paper needs at least one claim")
        if len(set(claims)) != len(claims):
            raise ValueError("claims must be unique")
        if margin_usec < 0 or base_pool_usec <= 0 or attack_pool_base_usec < 0:
            raise ValueError("the margin and the pools must be non-negative, the base positive")
        self.claims = claims
        self.margin_usec = margin_usec
        self.base_pool_usec = base_pool_usec
        self.attack_pool_base_usec = attack_pool_base_usec
        self.phase = Phase.SETUP
        self.setup_usec: int | None = None  # S, recorded by end_setup()
        self.base: _Distribution | None = None
        self.attacks: _Distribution | None = None
        self.no_distribution = False  # n_attack = 0
        self.charged: dict[Account, int] = {}
        self.running: dict[str, Grant] = {}
        self.records: dict[str, tuple[Account, int]] = {}
        self.invalid_reasons: list[str] = []
        self.log: list[str] = []

    # -- state ---------------------------------------------------------------------

    @property
    def accounting_valid(self) -> bool:
        return not self.invalid_reasons

    @property
    def setup_exhausted(self) -> bool:
        """The setup used the whole base pool: every claim is INCONCLUSIVE (setup)."""
        return (
            self.base is not None
            and self.base.reserve_usec == 0
            and (self._pool_balance(Pool.BASE) <= 0)
        )

    def _pool_of(self, account: Account) -> Pool:
        return Pool.ATTACKS if account.pool is Pool.ATTACKS else Pool.BASE

    def _used(self, pool: Pool) -> int:
        """Charged usage plus the reservations of running containers, in a pool."""
        charged = sum(u for a, u in self.charged.items() if self._pool_of(a) is pool)
        held = sum(
            g.reservation_usec for g in self.running.values() if self._pool_of(g.account) is pool
        )
        return charged + held

    def _pool_total(self, pool: Pool) -> int:
        if pool is Pool.BASE:
            return self.base_pool_usec
        return self.attacks.total_usec if self.attacks is not None else 0

    def _pool_balance(self, pool: Pool) -> int:
        return self._pool_total(pool) - self._used(pool)

    def _waiting_reserves(self, dist: _Distribution, claim: str) -> int:
        later = dist.claims[dist.claims.index(claim) + 1 :]
        return dist.reserve_usec * len([c for c in later if c not in dist.done])

    def _current(self, dist: _Distribution) -> str | None:
        pending = [c for c in dist.claims if c not in dist.done]
        return pending[0] if pending else None

    def _refusal(self, account: Account, reason: str) -> Decision:
        pool = account.pool
        balance = self._pool_balance(self._pool_of(account))
        return Decision(False, reason, pool, 0, balance, 0)

    def authorized(self, account: Account) -> Decision:
        """What ``account`` may use now, under the order and the sharing rule (W2.9)."""
        if account.claim is not None and account.claim not in self.claims:
            return self._refusal(account, f"unknown account {account}")
        if account.pool is Pool.SETUP:
            if self.phase is not Phase.SETUP:
                return self._refusal(account, "the setup account is closed")
            balance = self._pool_balance(Pool.BASE)
            return Decision(
                balance > 0,
                "" if balance > 0 else BUDGET_EXHAUSTED,
                Pool.SETUP,
                max(balance, 0),
                balance,
                0,
            )
        if account.pool is Pool.BASE:
            if self.phase is Phase.SETUP:
                return self._refusal(account, "the setup account is still open")
            if self.phase is not Phase.BASE:
                return self._refusal(
                    account, "no transfer from the attacks to the base reproduction"
                )
            dist = self.base
            pool = Pool.BASE
        else:
            if self.phase is not Phase.ATTACKS:
                return self._refusal(account, "the attack pool is not open")
            dist = self.attacks
            pool = Pool.ATTACKS
            if account.claim not in dist.claims:
                return self._refusal(account, f"{account.claim} is not eligible for attacks")
        current = self._current(dist)
        if account.claim != current:
            return self._refusal(
                account, f"claims run in the drawn order; the current claim is {current}"
            )
        balance = self._pool_balance(pool)
        reserved = self._waiting_reserves(dist, account.claim)
        available = balance - reserved
        if available <= 0:
            return Decision(
                False,
                BUDGET_EXHAUSTED,
                account.pool
                if pool is Pool.ATTACKS
                else (Pool.SETUP if self.setup_exhausted else Pool.BASE),
                0,
                balance,
                reserved,
            )
        return Decision(True, "", account.pool, available, balance, reserved)

    def decide(self, account: Account, amount_usec: int) -> Decision:
        """Whether a charge of ``amount_usec`` to ``account`` is allowed now (W2.9)."""
        if amount_usec < 0:
            raise ValueError("a charge cannot be negative")
        d = self.authorized(account)
        if d.allowed and amount_usec > d.available_usec:
            return Decision(
                False, BUDGET_EXHAUSTED, d.pool, d.available_usec, d.balance_usec, d.reserved_usec
            )
        return d

    # -- control during execution (W2.10a) -------------------------------------------

    def grant(self, account: Account, container_ids: Sequence[str]) -> list[Grant]:
        """Reserve R for each of k containers that start together for ``account``.

        Each gets R = available // k and F = R - M. The grant is refused when F is not
        positive; nothing is reserved then."""
        ids = list(container_ids)
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("container ids must be given, without duplicates")
        for cid in ids:
            if cid in self.running or cid in self.records:
                raise ValueError(f"container {cid} was already granted")
        d = self.authorized(account)
        if not d.allowed:
            raise BudgetRefusedError(d, f"grant refused for {account}: {d.reason} ({d.pool.value})")
        share = d.available_usec // len(ids)
        threshold = share - self.margin_usec
        if threshold <= 0:
            refused = Decision(
                False, BUDGET_EXHAUSTED, d.pool, d.available_usec, d.balance_usec, d.reserved_usec
            )
            raise BudgetRefusedError(
                refused,
                f"grant refused for {account}: {BUDGET_EXHAUSTED} ({d.pool.value}); "
                f"threshold {threshold} usec is not positive",
            )
        grants = [Grant(cid, account, threshold, self.margin_usec, share) for cid in ids]
        for g in grants:
            self.running[g.container_id] = g
        self.log.append(
            f"grant {account} x{len(ids)}: F={threshold} M={self.margin_usec} R={share}"
        )
        return grants

    def finish(self, container_id: str, account: Account, usage_usec: int) -> None:
        """The final record of a container, read once when it ends (W2.10)."""
        if usage_usec < 0:
            raise RecordRejectedError(f"negative usage for container {container_id}")
        if container_id in self.records:
            raise RecordRejectedError(f"container {container_id} recorded twice")
        if account.pool is not Pool.SETUP and account.claim not in self.claims:
            raise RecordRejectedError(f"unknown account {account}")
        grant = self.running.get(container_id)
        if grant is None:
            raise RecordRejectedError(f"container {container_id} has no reservation")
        if grant.account != account:
            raise RecordRejectedError(
                f"container {container_id} was granted to {grant.account}, not {account}"
            )
        del self.running[container_id]
        self.records[container_id] = (account, usage_usec)
        self.charged[account] = self.charged.get(account, 0) + usage_usec
        if usage_usec > grant.reservation_usec:
            self.invalid_reasons.append(
                f"breach: container {container_id} used {usage_usec} usec, above its "
                f"reservation {grant.reservation_usec}"
            )

    # -- phases ------------------------------------------------------------------------

    def _no_running(self, what: str) -> None:
        if self.running:
            raise ValueError(f"{what}: containers still running: {sorted(self.running)}")

    def end_setup(self) -> None:
        if self.phase is not Phase.SETUP:
            raise ValueError("the setup is already closed")
        self._no_running("end_setup")
        self.setup_usec = self.charged.get(SETUP, 0)
        remaining = max(self.base_pool_usec - self.setup_usec, 0)
        self.base = _Distribution(
            list(self.claims), self.base_pool_usec, remaining // len(self.claims)
        )
        self.phase = Phase.BASE
        self.log.append(f"setup S={self.setup_usec}; base reserve {self.base.reserve_usec}")

    def close_base(self, claim: str) -> None:
        if self.phase is not Phase.BASE or claim != self._current(self.base):
            raise ValueError(f"the current base claim is {self._current(self.base)}, not {claim}")
        self._no_running(f"close_base({claim})")
        self.base.done.append(claim)

    def freeze_attacks(self, eligible: Mapping[str, bool]) -> None:
        """After all base runs: freeze the eligible claims (base obtained and at least one
        applicable attack, fixed before the lock), the pool and the reserve."""
        if self.phase is not Phase.BASE or self._current(self.base) is not None:
            raise ValueError("the attack pool is frozen only after every base run")
        if set(eligible) != set(self.claims):
            raise ValueError("eligibility must be given for every claim")
        self._no_running("freeze_attacks")
        balance = max(self._pool_balance(Pool.BASE), 0)
        chosen = [c for c in self.claims if eligible[c]]
        total = self.attack_pool_base_usec + balance
        if not chosen:
            self.no_distribution = True
            self.attacks = _Distribution([], total, 0)
            self.phase = Phase.CLOSED
            self.log.append(f"attack pool {total}: n_attack = 0, no distribution")
            return
        self.attacks = _Distribution(chosen, total, total // len(chosen))
        self.phase = Phase.ATTACKS
        self.log.append(
            f"attack pool {total} (base balance {balance}); n_attack={len(chosen)}; "
            f"reserve {self.attacks.reserve_usec}"
        )

    def close_attack(self, claim: str) -> None:
        if self.phase is not Phase.ATTACKS or claim != self._current(self.attacks):
            raise ValueError(
                f"the current attack claim is {self._current(self.attacks)}, not {claim}"
            )
        self._no_running(f"close_attack({claim})")
        self.attacks.done.append(claim)
        if self._current(self.attacks) is None:
            self.phase = Phase.CLOSED

    # -- checks ------------------------------------------------------------------------

    def invariant_holds(self) -> bool:
        """Charged usage plus running reservations stay within each pool, and the
        reserves of the claims not yet run are untouched."""
        for pool in (Pool.BASE, Pool.ATTACKS):
            if pool is Pool.ATTACKS and self.attacks is None:
                continue
            dist = self.base if pool is Pool.BASE else self.attacks
            reserved = 0
            if dist is not None:
                current = self._current(dist)
                if current is not None:
                    reserved = self._waiting_reserves(dist, current)
            if self._used(pool) + reserved > self._pool_total(pool):
                return False
        return self.total_charged() <= self.base_pool_usec + self.attack_pool_base_usec

    def total_charged(self) -> int:
        return sum(self.charged.values())

    def check_completeness(self, parent_usage_usec: int, tolerance_usec: int) -> bool:
        """Compare the sum of the records with the usage of the paper's parent cgroup.

        A difference above the tolerance, or a container still without its final
        record, makes the accounting invalid (a Refute error, never a pass)."""
        if tolerance_usec < 0 or parent_usage_usec < 0:
            raise ValueError("the parent usage and the tolerance must be non-negative")
        if self.running:
            self.invalid_reasons.append(
                f"containers without a final record: {sorted(self.running)}"
            )
            return False
        difference = abs(parent_usage_usec - self.total_charged())
        if difference > tolerance_usec:
            self.invalid_reasons.append(
                f"records sum to {self.total_charged()} usec, the parent cgroup used "
                f"{parent_usage_usec} usec (difference {difference} > tolerance {tolerance_usec})"
            )
            return False
        return True
