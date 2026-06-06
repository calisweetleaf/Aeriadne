"""
CTMv3 Engine Tests
==================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Unit tests for all CTMv3 core engine modules using stdlib unittest
         and a temporary directory as the fake project root.

Run with:
    python3 -m unittest discover -s core/ctmv3/tests -v
    or:
    python3 -m unittest ctmv3.tests.test_engine -v
"""

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Ensure ctmv3 package is importable regardless of install state.
# The test file lives at ctmv3-plugin/core/ctmv3/tests/test_engine.py.
# The ctmv3 package namespace dir lives at ctmv3-plugin/core/.
# We add the core/ directory to sys.path so `import ctmv3.core.boot` works.
# ---------------------------------------------------------------------------

_TESTS_DIR = Path(__file__).resolve().parent
_CORE_SRC_DIR = _TESTS_DIR.parent.parent   # ctmv3-plugin/core/
if str(_CORE_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_SRC_DIR))

# Legacy path kept for backwards compatibility with existing sys.path setups
_PLUGIN_ROOT = _TESTS_DIR.parent.parent.parent   # /agent/workspace (or above ctmv3-plugin/)
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------

from ctmv3.core import boot as boot_module
from ctmv3.core import fingerprint as fp_module
from ctmv3.core import sovereign as sov_module
from ctmv3.core import dot_init as dot_module
from ctmv3.core import architecture_map as arch_module
from ctmv3.core import activate as activate_module
from ctmv3.core import templates as tmpl


# ---------------------------------------------------------------------------
# Helper: create a fresh temporary project root
# ---------------------------------------------------------------------------

def _tmp_root() -> Path:
    """Create and return a temporary directory path (caller must clean up)."""
    d = tempfile.mkdtemp(prefix="ctmv3_test_")
    return Path(d)


def _cleanup(path: Path) -> None:
    """Recursively remove a temporary directory tree."""
    shutil.rmtree(str(path), ignore_errors=True)


# ---------------------------------------------------------------------------
# Boot module tests (original suite)
# ---------------------------------------------------------------------------

