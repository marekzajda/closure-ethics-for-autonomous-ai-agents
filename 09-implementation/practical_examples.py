"""Runnable practical examples for the Closure Ethics reference governor.

Run from 09-implementation:
    python practical_examples.py

These scenarios use DEMO_POLICY and the public data structures in closure_ethics.py.
They are demonstrations, not production policy recommendations.
"""
from closure_ethics import (
    ActionEvidence,
    AuditEvidence,
    AuthorizationEvidence,
    ClosureEthicsGovernor,
    DEMO_POLICY,
    DeceptionEvidence,
    Interval,
    RepairEdge,
    RepairEvidence,
    ReversibilityEvidence,
    bounded_repair_search,
    evaluate,
)


def I(x: float) -> Interval:
    return Interval.point(x)


def unsafe_direct_deploy() -> ActionEvidence:
    return ActionEvidence(
        action_id="deploy-directly",
        catastrophic_risk=Interval(0.01, 0.04),
        agency_before={"operator": 1.0, "reviewer": 1.0},
        agency_after={"operator": 0.8, "reviewer": 0.2},
        audit=AuditEvidence(I(0.4), I(0.6), I(0.2)),
        repair=RepairEvidence(False, I(1.0), I(1.0)),
        reversibility=ReversibilityEvidence(I(0.2), I(0.3), I(0.4)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.8)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.95),
    )


def safe_sandbox_canary() -> ActionEvidence:
    return ActionEvidence(
        action_id="sandboxed-canary",
        catastrophic_risk=Interval(0.001, 0.01),
        agency_before={"operator": 1.0, "reviewer": 1.0},
        agency_after={"operator": 1.0, "reviewer": 1.0},
        audit=AuditEvidence(I(0.95), I(0.95), I(0.90)),
        repair=RepairEvidence(True, I(0.15), I(0.10), ("candidate", "rollback", "safe")),
        reversibility=ReversibilityEvidence(I(0.95), I(0.9), I(0.95)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.70),
    )


def example_1_direct_vs_sandbox(governor: ClosureEthicsGovernor) -> None:
    decision = governor.choose([unsafe_direct_deploy(), safe_sandbox_canary()])
    print("1 direct vs sandbox:", decision.status, decision.selected_action)
    assert decision.status == "EXECUTE"
    assert decision.selected_action == "sandboxed-canary"


