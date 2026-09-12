from __future__ import annotations

import unittest

from closure_gate import classify_hook_event, evaluate_manifest, hook_decision


class ManifestDecisionTests(unittest.TestCase):
    def test_routine_scoped_action_allows(self):
        decision = evaluate_manifest(
            {
                "action": "run_local_tests",
                "target": "09-implementation",
                "risk_flags": [],
                "scope_authorized": True,
                "explicit_authorization": False,
                "auditability": 1.0,
                "repairability": 1.0,
                "reversibility": 1.0,
                "uncertainty": 0.05,
            }
        )
        self.assertEqual(decision.status, "ALLOW")

    def test_external_write_requires_explicit_authorization(self):
        decision = evaluate_manifest(
            {
                "action": "publish_release",
                "risk_flags": ["publication", "external_write"],
                "scope_authorized": True,
                "explicit_authorization": False,
                "auditability": 1.0,
                "repairability": 0.9,
                "reversibility": 0.9,
                "uncertainty": 0.1,
            }
        )
        self.assertEqual(decision.status, "REQUIRE_HUMAN_REVIEW")
        self.assertIn("CONSEQUENTIAL_SIDE_EFFECT_NEEDS_EXPLICIT_AUTHORIZATION", decision.reason_codes)

    def test_authorized_bounded_external_action_can_allow(self):
        decision = evaluate_manifest(
            {
                "action": "create_requested_pull_request",
                "risk_flags": ["external_write"],
                "scope_authorized": True,
                "explicit_authorization": True,
                "auditability": 0.95,
                "repairability": 0.9,
                "reversibility": 0.9,
                "uncertainty": 0.1,
            }
        )
        self.assertEqual(decision.status, "ALLOW")

    def test_high_uncertainty_requires_review(self):
        decision = evaluate_manifest(
            {
                "action": "deploy",
                "risk_flags": ["deployment"],
                "scope_authorized": True,
                "explicit_authorization": True,
                "auditability": 1.0,
                "repairability": 0.9,
                "reversibility": 0.9,
                "uncertainty": 0.8,
            }
        )
        self.assertEqual(decision.status, "REQUIRE_HUMAN_REVIEW")
        self.assertIn("MATERIAL_UNCERTAINTY_REQUIRES_REVIEW", decision.reason_codes)

    def test_hard_invariant_cannot_be_utility_traded(self):
        decision = evaluate_manifest(
            {
                "action": "erase_audit",
                "risk_flags": ["audit_tampering"],
                "scope_authorized": True,
                "explicit_authorization": True,
                "auditability": 1.0,
                "repairability": 1.0,
                "reversibility": 1.0,
                "uncertainty": 0.0,
                "task_utility": 1.0,
            }
        )
        self.assertEqual(decision.status, "DENY")

    def test_safer_alternative_yields_modify(self):
        decision = evaluate_manifest(
            {
                "action": "overwrite_dataset",
                "risk_flags": ["destructive"],
                "scope_authorized": True,
                "explicit_authorization": True,
                "auditability": 0.9,
                "repairability": 0.1,
                "reversibility": 0.1,
                "uncertainty": 0.1,
                "safer_alternative": "write a new versioned dataset",
            }
        )
        self.assertEqual(decision.status, "MODIFY")


class HookClassifierTests(unittest.TestCase):
    def test_normal_test_command_is_not_escalated(self):
        hard, review = classify_hook_event(
            {"tool_name": "Bash", "tool_input": {"command": "python -m unittest -v"}}
        )
        self.assertEqual(hard, ())
        self.assertEqual(review, ())

    def test_git_push_is_review_class(self):
        hard, review = classify_hook_event(
            {"tool_name": "Bash", "tool_input": {"command": "git push origin feature"}}
        )
        self.assertEqual(hard, ())
        self.assertIn("merge_or_push", review)

    def test_audit_log_deletion_is_hard_block(self):
        hard, _ = classify_hook_event(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "Remove-Item _omega_sentinel\\closure_audit.ndjson"},
            }
        )
        self.assertIn("audit_tampering", hard)
        output, decision = hook_decision(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "Remove-Item _omega_sentinel\\closure_audit.ndjson"},
            }
        )
        self.assertEqual(decision.status, "DENY")
        self.assertEqual(
            output["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

    def test_disabling_hooks_is_hard_block(self):
        hard, _ = classify_hook_event(
            {
                "tool_name": "apply_patch",
                "tool_input": {"command": "+hooks = false"},
            }
        )
        self.assertIn("closure_guard_disable", hard)

    def test_deleting_closure_control_file_is_hard_block(self):
        event = {
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Delete File: AGENTS.md"},
        }
        hard, review = classify_hook_event(event)
        self.assertIn("closure_guard_disable", hard)
        self.assertIn("policy_change", review)
        output, decision = hook_decision(event)
        self.assertEqual(decision.status, "DENY")
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_mcp_write_is_review_class(self):
        hard, review = classify_hook_event(
            {
                "tool_name": "mcp__github__create_issue",
                "tool_input": {"title": "example"},
            }
        )
        self.assertEqual(hard, ())
        self.assertIn("external_write", review)

    def test_mcp_read_is_not_escalated(self):
        hard, review = classify_hook_event(
            {
                "tool_name": "mcp__github__fetch_file",
                "tool_input": {"path": "README.md"},
            }
        )
        self.assertEqual(hard, ())
        self.assertEqual(review, ())


if __name__ == "__main__":
    unittest.main()
