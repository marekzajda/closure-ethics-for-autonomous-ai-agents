from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from closure_kernel import ClosureKernel


HERE = Path(__file__).resolve().parent


class OmegaSentinelTests(unittest.TestCase):
    def test_policy_allows_only_named_telemetry_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kernel = ClosureKernel(HERE / "closure_policy_v0_1.json")
            permitted = kernel.evaluate(
                "write_local_telemetry",
                root / "_omega_sentinel" / "latest.json",
                risk={"irreversible": 0.0, "scientific": 0.0, "external": 0.0},
                require_telemetry_target=True,
            )
            denied = kernel.evaluate(
                "write_local_telemetry",
                root / "scientific_result.json",
                require_telemetry_target=True,
            )
            self.assertTrue(permitted.allowed)
            self.assertFalse(denied.allowed)

    def test_v02_once_emits_local_outputs(self):
        import omega_sentinel as base
        from omega_sentinel_v0_2 import SentinelV02

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            telemetry = root / "_omega_sentinel"
            config = root / "config.json"
            config.write_text(json.dumps({
                "workspace_root": str(root),
                "telemetry_dir": str(telemetry),
                "policy_path": str(HERE / "closure_policy_v0_1.json"),
                "sample_seconds": 30,
                "heartbeat_seconds": 300,
                "bridge_interval_seconds": 300,
                "tail_lines": 10,
                "command_patterns": ["omega_test"],
            }), encoding="utf-8")

            process_result = ([], {
                "ok": True, "backend": "test", "degraded": False, "errors": []
            })
            with patch.object(base, "process_table", return_value=process_result), \
                    patch.object(base, "gpu_status", return_value={"available": False}):
                self.assertEqual(SentinelV02(config).run(once=True), 0)

            for name in ("latest.json", "events.ndjson", "closure_audit.ndjson", "dashboard.txt", "bridge.json"):
                self.assertTrue((telemetry / name).exists(), name)
            bridge = json.loads((telemetry / "bridge.json").read_text(encoding="utf-8"))
            self.assertEqual(bridge["schema"], "omega-sentinel-bridge-v0.2")


if __name__ == "__main__":
    unittest.main()