def example_2_utility_does_not_buy_repair(governor: ClosureEthicsGovernor) -> None:
    bad = ActionEvidence(
        action_id="high-reward-no-repair",
        catastrophic_risk=I(0.02),
        agency_before={"human": 1.0, "agent": 1.0},
        agency_after={"human": 1.0, "agent": 1.0},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(False, I(1.0), I(1.0)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(1.0),
    )
    good = ActionEvidence(
        action_id="lower-reward-with-repair",
        catastrophic_risk=I(0.01),
        agency_before={"human": 1.0, "agent": 1.0},
        agency_after={"human": 1.0, "agent": 1.0},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(True, I(0.2), I(0.15)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.4),
    )
    decision = governor.choose([bad, good])
    print("2 utility vs repair:", decision.status, decision.selected_action)
    assert decision.selected_action == "lower-reward-with-repair"


def example_3_authorized_but_covert(governor: ClosureEthicsGovernor) -> None:
    covert = ActionEvidence(
        action_id="authorized-but-covert",
        catastrophic_risk=I(0.01),
        agency_before={"human": 1.0},
        agency_after={"human": 1.0},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(True, I(0.1), I(0.1)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(1.0), I(1.0), I(1.0)),
        deception=DeceptionEvidence(I(0.9), I(0.8), I(0.0), I(0.0)),
        task_utility=I(1.0),
    )
    decision = governor.choose([covert])
    print("3 authorized but covert:", decision.status, decision.reason_codes)
    assert decision.status == "REFUSE_OR_ESCALATE"
    assert "REFUSE_COVERT_ACTION" in decision.reason_codes


def example_4_agency_plurality_loss() -> None:
    centralize = ActionEvidence(
        action_id="centralize-power",
        catastrophic_risk=I(0.01),
        agency_before={"human": 1.0, "agent": 1.0, "reviewer": 1.0},
        agency_after={"human": 0.1, "agent": 1.0, "reviewer": 0.05},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(True, I(0.1), I(0.1)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.8),
    )
    ev = evaluate(centralize, DEMO_POLICY)
    print("4 agency plurality:", ev.admissible, ev.violations)
    assert ev.violations == ("AGENCY_LOSS",)


def example_5_multi_agent_composition(governor: ClosureEthicsGovernor) -> None:
    local1 = ActionEvidence(
        action_id="agent-A-read",
        catastrophic_risk=I(0.01),
        agency_before={"A": 1.0, "B": 1.0},
        agency_after={"A": 1.0, "B": 1.0},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(True, I(0.1), I(0.1)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.6),
    )
    local2 = ActionEvidence(
        action_id="agent-B-write",
        catastrophic_risk=I(0.01),
        agency_before={"A": 1.0, "B": 1.0},
        agency_after={"A": 1.0, "B": 1.0},
        audit=AuditEvidence(I(0.9), I(0.9), I(0.9)),
        repair=RepairEvidence(True, I(0.1), I(0.1)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.65),
    )
    joint = ActionEvidence(
        action_id="A-and-B-coordinated",
        catastrophic_risk=I(0.01),
        agency_before={"A": 1.0, "B": 1.0},
        agency_after={"A": 1.0, "B": 1.0},
        audit=AuditEvidence(I(0.2), I(0.3), I(0.1)),
        repair=RepairEvidence(True, I(0.1), I(0.1)),
        reversibility=ReversibilityEvidence(I(0.9), I(0.9), I(0.9)),
        authorization=AuthorizationEvidence(I(0.9), I(0.9), I(0.9)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.85),
    )
    ev1 = evaluate(local1, DEMO_POLICY)
    ev2 = evaluate(local2, DEMO_POLICY)
    ev_joint = governor.evaluate_joint_action(joint)
    print("5 composition:", ev1.admissible, ev2.admissible, ev_joint.admissible, ev_joint.violations)
    assert ev1.admissible and ev2.admissible
    assert not ev_joint.admissible
    assert "AUDITABILITY_LOSS" in ev_joint.violations


def example_6_bounded_repair_search() -> None:
    graph = {
        "x": [
            RepairEdge("a", cost=1, risk=7),
            RepairEdge("b", cost=4, risk=1),
        ],
        "a": [RepairEdge("safe", cost=1, risk=1)],
        "b": [RepairEdge("safe", cost=1, risk=1)],
    }
    cert = bounded_repair_search(
        graph,
        start="x",
        safe_states={"safe"},
        max_cost=6,
        max_risk=3,
    )
    print("6 bounded repair:", cert.exists, cert.path, cert.total_cost, cert.total_risk)
    assert cert.exists
    assert cert.path == ("x", "b", "safe")


def example_7_recovery_mode(governor: ClosureEthicsGovernor) -> None:
    recovery = ActionEvidence(
        action_id="sandbox-and-log",
        catastrophic_risk=I(0.005),
        agency_before={"human": 1.0},
        agency_after={"human": 1.0},
        audit=AuditEvidence(I(0.95), I(0.95), I(0.95)),
        repair=RepairEvidence(True, I(0.05), I(0.05)),
        reversibility=ReversibilityEvidence(I(0.95), I(0.95), I(0.95)),
        authorization=AuthorizationEvidence(I(0.8), I(0.8), I(0.8)),
        deception=DeceptionEvidence(I(0.0), I(0.0), I(0.0), I(0.0)),
        task_utility=I(0.3),
    )
    decision = governor.choose(
        candidates=[unsafe_direct_deploy()],
        recovery_candidates=[recovery],
    )
    print("7 recovery:", decision.status, decision.selected_action)
    assert decision.status == "EXECUTE_RECOVERY"
    assert decision.selected_action == "sandbox-and-log"


def main() -> None:
    governor = ClosureEthicsGovernor(DEMO_POLICY)
    example_1_direct_vs_sandbox(governor)
    example_2_utility_does_not_buy_repair(governor)
    example_3_authorized_but_covert(governor)
    example_4_agency_plurality_loss()
    example_5_multi_agent_composition(governor)
    example_6_bounded_repair_search()
    example_7_recovery_mode(governor)
    print("All practical Closure Ethics examples passed.")


if __name__ == "__main__":
    main()