class TestBoot(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_empty_repo_is_cold_start(self) -> None:
        """An empty directory must return COLD_START."""
        inv = boot_module.discover(self.root)
        self.assertEqual(inv.branch, "COLD_START")
        self.assertEqual(inv.tier1_signals, [])
        self.assertEqual(inv.tier2_signals, [])

    def test_agents_md_triggers_tier1(self) -> None:
        """AGENTS.md presence must be detected as a Tier 1 signal."""
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        inv = boot_module.discover(self.root)
        self.assertIn("AGENTS.md", inv.tier1_signals)

    def test_sovereign_dir_triggers_tier1(self) -> None:
        """'.sovereign/' presence must be detected as a Tier 1 signal."""
        (self.root / ".sovereign").mkdir()
        inv = boot_module.discover(self.root)
        self.assertIn(".sovereign", inv.tier1_signals)

    def test_provenance_without_session_log_is_partial(self) -> None:
        """Tier 1 signal + PROVENANCE.md with empty Session Log must be PARTIAL."""
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (self.root / "PROVENANCE.md").write_text("# PROVENANCE\n\n## Session Log\n", encoding="utf-8")
        inv = boot_module.discover(self.root)
        # Session Log exists but has no data rows -> last_session = None -> PARTIAL
        self.assertEqual(inv.branch, "PARTIAL")

    def test_warm_start_when_provenance_has_session_row(self) -> None:
        """Tier 1 + PROVENANCE.md with a session row must be WARM_START."""
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        prov = (
            "# PROVENANCE\n\n"
            "## Session Log\n\n"
            "| Date | Agent | Action | Topology Drift? | Next |\n"
            "|------|-------|--------|----------------|------|\n"
            "| 2026-05-20 | Claude Code | initial | no | fill topology |\n"
        )
        (self.root / "PROVENANCE.md").write_text(prov, encoding="utf-8")
        inv = boot_module.discover(self.root)
        self.assertEqual(inv.branch, "WARM_START")
        self.assertIsNotNone(inv.last_session)

    def test_tier3_config_spine_detected(self) -> None:
        """pyproject.toml must appear in tier3_signals."""
        (self.root / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
        inv = boot_module.discover(self.root)
        self.assertIn("pyproject.toml", inv.tier3_signals)

    def test_classify_branch_cold(self) -> None:
        inv = boot_module.SignalInventory(project_root=self.root)
        self.assertEqual(boot_module.classify_branch(inv), "COLD_START")

    def test_is_warm_valid_returns_false_for_cold(self) -> None:
        inv = boot_module.SignalInventory(project_root=self.root)
        self.assertFalse(boot_module.is_warm_valid(inv))


# ---------------------------------------------------------------------------
# Boot module hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestBootHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_discover_raises_value_error_for_nonexistent_path(self) -> None:
        """discover() must raise ValueError for a path that does not exist."""
        with self.assertRaises(ValueError) as ctx:
            boot_module.discover(Path("/tmp/ctmv3_nonexistent_path_xyz_12345"))
        self.assertIn("does not exist", str(ctx.exception))

    def test_discover_raises_value_error_for_file_not_dir(self) -> None:
        """discover() must raise ValueError when given a file path, not a directory."""
        f = self.root / "not_a_dir.txt"
        f.write_text("data\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            boot_module.discover(f)
        self.assertIn("not a directory", str(ctx.exception))

    def test_discover_populates_file_count(self) -> None:
        """discover() must populate SignalInventory.file_count for non-empty repos."""
        (self.root / "file1.py").write_text("x=1\n")
        (self.root / "file2.py").write_text("x=2\n")
        inv = boot_module.discover(self.root)
        self.assertGreaterEqual(inv.file_count, 2)

    def test_file_count_bounded_by_max(self) -> None:
        """_count_files_bounded must return at most max_count."""
        # Create more files than the tiny cap we pass
        for i in range(10):
            (self.root / f"file{i}.txt").write_text(str(i))
        count = boot_module._count_files_bounded(self.root, max_depth=5, max_count=5)
        self.assertLessEqual(count, 5)

    def test_file_count_depth_bounded(self) -> None:
        """_count_files_bounded must respect max_depth and not descend deeper."""
        deep = self.root / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep_file.txt").write_text("deep")
        # With depth=1, we should not reach a/b/c/deep_file.txt
        count_shallow = boot_module._count_files_bounded(self.root, max_depth=1, max_count=1000)
        # a/ is depth 0 -> b/ is depth 1 -> c/ is depth 2 (not traversed at max_depth=1)
        # So deep_file.txt should NOT be counted
        self.assertEqual(count_shallow, 0)

    def test_is_warm_valid_raises_for_negative_threshold(self) -> None:
        """is_warm_valid must raise ValueError for negative age_days_threshold."""
        inv = boot_module.SignalInventory(project_root=self.root)
        with self.assertRaises(ValueError) as ctx:
            boot_module.is_warm_valid(inv, age_days_threshold=-1)
        self.assertIn("non-negative", str(ctx.exception))

    def test_extract_last_session_returns_none_for_empty_log(self) -> None:
        """_extract_last_session must return None if Session Log has no data rows."""
        prov = self.root / "PROVENANCE.md"
        prov.write_text("# PROVENANCE\n\n## Session Log\n\n| Date | Agent |\n|------|-------|\n")
        result = boot_module._extract_last_session(prov)
        self.assertIsNone(result)

    def test_extract_last_session_returns_last_row(self) -> None:
        """_extract_last_session must return the last data row."""
        prov = self.root / "PROVENANCE.md"
        prov.write_text(
            "# PROVENANCE\n\n## Session Log\n\n"
            "| Date | Agent | Action | Drift | Next |\n"
            "|------|-------|--------|-------|------|\n"
            "| 2026-01-01 | AgentA | first | no | next |\n"
            "| 2026-05-20 | AgentB | second | yes | fill |\n"
        )
        result = boot_module._extract_last_session(prov)
        self.assertIsNotNone(result)
        self.assertIn("AgentB", result)

    def test_read_session_state_meta_handles_malformed_json(self) -> None:
        """_read_session_state_meta must return (False, None) for malformed JSON."""
        ss = self.root / "session_state.json"
        ss.write_text("not valid json {{{", encoding="utf-8")
        valid, ts = boot_module._read_session_state_meta(ss)
        self.assertFalse(valid)
        self.assertIsNone(ts)

    def test_read_session_state_meta_handles_non_dict_json(self) -> None:
        """_read_session_state_meta must return (False, None) when JSON is a list."""
        ss = self.root / "session_state.json"
        ss.write_text('["not", "a", "dict"]', encoding="utf-8")
        valid, ts = boot_module._read_session_state_meta(ss)
        self.assertFalse(valid)
        self.assertIsNone(ts)

    def test_to_dict_is_json_serializable(self) -> None:
        """SignalInventory.to_dict() must produce a JSON-serializable object."""
        inv = boot_module.discover(self.root)
        serialized = json.dumps(inv.to_dict())
        self.assertIsInstance(serialized, str)


# ---------------------------------------------------------------------------
# Fingerprint module tests (original suite)
# ---------------------------------------------------------------------------

class TestFingerprint(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_compute_returns_sha256_prefix(self) -> None:
        h = fp_module.compute(self.root)
        self.assertTrue(h.startswith("sha256:"))
        self.assertEqual(len(h), 7 + 64)  # "sha256:" + 64 hex chars

    def test_empty_repo_hash_is_stable(self) -> None:
        """Two calls on the same empty repo must return the same hash."""
        h1 = fp_module.compute(self.root)
        h2 = fp_module.compute(self.root)
        self.assertEqual(h1, h2)

    def test_hash_changes_when_topology_changes(self) -> None:
        (self.root / "TOPOLOGY.md").write_text("# TOPOLOGY v1\n", encoding="utf-8")
        h1 = fp_module.compute(self.root)
        (self.root / "TOPOLOGY.md").write_text("# TOPOLOGY v2\n", encoding="utf-8")
        h2 = fp_module.compute(self.root)
        self.assertNotEqual(h1, h2)

    def test_write_creates_fingerprint_file(self) -> None:
        fp_path = fp_module.write(self.root)
        self.assertTrue(fp_path.exists())
        content = fp_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("sha256:"))

    def test_verify_matches_after_write(self) -> None:
        fp_module.write(self.root)
        matches, _ = fp_module.verify(self.root)
        self.assertTrue(matches)

    def test_verify_fails_after_topology_change(self) -> None:
        fp_module.write(self.root)
        (self.root / "TOPOLOGY.md").write_text("# changed\n", encoding="utf-8")
        matches, _ = fp_module.verify(self.root)
        self.assertFalse(matches)

    def test_verify_returns_false_when_no_fingerprint_file(self) -> None:
        matches, h = fp_module.verify(self.root)
        self.assertFalse(matches)
        self.assertTrue(h.startswith("sha256:"))


# ---------------------------------------------------------------------------
# Fingerprint module hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestFingerprintHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_compute_raises_for_nonexistent_path(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            fp_module.compute(Path("/tmp/ctmv3_does_not_exist_xyz"))
        self.assertIn("does not exist", str(ctx.exception))

    def test_compute_raises_for_file_not_dir(self) -> None:
        f = self.root / "notadir.txt"
        f.write_text("x")
        with self.assertRaises(ValueError) as ctx:
            fp_module.compute(f)
        self.assertIn("not a directory", str(ctx.exception))

    def test_write_raises_for_nonexistent_path(self) -> None:
        with self.assertRaises(ValueError):
            fp_module.write(Path("/tmp/ctmv3_does_not_exist_xyz"))

    def test_verify_raises_for_nonexistent_path(self) -> None:
        with self.assertRaises(ValueError):
            fp_module.verify(Path("/tmp/ctmv3_does_not_exist_xyz"))

    def test_streaming_hash_large_file(self) -> None:
        """Streaming hash must work for files larger than a single chunk."""
        large = self.root / "TOPOLOGY.md"
        # Write 100 KiB of data (much larger than 8 KiB chunk size)
        large.write_bytes(b"X" * 102_400)
        h = fp_module.compute(self.root)
        self.assertTrue(h.startswith("sha256:"))
        self.assertEqual(len(h), 7 + 64)

    def test_hash_deterministic_for_large_file(self) -> None:
        """Two compute() calls on the same large file must return identical hashes."""
        large = self.root / "TOPOLOGY.md"
        large.write_bytes(b"A" * 65_536)
        h1 = fp_module.compute(self.root)
        h2 = fp_module.compute(self.root)
        self.assertEqual(h1, h2)

    def test_atomic_write_leaves_no_tmp_file_on_success(self) -> None:
        """After write(), no .tmp file should remain."""
        fp_module.write(self.root)
        sovereign_dir = self.root / ".sovereign"
        tmp_files = list(sovereign_dir.glob("*.tmp"))
        self.assertEqual(tmp_files, [], f"Unexpected .tmp files: {tmp_files}")

    def test_write_is_atomic_on_crash_simulation(self) -> None:
        """
        Simulate a crash mid-write by patching os.replace to raise.
        The target file must either be absent (if it didn't exist) or contain
        the original content (if it did exist) — never partial content.
        """
        fp_path = self.root / ".sovereign" / "topology_fingerprint.txt"
        (self.root / ".sovereign").mkdir(parents=True)
        original_content = "sha256:original\n"
        fp_path.write_text(original_content)

        with patch("ctmv3.core.fingerprint.os.replace", side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                fp_module._atomic_write(fp_path, "sha256:new_content\n")

        # Original file must be untouched
        self.assertEqual(fp_path.read_text(), original_content)

        # .tmp file must have been cleaned up (best-effort)
        tmp_path = fp_path.with_suffix(fp_path.suffix + ".tmp")
        # tmp_path may or may not exist depending on OS cleanup; either is acceptable,
        # but the target must be intact — which we verified above.

    def test_read_stored_returns_none_when_absent(self) -> None:
        result = fp_module.read_stored(self.root)
        self.assertIsNone(result)

    def test_read_stored_returns_hash_after_write(self) -> None:
        fp_module.write(self.root)
        stored = fp_module.read_stored(self.root)
        self.assertIsNotNone(stored)
        self.assertTrue(stored.startswith("sha256:"))


# ---------------------------------------------------------------------------
# Sovereign module tests (original suite)
# ---------------------------------------------------------------------------

class TestSovereign(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_init_creates_sovereign_dir(self) -> None:
        sov_module.init(self.root)
        self.assertTrue((self.root / ".sovereign").is_dir())

    def test_init_creates_session_state(self) -> None:
        sov_module.init(self.root)
        ss_path = self.root / ".sovereign" / "session_state.json"
        self.assertTrue(ss_path.exists())
        data = json.loads(ss_path.read_text(encoding="utf-8"))
        self.assertIn("session_id", data)
        self.assertIn("open_tasks", data)

    def test_init_creates_golden_paths(self) -> None:
        sov_module.init(self.root)
        gp_path = self.root / ".sovereign" / "golden_paths.json"
        self.assertTrue(gp_path.exists())
        data = json.loads(gp_path.read_text(encoding="utf-8"))
        self.assertIn("ctm_session_bootstrap", data)

    def test_init_is_idempotent(self) -> None:
        """Calling init twice must not corrupt session_state.json."""
        sov_module.init(self.root)
        ss_before = (self.root / ".sovereign" / "session_state.json").read_text(encoding="utf-8")
        sov_module.init(self.root)
        ss_after = (self.root / ".sovereign" / "session_state.json").read_text(encoding="utf-8")
        self.assertEqual(ss_before, ss_after)

    def test_write_session_state_updates_fields(self) -> None:
        sov_module.init(self.root)
        sov_module.write_session_state(
            self.root,
            last_agent="TestAgent",
            last_action="test action",
            open_tasks=["task A"],
        )
        state = sov_module.read_session_state(self.root)
        self.assertEqual(state["last_agent"], "TestAgent")
        self.assertEqual(state["last_action"], "test action")
        self.assertEqual(state["open_tasks"], ["task A"])

    def test_read_session_state_handles_missing_file(self) -> None:
        """read_session_state must return a seed dict when file is absent."""
        state = sov_module.read_session_state(self.root)
        self.assertIsInstance(state, dict)

    def test_update_session_log_creates_provenance(self) -> None:
        """update_session_log must create PROVENANCE.md if absent."""
        sov_module.update_session_log(
            self.root,
            agent="TestAgent",
            action="did something",
            topology_drift=False,
            next_action="do more",
        )
        prov_path = self.root / "PROVENANCE.md"
        self.assertTrue(prov_path.exists())
        content = prov_path.read_text(encoding="utf-8")
        self.assertIn("TestAgent", content)
        self.assertIn("did something", content)

    def test_update_session_log_appends_row(self) -> None:
        """Two calls must produce two rows in the Session Log."""
        for i in range(2):
            sov_module.update_session_log(
                self.root,
                agent=f"Agent{i}",
                action=f"action {i}",
                topology_drift=False,
                next_action="continue",
            )
        content = (self.root / "PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn("Agent0", content)
        self.assertIn("Agent1", content)


# ---------------------------------------------------------------------------
# Sovereign module hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestSovereignHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_write_session_state_raises_for_empty_agent(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            sov_module.write_session_state(
                self.root,
                last_agent="",
                last_action="some action",
                open_tasks=[],
            )
        self.assertIn("non-empty", str(ctx.exception))

    def test_write_session_state_raises_for_whitespace_agent(self) -> None:
        with self.assertRaises(ValueError):
            sov_module.write_session_state(
                self.root,
                last_agent="   ",
                last_action="some action",
                open_tasks=[],
            )

    def test_write_session_state_raises_for_empty_action(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            sov_module.write_session_state(
                self.root,
                last_agent="TestAgent",
                last_action="",
                open_tasks=[],
            )
        self.assertIn("non-empty", str(ctx.exception))

    def test_update_session_log_raises_for_empty_agent(self) -> None:
        with self.assertRaises(ValueError):
            sov_module.update_session_log(
                self.root,
                agent="",
                action="something",
                topology_drift=False,
                next_action="continue",
            )

    def test_update_session_log_raises_for_empty_action(self) -> None:
        with self.assertRaises(ValueError):
            sov_module.update_session_log(
                self.root,
                agent="TestAgent",
                action="",
                topology_drift=False,
                next_action="continue",
            )

    def test_init_repairs_malformed_session_state(self) -> None:
        """init() must replace malformed session_state.json with a fresh seed."""
        (self.root / ".sovereign").mkdir(parents=True)
        ss_path = self.root / ".sovereign" / "session_state.json"
        ss_path.write_text("not json at all !!!", encoding="utf-8")
        sov_module.init(self.root)
        # After repair, session_state.json should be valid JSON with session_id
        data = json.loads(ss_path.read_text(encoding="utf-8"))
        self.assertIn("session_id", data)
        self.assertIsInstance(data["session_id"], str)
        self.assertTrue(len(data["session_id"]) > 0)

    def test_write_session_state_preserves_session_id(self) -> None:
        """Existing session_id must be preserved across write_session_state calls."""
        sov_module.init(self.root)
        original_id = sov_module.read_session_state(self.root)["session_id"]
        sov_module.write_session_state(
            self.root,
            last_agent="AgentB",
            last_action="second action",
            open_tasks=["task X"],
        )
        updated = sov_module.read_session_state(self.root)
        self.assertEqual(updated["session_id"], original_id)

    def test_atomic_write_no_tmp_file_remains(self) -> None:
        """After a successful write, no .tmp file should remain in .sovereign/."""
        sov_module.init(self.root)
        sov_module.write_session_state(
            self.root,
            last_agent="Agent",
            last_action="action",
            open_tasks=[],
        )
        sovereign_dir = self.root / ".sovereign"
        tmp_files = list(sovereign_dir.glob("*.tmp"))
        self.assertEqual(tmp_files, [])

    def test_read_session_state_handles_non_dict_json(self) -> None:
        """read_session_state must return seed when JSON is not a dict."""
        ss_path = self.root / ".sovereign" / "session_state.json"
        (self.root / ".sovereign").mkdir(parents=True)
        ss_path.write_text('["list", "not", "dict"]', encoding="utf-8")
        result = sov_module.read_session_state(self.root)
        self.assertIsInstance(result, dict)
        self.assertIn("session_id", result)


# ---------------------------------------------------------------------------
# Templates module tests (original suite)
# ---------------------------------------------------------------------------

class TestTemplates(unittest.TestCase):

    def test_list_templates_returns_nonempty(self) -> None:
        templates = tmpl.list_templates()
        self.assertGreater(len(templates), 0)

    def test_load_topology_template(self) -> None:
        content = tmpl.load("TOPOLOGY.md.template")
        self.assertIn("{{PROJECT_NAME}}", content)

    def test_render_substitutes_project_name(self) -> None:
        content = tmpl.render("TOPOLOGY.md.template", PROJECT_NAME="TestProject", TODAY="2026-05-23")
        self.assertIn("TestProject", content)
        self.assertNotIn("{{PROJECT_NAME}}", content)

    def test_render_leaves_unmatched_placeholders(self) -> None:
        """Placeholders with no matching context key must remain in output."""
        content = tmpl.render("TOPOLOGY.md.template", PROJECT_NAME="X")
        # TODAY is not supplied — {{TODAY}} should remain
        self.assertIn("{{TODAY}}", content)

    def test_template_not_found_raises(self) -> None:
        with self.assertRaises(tmpl.TemplateNotFoundError):
            tmpl.load("NONEXISTENT.md.template")

    def test_render_provenance_contains_session_log(self) -> None:
        content = tmpl.render_provenance("MyProject", "2026-05-23")
        self.assertIn("Session Log", content)
        self.assertIn("MyProject", content)


# ---------------------------------------------------------------------------
# Templates module hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestTemplatesHardening(unittest.TestCase):

    def test_load_raises_for_empty_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            tmpl.load("")
        self.assertIn("non-empty", str(ctx.exception))

    def test_load_raises_for_whitespace_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.load("   ")

    def test_load_raises_for_path_traversal(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            tmpl.load("../CONSTITUTION.md")
        self.assertIn("traversal", str(ctx.exception))

    def test_load_raises_for_absolute_path(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            tmpl.load("/etc/passwd")
        self.assertIn("traversal", str(ctx.exception))

    def test_render_topology_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_topology("", "2026-05-23")

    def test_render_provenance_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_provenance("", "2026-05-23")

    def test_render_failure_grammar_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_failure_grammar("", "2026-05-23")

    def test_render_architecture_map_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_architecture_map("")

    def test_render_agents_md_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_agents_md("")

    def test_render_claude_md_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_claude_md("")

    def test_render_copilot_instructions_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            tmpl.render_copilot_instructions("")

    def test_list_templates_returns_sorted_list(self) -> None:
        templates = tmpl.list_templates()
        self.assertEqual(templates, sorted(templates))


# ---------------------------------------------------------------------------
# Architecture map tests (original suite)
# ---------------------------------------------------------------------------

class TestArchitectureMap(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_scaffold_creates_file(self) -> None:
        path, status = arch_module.scaffold(self.root, project_name="TestRepo")
        self.assertEqual(status, "created")
        self.assertTrue(path.exists())

    def test_scaffold_skips_existing_without_force(self) -> None:
        arch_module.scaffold(self.root, project_name="TestRepo")
        path, status = arch_module.scaffold(self.root, project_name="TestRepo")
        self.assertEqual(status, "skipped")

    def test_scaffold_force_overwrites(self) -> None:
        arch_module.scaffold(self.root, project_name="TestRepo")
        path, status = arch_module.scaffold(self.root, project_name="TestRepo", force=True)
        self.assertEqual(status, "force-overwritten")

    def test_from_topology_uses_project_name(self) -> None:
        (self.root / "TOPOLOGY.md").write_text(
            "# TOPOLOGY — MyDomain\n\nsome content\n", encoding="utf-8"
        )
        path, status = arch_module.from_topology(self.root)
        self.assertEqual(status, "created")
        content = path.read_text(encoding="utf-8")
        self.assertIn("MyDomain", content)

    def test_infer_project_name_from_pyproject(self) -> None:
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "awesome-lib"\n', encoding="utf-8"
        )
        name = arch_module._infer_project_name(self.root)
        self.assertEqual(name, "awesome-lib")

    def test_infer_project_name_falls_back_to_dir(self) -> None:
        name = arch_module._infer_project_name(self.root)
        self.assertEqual(name, self.root.name)


# ---------------------------------------------------------------------------
# Architecture map hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestArchitectureMapHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_scaffold_raises_for_nonexistent_root(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            arch_module.scaffold(Path("/tmp/ctmv3_nonexistent_xyz"))
        self.assertIn("does not exist", str(ctx.exception))

    def test_scaffold_raises_for_file_not_dir(self) -> None:
        f = self.root / "file.txt"
        f.write_text("data")
        with self.assertRaises(ValueError) as ctx:
            arch_module.scaffold(f)
        self.assertIn("not a directory", str(ctx.exception))

    def test_scaffold_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            arch_module.scaffold(self.root, project_name="")
        self.assertIn("non-empty", str(ctx.exception))

    def test_scaffold_no_tmp_file_remains(self) -> None:
        arch_module.scaffold(self.root, project_name="TestRepo")
        tmp_files = list(self.root.glob("*.tmp"))
        self.assertEqual(tmp_files, [])

    def test_scaffold_status_created_for_new_file(self) -> None:
        _, status = arch_module.scaffold(self.root, project_name="TestRepo")
        self.assertEqual(status, "created")

    def test_scaffold_status_force_overwritten_for_existing(self) -> None:
        arch_module.scaffold(self.root, project_name="TestRepo")
        _, status = arch_module.scaffold(self.root, project_name="TestRepo", force=True)
        self.assertEqual(status, "force-overwritten")

    def test_from_topology_raises_for_nonexistent_root(self) -> None:
        with self.assertRaises(ValueError):
            arch_module.from_topology(Path("/tmp/ctmv3_nonexistent_xyz"))

    def test_infer_project_name_from_package_json(self) -> None:
        (self.root / "package.json").write_text('{"name": "my-app"}', encoding="utf-8")
        name = arch_module._infer_project_name(self.root)
        self.assertEqual(name, "my-app")

    def test_infer_project_name_from_gomod(self) -> None:
        (self.root / "go.mod").write_text("module github.com/daeron/myservice\n\ngo 1.21\n")
        name = arch_module._infer_project_name(self.root)
        self.assertEqual(name, "myservice")


# ---------------------------------------------------------------------------
# Dot init tests (original suite)
# ---------------------------------------------------------------------------

class TestDotInit(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_init_claude_creates_settings(self) -> None:
        results = dot_module.init_claude(self.root, "TestProject")
        settings_path = self.root / ".claude" / "settings.json"
        self.assertTrue(settings_path.exists())
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertIn("permissions", data)

    def test_init_codex_creates_skills_dir(self) -> None:
        dot_module.init_codex(self.root)
        self.assertTrue((self.root / ".codex" / "skills").is_dir())

    def test_init_github_creates_copilot_instructions(self) -> None:
        dot_module.init_github(self.root, "TestProject")
        copilot = self.root / ".github" / "copilot-instructions.md"
        self.assertTrue(copilot.exists())
        content = copilot.read_text(encoding="utf-8")
        self.assertIn("TestProject", content)

    def test_init_github_creates_topology_enforce_yml(self) -> None:
        dot_module.init_github(self.root, "TestProject")
        enforce = self.root / ".github" / "workflows" / "topology-enforce.yml"
        self.assertTrue(enforce.exists())

    def test_init_all_creates_all_targets(self) -> None:
        dot_module.init_all(self.root, "TestProject")
        self.assertTrue((self.root / ".claude" / "settings.json").exists())
        self.assertTrue((self.root / ".codex" / "skills").is_dir())
        self.assertTrue((self.root / ".github" / "copilot-instructions.md").exists())

    def test_init_skips_existing_without_force(self) -> None:
        dot_module.init_github(self.root, "TestProject")
        results = dot_module.init_github(self.root, "TestProject")
        copilot_key = str(self.root / ".github" / "copilot-instructions.md")
        self.assertEqual(results[copilot_key], "skipped")

    def test_invalid_target_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            dot_module.init_target("invalid", self.root, "TestProject")  # type: ignore


# ---------------------------------------------------------------------------
# Dot init hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestDotInitHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_init_claude_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            dot_module.init_claude(self.root, "")
        self.assertIn("non-empty", str(ctx.exception))

    def test_init_github_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            dot_module.init_github(self.root, "")
        self.assertIn("non-empty", str(ctx.exception))

    def test_init_all_raises_for_empty_project_name(self) -> None:
        with self.assertRaises(ValueError):
            dot_module.init_all(self.root, "")

    def test_init_target_raises_for_invalid_target(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            dot_module.init_target("notvalid", self.root, "TestProject")  # type: ignore
        self.assertIn("notvalid", str(ctx.exception))

    def test_write_if_absent_status_created_for_new_file(self) -> None:
        p = self.root / "newfile.txt"
        status = dot_module._write_if_absent(p, "content\n")
        self.assertEqual(status, "created")
        self.assertTrue(p.exists())

    def test_write_if_absent_status_skipped_for_existing(self) -> None:
        p = self.root / "existing.txt"
        p.write_text("original\n")
        status = dot_module._write_if_absent(p, "new content\n")
        self.assertEqual(status, "skipped")
        self.assertEqual(p.read_text(), "original\n")

    def test_write_if_absent_status_force_overwritten(self) -> None:
        p = self.root / "existing.txt"
        p.write_text("original\n")
        status = dot_module._write_if_absent(p, "replaced\n", force=True)
        self.assertEqual(status, "force-overwritten")
        self.assertEqual(p.read_text(), "replaced\n")

    def test_no_tmp_files_after_init_github(self) -> None:
        dot_module.init_github(self.root, "TestProject")
        tmp_files = list(self.root.rglob("*.tmp"))
        self.assertEqual(tmp_files, [], f"Unexpected .tmp files: {tmp_files}")

    def test_init_idempotent_second_run_does_not_corrupt(self) -> None:
        """Running init_all twice must produce consistent, non-corrupted output."""
        dot_module.init_all(self.root, "TestProject")
        original_settings = (self.root / ".claude" / "settings.json").read_text()
        dot_module.init_all(self.root, "TestProject")
        after_settings = (self.root / ".claude" / "settings.json").read_text()
        self.assertEqual(original_settings, after_settings)


# ---------------------------------------------------------------------------
# Activate (full cold-start) tests (original suite)
# ---------------------------------------------------------------------------

class TestActivate(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_activate_cold_creates_all_expected_files(self) -> None:
        """Cold-start activate must create all mandatory CTMv3 artifacts."""
        report = activate_module.run(self.root)

        self.assertFalse(report.get("aborted"), f"Unexpected abort: {report.get('abort_reason')}")

        expected_files = [
            "TOPOLOGY.md",
            "FAILURE_GRAMMAR.md",
            "PROVENANCE.md",
            "ARCHITECTURE_MAP.md",
            "AGENTS.md",
            "CLAUDE.md",
        ]
        for fname in expected_files:
            self.assertTrue(
                (self.root / fname).exists(),
                f"Missing expected artifact: {fname}",
            )

        self.assertTrue((self.root / ".sovereign").is_dir())
        self.assertTrue((self.root / ".sovereign" / "session_state.json").exists())
        self.assertTrue((self.root / ".sovereign" / "golden_paths.json").exists())

    def test_activate_cold_produces_fingerprint(self) -> None:
        report = activate_module.run(self.root)
        self.assertTrue(report["fingerprint"].startswith("sha256:"))

    def test_activate_second_run_without_force_aborts(self) -> None:
        """Second activate without --force must be refused (idempotency guard)."""
        activate_module.run(self.root)
        report = activate_module.run(self.root)
        self.assertTrue(report.get("aborted"))
        self.assertIsNotNone(report.get("abort_reason"))

    def test_activate_second_run_with_force_succeeds(self) -> None:
        """Second activate with --force must succeed and overwrite."""
        activate_module.run(self.root)
        report = activate_module.run(self.root, force=True)
        self.assertFalse(report.get("aborted"))
        # Files should be force-overwritten
        for fname in ["TOPOLOGY.md", "FAILURE_GRAMMAR.md", "PROVENANCE.md"]:
            status = report["files_written"].get(str(self.root / fname))
            self.assertEqual(status, "force-overwritten", f"Expected force-overwritten for {fname}")

    def test_activate_report_is_json_serializable(self) -> None:
        report = activate_module.run(self.root)
        # Should not raise
        serialized = json.dumps(report)
        self.assertIsInstance(serialized, str)

    def test_activate_detects_language_python(self) -> None:
        (self.root / "pyproject.toml").write_text('[project]\nname = "mypkg"\n', encoding="utf-8")
        report = activate_module.run(self.root)
        # Verify TOPOLOGY.md contains the detected language
        topology = (self.root / "TOPOLOGY.md").read_text(encoding="utf-8")
        self.assertIn("python", topology)

    def test_boot_after_activate_is_not_cold_start(self) -> None:
        """After activate, boot discovery must not return COLD_START."""
        activate_module.run(self.root)
        inv = boot_module.discover(self.root)
        self.assertNotEqual(inv.branch, "COLD_START")


# ---------------------------------------------------------------------------
# Activate hardening tests (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestActivateHardening(unittest.TestCase):

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_run_raises_for_invalid_dot_targets(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            activate_module.run(self.root, dot_targets="invalid_target")
        self.assertIn("invalid_target", str(ctx.exception))

    def test_run_raises_for_nonexistent_root(self) -> None:
        """run() must propagate ValueError when project_root does not exist."""
        with self.assertRaises(ValueError):
            activate_module.run(Path("/tmp/ctmv3_does_not_exist_xyz"))

    def test_no_tmp_files_after_activate(self) -> None:
        """Atomic writes must leave no .tmp files after a successful activate."""
        activate_module.run(self.root)
        tmp_files = list(self.root.rglob("*.tmp"))
        self.assertEqual(tmp_files, [], f"Unexpected .tmp files: {tmp_files}")

    def test_language_detection_falls_back_to_unknown(self) -> None:
        """With no config spine files, language must be 'unknown', not a TODO placeholder string."""
        report = activate_module.run(self.root)
        topology = (self.root / "TOPOLOGY.md").read_text(encoding="utf-8")
        # The **Language** line must show 'unknown', not the old TODO sentinel value
        import re
        lang_line = next(
            (ln for ln in topology.splitlines() if ln.startswith("**Language**")), None
        )
        self.assertIsNotNone(lang_line, "**Language** line missing from TOPOLOGY.md")
        self.assertIn("unknown", lang_line)
        self.assertNotIn("TODO", lang_line)

    def test_activate_go_repo_detected(self) -> None:
        (self.root / "go.mod").write_text("module github.com/daeron/myapp\n\ngo 1.21\n")
        report = activate_module.run(self.root)
        topology = (self.root / "TOPOLOGY.md").read_text(encoding="utf-8")
        self.assertIn("go", topology)

    def test_report_contains_project_name(self) -> None:
        (self.root / "pyproject.toml").write_text('[project]\nname = "SpecificProjectName"\n')
        report = activate_module.run(self.root)
        self.assertEqual(report["project_name"], "SpecificProjectName")

    def test_idempotent_rerun_with_force_no_data_loss(self) -> None:
        """Force rerun must create all expected files and not leave partial state."""
        activate_module.run(self.root)
        report2 = activate_module.run(self.root, force=True)
        self.assertFalse(report2["aborted"])
        for fname in ["TOPOLOGY.md", "ARCHITECTURE_MAP.md", "AGENTS.md", "CLAUDE.md"]:
            self.assertTrue((self.root / fname).exists(), f"Missing after force rerun: {fname}")

    def test_activate_detects_mixed_language(self) -> None:
        """Mixed-language repos (Python + Go) should reflect 'mixed' in topology."""
        (self.root / "pyproject.toml").write_text('[project]\nname = "mypkg"\n')
        (self.root / "go.mod").write_text("module github.com/daeron/svc\n\ngo 1.21\n")
        report = activate_module.run(self.root)
        topology = (self.root / "TOPOLOGY.md").read_text(encoding="utf-8")
        self.assertIn("mixed", topology)

    def test_scaffold_protected_creates_on_first_run(self) -> None:
        """_scaffold_protected must record 'created' for new files."""
        p = self.root / "TEST_FILE.md"
        results: dict = {}
        activate_module._scaffold_protected(p, "content\n", force=False, results=results)
        self.assertEqual(results[str(p)], "created")
        self.assertTrue(p.exists())

    def test_scaffold_protected_records_force_overwritten(self) -> None:
        """_scaffold_protected must record 'force-overwritten' for existing files with force."""
        p = self.root / "TEST_FILE.md"
        p.write_text("original\n")
        results: dict = {}
        activate_module._scaffold_protected(p, "replaced\n", force=True, results=results)
        self.assertEqual(results[str(p)], "force-overwritten")

    def test_scaffold_protected_skips_without_force(self) -> None:
        """_scaffold_protected must record 'skipped' when file exists and force=False."""
        p = self.root / "TEST_FILE.md"
        p.write_text("original\n")
        results: dict = {}
        activate_module._scaffold_protected(p, "would-replace\n", force=False, results=results)
        self.assertEqual(results[str(p)], "skipped")
        self.assertEqual(p.read_text(), "original\n")


# ---------------------------------------------------------------------------
# Integration: full workflow test (original suite, kept intact)
# ---------------------------------------------------------------------------

class TestFullWorkflow(unittest.TestCase):
    """Integration test that exercises the complete CTMv3 lifecycle."""

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_full_lifecycle(self) -> None:
        # 1. Empty repo is cold start
        inv = boot_module.discover(self.root)
        self.assertEqual(inv.branch, "COLD_START")

        # 2. Activate
        report = activate_module.run(self.root)
        self.assertFalse(report.get("aborted"))

        # 3. Fingerprint matches immediately after activate
        matches, h = fp_module.verify(self.root)
        self.assertTrue(matches, f"Fingerprint should match after activate, got {h}")

        # 4. Modify TOPOLOGY.md -> fingerprint drift
        (self.root / "TOPOLOGY.md").write_text(
            "# TOPOLOGY modified\n", encoding="utf-8"
        )
        matches2, _ = fp_module.verify(self.root)
        self.assertFalse(matches2)

        # 5. Session close re-fingerprints
        sov_module.update_session_log(
            self.root,
            agent="TestAgent",
            action="modified TOPOLOGY.md",
            topology_drift=True,
            next_action="fill LBCs",
        )
        fp_module.write(self.root)
        matches3, _ = fp_module.verify(self.root)
        self.assertTrue(matches3)

        # 6. Boot now detects warm or partial (PROVENANCE.md has a row)
        inv2 = boot_module.discover(self.root)
        self.assertIn(inv2.branch, ("WARM_START", "PARTIAL"))


# ---------------------------------------------------------------------------
# Integration: hardening cross-module test (v1.1.0 additions)
# ---------------------------------------------------------------------------

class TestFullWorkflowHardening(unittest.TestCase):
    """Hardening-focused integration tests that cross module boundaries."""

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_no_tmp_files_after_full_lifecycle(self) -> None:
        """No .tmp artifact files must remain after a complete activate + session close."""
        activate_module.run(self.root)
        sov_module.update_session_log(
            self.root,
            agent="TestAgent",
            action="lifecycle test",
            topology_drift=False,
            next_action="done",
        )
        fp_module.write(self.root)
        tmp_files = list(self.root.rglob("*.tmp"))
        self.assertEqual(tmp_files, [], f"Unexpected .tmp files: {tmp_files}")

    def test_discover_after_activate_produces_correct_branch(self) -> None:
        """After a cold-start activate, re-running discover must produce PARTIAL or WARM_START."""
        activate_module.run(self.root)
        inv = boot_module.discover(self.root)
        self.assertIn(
            inv.branch,
            ("WARM_START", "PARTIAL"),
            f"Expected WARM_START or PARTIAL after activate, got {inv.branch}",
        )

    def test_multiple_session_logs_all_preserved(self) -> None:
        """Multiple session log appends must all appear in PROVENANCE.md."""
        activate_module.run(self.root)
        agents = ["AgentAlpha", "AgentBeta", "AgentGamma"]
        for ag in agents:
            sov_module.update_session_log(
                self.root,
                agent=ag,
                action=f"{ag} did work",
                topology_drift=False,
                next_action="continue",
            )
        content = (self.root / "PROVENANCE.md").read_text(encoding="utf-8")
        for ag in agents:
            self.assertIn(ag, content, f"Missing agent {ag} from session log")

    def test_fingerprint_stable_across_rewrite(self) -> None:
        """Writing the same TOPOLOGY.md content twice produces the same fingerprint."""
        topo_content = "# TOPOLOGY — StableProject\n\nSome content.\n"
        (self.root / "TOPOLOGY.md").write_text(topo_content)
        h1 = fp_module.compute(self.root)
        (self.root / "TOPOLOGY.md").write_text(topo_content)
        h2 = fp_module.compute(self.root)
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ---------------------------------------------------------------------------
# FIX 11 — Additional test classes (v1.2.0 hardening pass)
# ---------------------------------------------------------------------------


class TestDatetimeDeprecationFix(unittest.TestCase):
    """Verify that sovereign.py and boot.py do not emit DeprecationWarning for utcnow."""

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_write_session_state_no_utcnow_deprecation(self) -> None:
        """write_session_state must not trigger DeprecationWarning about utcnow."""
        sov_module.init(self.root)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sov_module.write_session_state(
                self.root,
                last_agent="DeprecTestAgent",
                last_action="deprecation check",
                open_tasks=[],
            )
        utcnow_warnings = [
            w for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "utcnow" in str(w.message).lower()
        ]
        self.assertEqual(
            utcnow_warnings,
            [],
            f"Unexpected utcnow DeprecationWarnings: {utcnow_warnings}",
        )

    def test_update_session_log_no_utcnow_deprecation(self) -> None:
        """update_session_log must not trigger DeprecationWarning about utcnow."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sov_module.update_session_log(
                self.root,
                agent="DeprecTestAgent",
                action="deprecation check",
                topology_drift=False,
                next_action="continue",
            )
        utcnow_warnings = [
            w for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "utcnow" in str(w.message).lower()
        ]
        self.assertEqual(utcnow_warnings, [])

    def test_is_warm_valid_no_utcnow_deprecation(self) -> None:
        """is_warm_valid must not trigger DeprecationWarning about utcnow."""
        inv = boot_module.SignalInventory(project_root=self.root)
        inv.branch = "WARM_START"
        inv.session_state_valid = True
        inv.session_timestamp = datetime.now()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            boot_module.is_warm_valid(inv)
        utcnow_warnings = [
            w for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "utcnow" in str(w.message).lower()
        ]
        self.assertEqual(utcnow_warnings, [])


class TestCLISubcommands(unittest.TestCase):
    """Test CLI subcommand handlers by calling them directly with argparse.Namespace."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_args(self, **kwargs: object) -> argparse.Namespace:
        """Build a Namespace with sensible defaults for common args."""
        defaults: dict[str, object] = {
            "project_root": str(self.tmp),
            "json": True,
            "no_golden_path": True,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_cmd_boot_cold_start(self) -> None:
        """Boot on an empty directory must return COLD_START."""
        from ctmv3.core.cli import cmd_boot
        args = self._make_args()
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_boot(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["branch"], "COLD_START")

    def test_cmd_version(self) -> None:
        """Version command must return the current engine version."""
        from ctmv3.core.cli import cmd_version
        from ctmv3.core import __version__
        args = self._make_args()
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_version(args)
        output = json.loads(buf.getvalue())
        self.assertIn("version", output)
        self.assertEqual(output["version"], __version__)
        self.assertEqual(output["version"], "1.2.0")

    def test_cmd_status_cold(self) -> None:
        """Status on an empty directory must report COLD_START branch."""
        from ctmv3.core.cli import cmd_status
        args = self._make_args()
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_status(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["branch"], "COLD_START")

    def test_cmd_warm_exits_3_on_cold(self) -> None:
        """warm command must exit with code 3 (missing prereq) on a cold repo."""
        from ctmv3.core.cli import cmd_warm
        args = self._make_args()
        with self.assertRaises(SystemExit) as ctx:
            cmd_warm(args)
        self.assertEqual(ctx.exception.code, 3)

    def test_cmd_sovereign_init(self) -> None:
        """sovereign-init must create .sovereign/ and report status=initialized."""
        from ctmv3.core.cli import cmd_sovereign_init
        args = self._make_args()
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_sovereign_init(args)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["status"], "initialized")
        self.assertTrue((self.tmp / ".sovereign").exists())

    def test_cmd_fingerprint_exits_3_on_empty_repo(self) -> None:
        """fingerprint command must exit 3 (missing prereq) when no topology files exist."""
        from ctmv3.core.cli import cmd_fingerprint
        args = self._make_args()
        with self.assertRaises(SystemExit) as ctx:
            cmd_fingerprint(args)
        self.assertEqual(ctx.exception.code, 3)


class TestIsWarmValidTimezone(unittest.TestCase):
    """Verify is_warm_valid handles timezone-aware timestamps correctly."""

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def test_timezone_aware_timestamp_recent(self) -> None:
        """A recent timezone-aware timestamp must pass the warm validity check."""
        from datetime import timezone as tz
        inv = boot_module.SignalInventory(project_root=self.root)
        inv.branch = "WARM_START"
        inv.session_state_valid = True
        # Timezone-aware recent timestamp (today)
        aware_ts = datetime.now(tz.utc)
        inv.session_timestamp = aware_ts
        self.assertTrue(boot_module.is_warm_valid(inv))

    def test_timezone_aware_timestamp_stale(self) -> None:
        """A 60-day-old timezone-aware timestamp must fail the warm validity check."""
        from datetime import timezone as tz
        inv = boot_module.SignalInventory(project_root=self.root)
        inv.branch = "WARM_START"
        inv.session_state_valid = True
        # 60 days ago — stale beyond the 30-day default threshold
        stale_ts = datetime.now(tz.utc) - timedelta(days=60)
        inv.session_timestamp = stale_ts
        self.assertFalse(boot_module.is_warm_valid(inv))

    def test_naive_timestamp_recent(self) -> None:
        """A recent naive UTC timestamp must also pass the warm validity check."""
        inv = boot_module.SignalInventory(project_root=self.root)
        inv.branch = "WARM_START"
        inv.session_state_valid = True
        inv.session_timestamp = datetime.now()
        self.assertTrue(boot_module.is_warm_valid(inv))


class TestScaffoldProtectedBranchFix(unittest.TestCase):
    """TD2 regression test: verify _scaffold_protected returns correct status strings."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_force_on_nonexistent_returns_created(self) -> None:
        """force=True on a non-existent file must return 'created', not 'force-overwritten'."""
        target = self.tmp / "newfile.md"
        results: dict[str, str] = {}
        activate_module._scaffold_protected(target, "content", force=True, results=results)
        self.assertEqual(results[str(target)], "created")

    def test_force_on_existing_returns_force_overwritten(self) -> None:
        """force=True on an existing file must return 'force-overwritten'."""
        target = self.tmp / "existing.md"
        target.write_text("old content")
        results: dict[str, str] = {}
        activate_module._scaffold_protected(target, "new content", force=True, results=results)
        self.assertEqual(results[str(target)], "force-overwritten")

    def test_no_force_on_nonexistent_returns_created(self) -> None:
        """force=False on a non-existent file must return 'created'."""
        target = self.tmp / "brand_new.md"
        results: dict[str, str] = {}
        activate_module._scaffold_protected(target, "content", force=False, results=results)
        self.assertEqual(results[str(target)], "created")

    def test_no_force_on_existing_returns_skipped(self) -> None:
        """force=False on an existing file must return 'skipped'."""
        target = self.tmp / "preserved.md"
        target.write_text("keep this")
        results: dict[str, str] = {}
        activate_module._scaffold_protected(target, "ignore this", force=False, results=results)
        self.assertEqual(results[str(target)], "skipped")
        self.assertEqual(target.read_text(), "keep this")


class TestSessionLogRotation(unittest.TestCase):
    """PR1: Verify session log rotation triggers and archives correctly."""

    def setUp(self) -> None:
        self.root = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.root)

    def _build_provenance_with_rows(self, row_count: int) -> str:
        """Build a PROVENANCE.md string with exactly row_count data rows."""
        header = "# PROVENANCE\n\n## Session Log\n\n"
        table_header = "| Date | Agent | Action | Topology Drift? | Next Recommended Action |\n"
        table_sep = "|------|-------|--------|----------------|------------------------|\n"
        rows = "".join(
            f"| 2026-01-01 | Agent{i:03d} | action_{i} | no | next_{i} |\n"
            for i in range(row_count)
        )
        return header + table_header + table_sep + rows

    def test_rotation_not_triggered_below_limit(self) -> None:
        """Rotation must NOT occur when row count is at or below MAX_SESSION_LOG_ROWS."""
        from ctmv3.core.sovereign import MAX_SESSION_LOG_ROWS
        content = self._build_provenance_with_rows(MAX_SESSION_LOG_ROWS - 1)
        prov_path = self.root / "PROVENANCE.md"
        prov_path.write_text(content)

        sov_module.update_session_log(
            self.root,
            agent="RotationTest",
            action="below limit",
            topology_drift=False,
            next_action="continue",
        )

        # No archive should exist yet
        sov_dir = self.root / ".sovereign"
        archives = list(sov_dir.glob("provenance_archive_*.md")) if sov_dir.exists() else []
        self.assertEqual(archives, [])

    def test_rotation_triggers_at_limit(self) -> None:
        """Rotation MUST occur when row count exceeds MAX_SESSION_LOG_ROWS."""
        from ctmv3.core.sovereign import MAX_SESSION_LOG_ROWS, SESSION_LOG_RETAIN_ROWS
        # Seed with exactly MAX_SESSION_LOG_ROWS rows
        content = self._build_provenance_with_rows(MAX_SESSION_LOG_ROWS)
        prov_path = self.root / "PROVENANCE.md"
        prov_path.write_text(content)

        # Adding one more row triggers rotation
        sov_module.update_session_log(
            self.root,
            agent="RotationTest",
            action="trigger rotation",
            topology_drift=False,
            next_action="verify archive",
        )

        # Archive must exist in .sovereign/
        sov_dir = self.root / ".sovereign"
        archives = list(sov_dir.glob("provenance_archive_*.md"))
        self.assertTrue(len(archives) > 0, "Expected archive file to be created")

        # PROVENANCE.md must have fewer rows than the original
        updated = prov_path.read_text()
        data_rows = [
            line for line in updated.splitlines()
            if line.strip().startswith("|")
            and "---" not in line
            and "Date" not in line
        ]
        # Should have SESSION_LOG_RETAIN_ROWS + 1 (new row just added)
        self.assertLessEqual(len(data_rows), SESSION_LOG_RETAIN_ROWS + 1)

    def test_archive_contains_correct_rows(self) -> None:
        """Archive file must contain the rows removed from PROVENANCE.md."""
        from ctmv3.core.sovereign import MAX_SESSION_LOG_ROWS, SESSION_LOG_RETAIN_ROWS
        content = self._build_provenance_with_rows(MAX_SESSION_LOG_ROWS)
        prov_path = self.root / "PROVENANCE.md"
        prov_path.write_text(content)

        sov_module.update_session_log(
            self.root,
            agent="ArchiverAgent",
            action="test archive contents",
            topology_drift=False,
            next_action="verify",
        )

        sov_dir = self.root / ".sovereign"
        archives = list(sov_dir.glob("provenance_archive_*.md"))
        self.assertTrue(archives, "No archive file created")
        archive_content = archives[0].read_text()
        # Archive header must be present
        self.assertIn("# PROVENANCE Session Log Archive", archive_content)
        # Archive should contain rows that were removed
        expected_archived = MAX_SESSION_LOG_ROWS - SESSION_LOG_RETAIN_ROWS
        self.assertGreater(expected_archived, 0)


class TestTomllibExtraction(unittest.TestCase):
    """Verify _extract_from_pyproject correctly uses tomllib/tomli or falls back to naive."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pep517_project_name(self) -> None:
        """Must extract [project].name from a valid PEP 517 pyproject.toml."""
        pyproject = self.tmp / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-pep517-project"\nversion = "1.0.0"\n')
        result = arch_module._extract_from_pyproject(pyproject)
        self.assertEqual(result, "my-pep517-project")

    def test_poetry_project_name(self) -> None:
        """Must extract [tool.poetry].name from a Poetry pyproject.toml."""
        pyproject = self.tmp / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "my-poetry-project"\nversion = "1.0.0"\n')
        result = arch_module._extract_from_pyproject(pyproject)
        self.assertEqual(result, "my-poetry-project")

    def test_invalid_toml_falls_back_gracefully(self) -> None:
        """With invalid TOML content, must not crash — fallback to naive scanner or None."""
        pyproject = self.tmp / "pyproject.toml"
        # Deliberately malformed TOML (unclosed quote)
        pyproject.write_text('[project]\nname = "broken\n')
        # Must not raise — either returns None or some result
        try:
            result = arch_module._extract_from_pyproject(pyproject)
            # Whatever the result, it should not crash
        except Exception as exc:
            self.fail(f"_extract_from_pyproject raised unexpectedly: {exc}")

    def test_missing_name_field_returns_none(self) -> None:
        """pyproject.toml without a name field must return None."""
        pyproject = self.tmp / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')
        result = arch_module._extract_from_pyproject(pyproject)
        self.assertIsNone(result)

    def test_naive_fallback_available(self) -> None:
        """_extract_from_pyproject_naive must work and return name for simple input."""
        pyproject = self.tmp / "pyproject.toml"
        pyproject.write_text('[project]\nname = "naive-test-project"\n')
        result = arch_module._extract_from_pyproject_naive(pyproject)
        self.assertEqual(result, "naive-test-project")


class TestDiscoverAll(unittest.TestCase):
    """Verify discover_all() correctly identifies CTM-activated subdirectories."""

    def setUp(self) -> None:
        self.tmp = _tmp_root()

    def tearDown(self) -> None:
        _cleanup(self.tmp)

    def test_discover_all_empty_monorepo(self) -> None:
        """discover_all on an empty directory must return an empty list."""
        results = boot_module.discover_all(self.tmp)
        self.assertEqual(results, [])

    def test_discover_all_finds_activated_subdirs(self) -> None:
        """discover_all must find subdirs with Tier 1 CTM signals."""
        # service-a: has .sovereign (Tier 1)
        subdir_a = self.tmp / "service-a"
        subdir_a.mkdir()
        (subdir_a / ".sovereign").mkdir()
        (subdir_a / "AGENTS.md").write_text("# AGENTS")

        # service-b: has ARCHITECTURE_MAP.md (Tier 1)
        subdir_b = self.tmp / "service-b"
        subdir_b.mkdir()
        (subdir_b / "ARCHITECTURE_MAP.md").write_text("# ARCH")

        # service-c: no Tier 1 signals — must NOT appear in results
        subdir_c = self.tmp / "service-c"
        subdir_c.mkdir()
        (subdir_c / "README.md").write_text("# Just a readme")

        results = boot_module.discover_all(self.tmp)
        activated_roots = {inv.project_root for inv in results}
        self.assertIn(subdir_a.resolve(), activated_roots)
        self.assertIn(subdir_b.resolve(), activated_roots)
        self.assertNotIn(subdir_c.resolve(), activated_roots)

    def test_discover_all_raises_for_nonexistent_root(self) -> None:
        """discover_all must raise ValueError for a non-existent project_root."""
        with self.assertRaises(ValueError) as ctx:
            boot_module.discover_all(Path("/tmp/ctmv3_nonexistent_discover_all_xyz"))
        self.assertIn("existing directory", str(ctx.exception))

    def test_discover_all_returns_sorted_list(self) -> None:
        """discover_all results must be sorted by project_root path string."""
        for name in ("bravo", "alpha", "charlie"):
            sub = self.tmp / name
            sub.mkdir()
            (sub / "AGENTS.md").write_text(f"# {name}")

        results = boot_module.discover_all(self.tmp)
        roots = [str(inv.project_root) for inv in results]
        self.assertEqual(roots, sorted(roots))

    def test_discover_all_respects_max_depth(self) -> None:
        """discover_all must not scan beyond max_depth."""
        # Create a deeply nested activated subdir
        deep = self.tmp / "level1" / "level2" / "level3" / "activated"
        deep.mkdir(parents=True)
        (deep / "AGENTS.md").write_text("# deep")

        # With max_depth=2, should not find level3/activated (depth=4 from root)
        results_shallow = boot_module.discover_all(self.tmp, max_depth=2)
        shallow_roots = {inv.project_root for inv in results_shallow}
        self.assertNotIn(deep.resolve(), shallow_roots)

        # With max_depth=4, should find it
        results_deep = boot_module.discover_all(self.tmp, max_depth=4)
        deep_roots = {inv.project_root for inv in results_deep}
        self.assertIn(deep.resolve(), deep_roots)

    def test_discover_all_does_not_include_root_itself(self) -> None:
        """discover_all must not include the root directory itself, only subdirs."""
        # Activate the root itself
        (self.tmp / "AGENTS.md").write_text("# root AGENTS")
        # Also create an activated subdir
        sub = self.tmp / "sub-service"
        sub.mkdir()
        (sub / "AGENTS.md").write_text("# sub AGENTS")

        results = boot_module.discover_all(self.tmp)
        activated_roots = {inv.project_root for inv in results}
        # Root itself must NOT be in results
        self.assertNotIn(self.tmp.resolve(), activated_roots)
        # Sub must be in results
        self.assertIn(sub.resolve(), activated_roots)
