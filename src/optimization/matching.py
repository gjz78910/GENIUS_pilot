"""Job-to-engineer assignment logic.

Overview
--------
Given a set of engineers and jobs, assign each job to an engineer such that:
- The engineer has the required skills
- The engineer's total workload (job time + travel time) fits within working hours
- As many jobs as possible are assigned

    Engineers                Jobs              Result
    ┌──────────┐           ┌──────┐
    │ Alice    │◄──────────│ J1   │          Alice: [J1, J3]
    │ repair,  │     ┌─────│ J2   │          Bob:   [J2, J4]
    │ install  │     │     │ J3   │          Unassigned: []
    ├──────────┤     │     │ J4   │
    │ Bob      │◄────┘     └──────┘
    │ repair   │
    └──────────┘

The main entry point is `assign_jobs`, which delegates to a pluggable
matching strategy.

Strategy Pattern
----------------
    ┌────────────────┐
    │  assign_jobs   │  ◄── public entry point
    └───────┬────────┘
            │ delegates to
            ▼
    ┌────────────────────┐
    │ MatchingStrategy   │  ◄── abstract base class
    └───────┬────────────┘
            │
     ┌──────┴───────────────────────┐
     │                              │
     ▼                              ▼
    ┌───────────────┐   ┌───────────────────────────┐
    │ Greedy        │   │ ConstrainedGreedy         │  ◄── default
    │ O(j·e)       │   │ O(j·e·log j)             │
    │ fast, naive   │   │ + swap for small inputs   │
    └───────────────┘   └───────────────────────────┘

Usage:
    # Default (constrained greedy + swap for small):
    assignments, unassigned = assign_jobs(engineers, jobs, matrix)

    # Explicit greedy-only:
    assignments, unassigned = assign_jobs(engineers, jobs, matrix, strategy=GreedyStrategy())

    # Custom strategy:
    matching.DEFAULT_STRATEGY = MyCustomStrategy()

Implementing a new strategy:
    Subclass `MatchingStrategy` and implement `assign()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from src.models.engineer import Engineer
from src.models.job import Job
from src.optimization.routing import find_optimal_route


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_capable_engineers(job: Job, engineers: List[Engineer]) -> List[Engineer]:
    """Return engineers who possess ALL skills required by a job.

    Example:
        Job requires: [repair, install]
        Alice skills: [repair, install, inspect]  ◄── capable
        Bob skills:   [repair]                    ◄── NOT capable (missing install)

    Note
    ----
    This is the simple O(e) scan used by the greedy strategy and tests.
    For repeated lookups over the same engineer pool, prefer
    `SkillIndex`, which answers the same query in roughly O(required_skills)
    via precomputed skill→engineer sets.
    """
    return [
        engineer
        for engineer in engineers
        if all(skill in engineer.skills for skill in job.required_skills)
    ]


class SkillIndex:
    """Precomputed index mapping each skill to the engineers possessing it.

    Built once per engineer pool, it answers "which engineers can do this
    job?" by intersecting the engineer sets of the job's required skills,
    instead of rescanning every engineer for every job.

        skill_to_engineers = {
            "repair":  {Alice, Bob},
            "install": {Alice},
        }

        Job needs [repair, install] → {Alice, Bob} ∩ {Alice} = {Alice}

    Results are cached by the (frozen) set of required skills so repeated
    job profiles cost nothing after the first lookup.
    """

    def __init__(self, engineers: List[Engineer]) -> None:
        self._engineers = engineers
        self._skill_to_engineers: Dict[str, set] = {}
        for engineer in engineers:
            for skill in engineer.skills:
                self._skill_to_engineers.setdefault(skill, set()).add(engineer.id)
        self._by_id = {e.id: e for e in engineers}
        self._cache: Dict[frozenset, List[Engineer]] = {}

    def capable_engineers(self, job: Job) -> List[Engineer]:
        """Return engineers possessing ALL of the job's required skills."""
        key = frozenset(job.required_skills)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        if not key:
            # No skills required: every engineer is capable.
            result = list(self._engineers)
        else:
            id_sets = [self._skill_to_engineers.get(skill) for skill in key]
            if any(s is None for s in id_sets):
                result = []
            else:
                capable_ids = set.intersection(*id_sets)
                # Preserve original engineer ordering for deterministic results.
                result = [e for e in self._engineers if e.id in capable_ids]

        self._cache[key] = result
        return result


class _EngineerState:
    """Mutable per-engineer capacity tracker used during matching.

    Tracks committed job time and an incrementally maintained travel
    estimate so that each capacity check costs O(k) (k = distinct job
    locations) instead of rebuilding a full nearest-neighbor tour, which
    was O(k²) per check in the previous implementation.

    Travel model (matches the documented "cheapest connection" estimate):
        home ──┐ each new location attaches to its cheapest existing
               ▼ neighbour (home or an already-visited location)
        travel_acc += min(dist(anchor, new_loc) for anchor in visited)
        + cheapest return leg back home
    """

    __slots__ = ("home", "committed_time", "locs", "travel_acc", "min_home")

    def __init__(self, home: str) -> None:
        self.home = home
        self.committed_time = 0.0
        self.locs: set = set()
        self.travel_acc = 0.0  # home → ... chained insertion cost (no return leg)
        self.min_home = 0.0    # cheapest leg from a visited job location back home

    def _marginal(
        self, location: str, travel_matrix: Dict[str, Dict[str, float]]
    ) -> Tuple[float, float]:
        """Return (estimated_total_travel, marginal_insertion_cost) for `location`."""
        if not self.locs:
            out = travel_matrix.get(self.home, {}).get(location, 0.0)
            back = travel_matrix.get(location, {}).get(self.home, 0.0)
            return out + back, out

        if location in self.locs:
            # Already visiting this location; no new travel introduced.
            return self.travel_acc + self.min_home, 0.0

        best = travel_matrix.get(self.home, {}).get(location, 0.0)
        for loc in self.locs:
            d = travel_matrix.get(loc, {}).get(location, 0.0)
            if d < best:
                best = d
        new_min_home = min(
            self.min_home, travel_matrix.get(location, {}).get(self.home, 0.0)
        )
        return self.travel_acc + best + new_min_home, best

    def fits(
        self,
        job: Job,
        working_hours: float,
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> bool:
        """True if adding `job` keeps total time within working hours."""
        travel_est, _ = self._marginal(job.location, travel_matrix)
        return self.committed_time + job.length + travel_est <= working_hours

    def commit(self, job: Job, travel_matrix: Dict[str, Dict[str, float]]) -> None:
        """Record `job` as assigned, updating travel/time state in place."""
        loc = job.location
        if loc not in self.locs:
            if not self.locs:
                self.travel_acc = travel_matrix.get(self.home, {}).get(loc, 0.0)
                self.min_home = travel_matrix.get(loc, {}).get(self.home, 0.0)
            else:
                _, marginal = self._marginal(loc, travel_matrix)
                self.travel_acc += marginal
                self.min_home = min(
                    self.min_home, travel_matrix.get(loc, {}).get(self.home, 0.0)
                )
            self.locs.add(loc)
        self.committed_time += job.length


def can_fit_job_fast(
    engineer: Engineer,
    job: Job,
    current_jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Fast capacity check using additive marginal travel cost.

    Instead of computing a full route, estimates travel by summing the
    cheapest insertion cost for the new job:

        marginal_cost = min(dist from any current location to new job)

    This is O(n) where n = number of current jobs, making it suitable
    for repeated calls during the matching loop.

    Capacity model:
        ├─── working_hours (8h) ──────────────────────────────┤
        ├── est. travel ──┤── total job time ─────┤  margin?  │
                                                       ▲
                                           new job fits here?

    Slightly underestimates travel (optimistic) so the final route
    computed by the Scheduler may exceed capacity in edge cases.
    The Scheduler recalculates accurate routes after assignment.
    """
    total_job_time = sum(j.length for j in current_jobs) + job.length

    if not current_jobs:
        # First job: travel = home → job → home
        travel_est = (
            travel_matrix.get(engineer.location, {}).get(job.location, 0.0)
            + travel_matrix.get(job.location, {}).get(engineer.location, 0.0)
        )
    else:
        # Estimate: nearest-neighbor sum of unique locations + return
        locations = list(dict.fromkeys(
            [j.location for j in current_jobs] + [job.location]
        ))
        current = engineer.location
        travel_est = 0.0
        remaining = list(locations)
        while remaining:
            nearest = min(remaining, key=lambda loc: travel_matrix.get(current, {}).get(loc, 0.0))
            travel_est += travel_matrix.get(current, {}).get(nearest, 0.0)
            remaining.remove(nearest)
            current = nearest
        # Return home
        travel_est += travel_matrix.get(current, {}).get(engineer.location, 0.0)

    return total_job_time + travel_est <= engineer.working_hours


def can_fit_job_exact(
    engineer: Engineer,
    job: Job,
    current_jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
) -> bool:
    """Exact capacity check using full route optimization.

    Computes the actual optimal route including the new job. Accurate
    but expensive — use only for small instances or final validation.
    """
    total_job_time = sum(j.length for j in current_jobs) + job.length
    job_locations = [j.location for j in current_jobs] + [job.location]
    _, estimated_travel_time = find_optimal_route(
        engineer.location, job_locations, travel_matrix
    )
    return total_job_time + estimated_travel_time <= engineer.working_hours


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class MatchingStrategy(ABC):
    """Abstract base class for job-to-engineer matching strategies.

    Subclass this and implement `assign()` to create a new matching algorithm.
    """

    @abstractmethod
    def assign(
        self,
        engineers: List[Engineer],
        jobs: List[Job],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Dict[int, List[Job]], List[Job]]:
        """Assign jobs to engineers.

        Returns
        -------
        Tuple[Dict[int, List[Job]], List[Job]]
            (assignments dict mapping engineer ID → job list, unassigned jobs list)
        """
        ...


# ---------------------------------------------------------------------------
# Greedy strategy (original behaviour)
# ---------------------------------------------------------------------------


class GreedyStrategy(MatchingStrategy):
    """Assign each job to the closest skilled engineer with capacity.

    Algorithm:
        For each job (in input order):
            1. Find engineers with required skills
            2. Sort by distance to job (closest first)
            3. Assign to first engineer with available capacity
            4. If none fits, mark as unassigned

    Limitation — the "greedy trap":

        Jobs: J1 (repair), J2 (install)
        Alice: [repair, install], 3h capacity
        Bob:   [repair], 8h capacity

        Greedy processes J1 first:
            J1 → Alice (closest, has repair)    ✓
            J2 → Alice (only one with install)  ✗ no capacity!

        Result: J2 unassigned — but optimal assigns J1→Bob, J2→Alice.

    Use `ConstrainedGreedyStrategy` to avoid this problem.
    """

    def assign(
        self,
        engineers: List[Engineer],
        jobs: List[Job],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Dict[int, List[Job]], List[Job]]:
        assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
        unassigned: List[Job] = []

        for job in jobs:
            candidates = get_capable_engineers(job, engineers)
            if not candidates:
                unassigned.append(job)
                continue

            candidates.sort(
                key=lambda eng: travel_matrix.get(eng.location, {}).get(
                    job.location, float("inf")
                )
            )

            assigned = False
            for engineer in candidates:
                if can_fit_job_fast(engineer, job, assignments[engineer.id], travel_matrix):
                    assignments[engineer.id].append(job)
                    assigned = True
                    break

            if not assigned:
                unassigned.append(job)

        return assignments, unassigned


# ---------------------------------------------------------------------------
# Constrained Greedy + Swap strategy (default)
# ---------------------------------------------------------------------------


class ConstrainedGreedyStrategy(MatchingStrategy):
    """Constrained greedy with optional swap repair for small instances.

    Addresses the greedy trap by processing jobs in constraint order AND
    applying a swap repair pass for small inputs where it's affordable.

    Phase 1: Constrained Greedy — O(j · e · log j)
    ------------------------------------------------
    Sorts jobs by number of capable engineers (fewest first), then assigns
    greedily. Most-constrained jobs get first pick of capacity.

        Sort order (fewest capable engineers first):
            J2 (install) → 1 engineer can do it  ◄── assigned first
            J1 (repair)  → 2 engineers can do it
            J3 (repair)  → 2 engineers can do it

    This alone solves benchmarks 4 and 5 (exclusive skill traps).

    Phase 2: Swap Improvement (small instances only)
    -------------------------------------------------
    For instances with ≤ SWAP_THRESHOLD jobs, runs a single-pass swap
    to recover from remaining greedy mistakes:

        Before swap:                    After swap:
        ┌────────────────────┐          ┌────────────────────┐
        │ Alice: [J1]  FULL  │          │ Alice: [J2]        │ ◄── J2 fits now
        │ Bob:   [J3]        │          │ Bob:   [J3, J1]    │ ◄── J1 moved here
        │ Unassigned: [J2]   │          │ Unassigned: []     │
        └────────────────────┘          └────────────────────┘

    For large instances (> SWAP_THRESHOLD), the swap is skipped entirely
    to meet scalability targets.

    Capacity Check
    --------------
    Uses fast nearest-neighbor travel estimate (O(n) per check) rather
    than full route optimization. Accurate routes are computed by the
    Scheduler after all assignments are finalized.
    """

    # Maximum number of jobs for which the swap pass is activated
    SWAP_THRESHOLD = 100

    def assign(
        self,
        engineers: List[Engineer],
        jobs: List[Job],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Dict[int, List[Job]], List[Job]]:
        # --- Phase 1: Greedy, most-constrained jobs first ---
        assignments: Dict[int, List[Job]] = {e.id: [] for e in engineers}
        unassigned: List[Job] = []

        # Build skill index once so capability lookups are ~O(required_skills)
        # instead of rescanning every engineer for every job.
        index = SkillIndex(engineers)

        # Per-engineer capacity trackers maintained incrementally (O(k) per
        # check) rather than rebuilding a nearest-neighbor tour each time.
        states: Dict[int, _EngineerState] = {
            e.id: _EngineerState(e.location) for e in engineers
        }
        hours: Dict[int, float] = {e.id: e.working_hours for e in engineers}

        # Sort jobs by how constrained they are (fewest capable engineers first)
        jobs_sorted = sorted(jobs, key=lambda j: len(index.capable_engineers(j)))

        for job in jobs_sorted:
            candidates = index.capable_engineers(job)
            if not candidates:
                unassigned.append(job)
                continue

            # Among capable engineers, prefer the closest one
            candidates = sorted(
                candidates,
                key=lambda eng: travel_matrix.get(eng.location, {}).get(
                    job.location, float("inf")
                ),
            )

            assigned = False
            for engineer in candidates:
                if states[engineer.id].fits(job, hours[engineer.id], travel_matrix):
                    assignments[engineer.id].append(job)
                    states[engineer.id].commit(job, travel_matrix)
                    assigned = True
                    break

            if not assigned:
                unassigned.append(job)

        # --- Phase 2: Swap improvement (small instances only) ---
        if unassigned and len(jobs) <= self.SWAP_THRESHOLD:
            assignments, unassigned = self._improve_by_swaps(
                assignments, unassigned, engineers, travel_matrix
            )

        return assignments, unassigned

    def _improve_by_swaps(
        self,
        assignments: Dict[int, List[Job]],
        unassigned: List[Job],
        engineers: List[Engineer],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Dict[int, List[Job]], List[Job]]:
        """Single-pass swap: try to place each unassigned job once.

        For each unassigned job:
            For each capable engineer (who can't fit it directly):
                For each of their current jobs:
                    If removing it makes room AND it can go elsewhere:
                        Perform the swap.

        Single pass — O(u · e · j_per_e · e) in the worst case, but
        bounded by SWAP_THRESHOLD so u and j_per_e are small.
        """
        still_unassigned: List[Job] = []

        for job in unassigned:
            if self._try_single_swap(job, assignments, engineers, travel_matrix):
                pass  # successfully placed
            else:
                still_unassigned.append(job)

        return assignments, still_unassigned

    def _try_single_swap(
        self,
        job: Job,
        assignments: Dict[int, List[Job]],
        engineers: List[Engineer],
        travel_matrix: Dict[str, Dict[str, float]],
    ) -> bool:
        """Try to place `job` by moving one existing assignment elsewhere.

        Search pattern:

            Can engineer E take `job`?
            │
            └── No (full) → for each job J currently assigned to E:
                                │
                                └── Remove J temporarily
                                    ├── Does `job` fit now? → No: skip
                                    └── Yes: can another engineer take J?
                                        ├── No:  undo, try next J
                                        └── Yes: perform swap ✓
        """
        candidates = get_capable_engineers(job, engineers)

        for engineer in candidates:
            # First check if it fits directly (shouldn't normally reach
            # here since greedy already tried, but capacity may have
            # changed from earlier swaps)
            if can_fit_job_fast(engineer, job, assignments[engineer.id], travel_matrix):
                assignments[engineer.id].append(job)
                return True

            # Try displacing one existing job
            for existing_job in list(assignments[engineer.id]):
                test_jobs = [
                    j for j in assignments[engineer.id] if j.id != existing_job.id
                ]

                if not can_fit_job_fast(engineer, job, test_jobs, travel_matrix):
                    continue

                # Can existing_job go to another engineer?
                other_candidates = get_capable_engineers(existing_job, engineers)
                for other_eng in other_candidates:
                    if other_eng.id == engineer.id:
                        continue
                    if can_fit_job_fast(
                        other_eng,
                        existing_job,
                        assignments[other_eng.id],
                        travel_matrix,
                    ):
                        # Perform the swap
                        assignments[engineer.id].remove(existing_job)
                        assignments[other_eng.id].append(existing_job)
                        assignments[engineer.id].append(job)
                        return True

        return False


# ---------------------------------------------------------------------------
# Module default and public entry point
# ---------------------------------------------------------------------------

DEFAULT_STRATEGY: MatchingStrategy = ConstrainedGreedyStrategy()


def assign_jobs(
    engineers: List[Engineer],
    jobs: List[Job],
    travel_matrix: Dict[str, Dict[str, float]],
    strategy: MatchingStrategy | None = None,
) -> Tuple[Dict[int, List[Job]], List[Job]]:
    """Assign jobs to engineers using the given (or default) strategy.

    This is the public entry point for job matching. It delegates to the
    configured strategy (default: constrained greedy with swap).

    Parameters
    ----------
    engineers : List[Engineer]
        The available field engineers.
    jobs : List[Job]
        The jobs that need to be assigned.
    travel_matrix : Dict[str, Dict[str, float]]
        Travel time between locations.
    strategy : MatchingStrategy | None
        The matching strategy to use. Defaults to `DEFAULT_STRATEGY`.

    Returns
    -------
    Tuple[Dict[int, List[Job]], List[Job]]
        A tuple containing:
        - A mapping from engineer ID to the list of jobs assigned
        - A list of unassigned jobs

    Examples
    --------
    >>> from src.optimization.matching import assign_jobs, GreedyStrategy
    >>> # Use default strategy:
    >>> assignments, unassigned = assign_jobs(engineers, jobs, matrix)
    >>> # Use greedy-only:
    >>> assignments, unassigned = assign_jobs(engineers, jobs, matrix, strategy=GreedyStrategy())
    """
    if strategy is None:
        strategy = DEFAULT_STRATEGY
    return strategy.assign(engineers, jobs, travel_matrix)
