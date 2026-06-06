#!/usr/bin/env python3
"""
Exoskeleton Tool (V1)

Control-plane layer that makes capability space explorable.
"""

import json
import logging
import os
import math
import re
import threading
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ── Lisan al-Gaib: Prescient subsystems (ALWAYS load — non-negotiable) ────────
try:
    from tools.lisan_al_gaib import (
        CognitiveJournalSubsystem,
        GoldenPathOracle,
        NarrativeEngine,
        _SpectralIntentDecomposer,
        _MCTSPlanner,
        _ThompsonContextualBandit,
        SessionMomentum,
    )
    _LISAN_PRESCIENT_AVAILABLE = True
except ImportError as _imp_err:
    _LISAN_PRESCIENT_AVAILABLE = False
    _SpectralIntentDecomposer = None  # type: ignore[assignment]
    _MCTSPlanner = None               # type: ignore[assignment,misc]
    _ThompsonContextualBandit = None  # type: ignore[assignment,misc]
    SessionMomentum = None            # type: ignore[assignment,misc]
    logging.getLogger(__name__).warning(
        "Lisan prescient subsystems not installed: %s", _imp_err
    )
except Exception as _lisan_prescient_err:
    _LISAN_PRESCIENT_AVAILABLE = False
    _SpectralIntentDecomposer = None  # type: ignore[assignment]
    _MCTSPlanner = None               # type: ignore[assignment,misc]
    _ThompsonContextualBandit = None  # type: ignore[assignment,misc]
    SessionMomentum = None            # type: ignore[assignment,misc]
    logging.getLogger(__name__).error(
        "CRITICAL: Lisan prescient subsystems failed to load due to code/syntax error: %s",
        _lisan_prescient_err,
        exc_info=True
    )

# ── Lisan al-Gaib: Distillation (opt-in, failure is non-fatal) ───────────────
try:
    from tools.lisan_al_gaib import DistillationSubsystem
    _LISAN_DISTILLATION_AVAILABLE = True
except ImportError:
    _LISAN_DISTILLATION_AVAILABLE = False
except Exception as _exc:
    _LISAN_DISTILLATION_AVAILABLE = False
    logging.getLogger(__name__).error(
        "CRITICAL: Lisan distillation failed to load due to code/syntax error: %s",
        _exc,
        exc_info=True
    )

# ── Muad'Dib: Neural substrate twin (opt-in, failure is non-fatal) ───────────
try:
    from muadib.muaddib import DigitalTwinTool as _DigitalTwinTool
    _DIGITAL_TWIN_AVAILABLE = True
except ImportError:
    _DIGITAL_TWIN_AVAILABLE = False
    _DigitalTwinTool = None  # type: ignore[assignment,misc]
except Exception as _exc:
    _DIGITAL_TWIN_AVAILABLE = False
    _DigitalTwinTool = None  # type: ignore[assignment,misc]
    logging.getLogger(__name__).error(
        "CRITICAL: DigitalTwinTool failed to load due to code/syntax error: %s",
        _exc,
        exc_info=True
    )

# ── Muad'Dib advanced mode gate ──────────────────────────────────────────────
# Active by default — server is always running, Q-table has real training data.
# Set MUADIB_ADVANCED_MODE=0 only to emergency-disable.
_MUADIB_ADVANCED_MODE: bool = os.getenv("MUADIB_ADVANCED_MODE", "1") != "0"
_ADV_ALPHA: float = 0.15  # max blend weight for advanced signal

# Backward-compat alias used throughout this module
_LISAN_AVAILABLE = _LISAN_PRESCIENT_AVAILABLE


class ExoskeletonTool:
    """Control-plane orchestration toolset for MCP capability awareness."""

    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        golden_paths_path: Optional[Path] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self._lisan_available = _LISAN_AVAILABLE
        repo_root = Path(__file__).resolve().parent.parent

        # Unified data directory resolution - single source of truth
        configured_data_dir = os.environ.get("SOVEREIGN_DATA_DIR", "").strip()
        if not configured_data_dir:
            # Legacy fallback for existing installations
            configured_data_dir = os.environ.get(
                "MCP_DATA_DIR", str(repo_root / "data")
            )
        self.data_dir = Path(data_dir or configured_data_dir).expanduser().resolve()
        self.exo_dir = self.data_dir / "exoskeleton"
        self.exo_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.exo_dir / "exoskeleton_state.json"
        self.history_file = self.exo_dir / "execution_history.jsonl"
        self.activity_file = self.exo_dir / "cross_ai_activity.jsonl"
        self.checkpoint_file = self.exo_dir / "exo_checkpoints.jsonl"
        self.plans_file = self.exo_dir / "active_plans.json"
        self.manifest_path = (
            Path(manifest_path).expanduser().resolve()
            if manifest_path
            else (repo_root / "tool_manifest.json")
        )
        self._live_tools_provider: Optional[Callable[[], Dict[str, Any]]] = None
        self._last_live_sync_ts = 0.0
        self._spectral_decomposer = (
            _SpectralIntentDecomposer()
            if _LISAN_AVAILABLE and _SpectralIntentDecomposer is not None
            else None
        )

        # Thread-safety for state mutations (reflect, sync)
        self._state_lock = threading.Lock()
        self._plan_counter = 0

        self.category_graph: Dict[str, Set[str]] = {
            "exoskeleton": {
                "memory",
                "project_context",
                "analysis",
                "execution",
                "web",
            },
            "memory": {"sessions", "analysis", "project_context", "exoskeleton"},
            "sessions": {"memory", "analysis", "project_context"},
            "project_context": {"analysis", "execution", "files", "web", "memory"},
            "analysis": {"project_context", "memory", "execution", "web"},
            "execution": {"project_context", "analysis", "files", "web"},
            "web": {"project_context", "analysis", "execution"},
            "files": {"project_context", "analysis", "execution", "memory"},
            "visual": {"execution", "analysis"},
            "system": {"execution", "project_context"},
            "misc": {"project_context", "analysis"},
        }

        self.intent_keywords: Dict[str, List[str]] = {
            "memory": ["memory", "remember", "store", "persist", "history", "context"],
            "sessions": ["session", "workflow", "log", "track", "resume", "pause"],
            "project_context": [
                "project",
                "repo",
                "structure",
                "dependency",
                "changes",
                "codebase",
            ],
            "analysis": ["analyze", "audit", "debug", "issue", "quality", "security"],
            "execution": ["run", "command", "terminal", "execute", "build", "test"],
            "web": ["web", "http", "url", "fetch", "download", "search", "api"],
            "files": ["file", "read", "write", "append", "directory", "path"],
            "visual": ["screen", "window", "screenshot", "visual", "click"],
            "exoskeleton": [
                "plan",
                "route",
                "capability",
                "category",
                "bootstrap",
                "reflect",
            ],
        }

        self.category_latency_penalty = {
            "exoskeleton": 0.02,
            "memory": 0.05,
            "sessions": 0.06,
            "project_context": 0.07,
            "analysis": 0.15,
            "execution": 0.11,
            "web": 0.17,
            "files": 0.05,
            "visual": 0.18,
            "system": 0.05,
            "misc": 0.08,
        }

        self.category_token_estimate = {
            "exoskeleton": 120,
            "memory": 220,
            "sessions": 230,
            "project_context": 300,
            "analysis": 420,
            "execution": 260,
            "web": 320,
            "files": 220,
            "visual": 380,
            "system": 200,
            "misc": 240,
        }

        self.tool_catalog: Dict[str, Dict[str, Any]] = {}
        self.idf: Dict[str, float] = {}
        self._load_catalog()
        self._catalog_manifest_mtime = self._get_manifest_mtime()
        self._refresh_spectral_catalog()

        # Golden paths: pre-trained workflow templates
        self.golden_paths_file = (
            Path(golden_paths_path).expanduser().resolve()
            if golden_paths_path
            else (repo_root / "golden_paths.json")
        )
        self.golden_paths: Dict[str, Dict[str, Any]] = self._filter_golden_paths(
            self._load_json(
                self.golden_paths_file,
                {},
            )
        )

        # Auto-discovered workflows from successful chains (backed by auto_tool_module)
        self._auto_discovered_file = self.exo_dir / "auto_discovered_workflows.json"
        self.auto_discovered_workflows: Dict[str, Dict[str, Any]] = self._load_json(
            self._auto_discovered_file,
            {},
        )

        # Try to integrate with auto_tool_module for sophisticated pattern tracking
        self._auto_tool = None
        try:
            from tools.auto_tool_module import IntelligentOptimizationTool

            self._auto_tool = IntelligentOptimizationTool(str(self.data_dir))
            self.logger.info("Integrated auto_tool_module for pattern analysis")
        except ImportError:
            self.logger.debug(
                "auto_tool_module not available, using basic auto-discovery"
            )
        self.golden_paths: Dict[str, Dict[str, Any]] = self._filter_golden_paths(
            self._load_json(
                self.golden_paths_file,
                {},
            )
        )

        self.state = self._load_state()
        self._ensure_tool_priors()
        self._seed_golden_paths()
        self._save_state()

        # Session-level momentum tracking (non-persistent, per-process)
        self.session_state: Dict[str, Any] = {
            "session_id": f"session_{uuid.uuid4().hex[:8]}_{int(time.time())}",
            "session_start": time.time(),
            "recent_tools": [],
            "recent_categories": [],
            "tool_sequence": [],
            "intent_history": [],
            "active_workflow": None,
        }

        # Category transition probability matrix (learned, persistent)
        self._transitions_file = self.exo_dir / "category_transitions.json"
        self.category_transitions: Dict[str, Dict[str, float]] = self._load_json(
            self._transitions_file,
            self._initialize_transition_matrix(),
        )

        # Active plan checkpoints (persistent across sessions)
        self._active_plans: Dict[str, Dict[str, Any]] = self._load_json(
            self.plans_file,
            {},
        )

        # ── Lisan al-Gaib subsystems ─────────────────────────────────────────
        self._lisan_available = _LISAN_AVAILABLE
        if _LISAN_AVAILABLE:
            try:
                # Distillation is opt-in — only init if module was successfully imported
                self._distillation = (
                    DistillationSubsystem(data_dir=self.data_dir, logger=self.logger)
                    if _LISAN_DISTILLATION_AVAILABLE
                    else None
                )
                self._cognitive_journal = CognitiveJournalSubsystem(
                    data_dir=self.data_dir, logger=self.logger
                )
                self._golden_oracle = GoldenPathOracle(
                    golden_paths_file=self.golden_paths_file, logger=self.logger
                )
                self.logger.info(
                    "Lisan subsystems initialized: cognitive_journal, golden_oracle%s",
                    ", distillation" if self._distillation is not None else "",
                )
            except Exception as _lisan_init_err:
                self.logger.warning(
                    "Lisan subsystem init failed (non-fatal): %s", _lisan_init_err
                )
                self._distillation = None
                self._cognitive_journal = None
                self._golden_oracle = None
        else:
            self._distillation = None
            self._cognitive_journal = None
            self._golden_oracle = None

        # ── Muad'Dib: Neural substrate twin ──────────────────────────────────
        self._digital_twin: Optional[Any] = None
        if _DIGITAL_TWIN_AVAILABLE and _DigitalTwinTool is not None:
            try:
                self._digital_twin = _DigitalTwinTool(data_dir=self.data_dir)
                self.logger.info(
                    "Muad'Dib neural twin initialized (vocab=%d)",
                    self._digital_twin.bb7_dt_status().get("vocab_size_used", 0),
                )
            except Exception as _twin_err:
                self.logger.warning(
                    "Muad'Dib neural twin init failed (non-fatal): %s", _twin_err
                )
                self._digital_twin = None

        # ── Neural attention cache (Gap #4) ───────────────────────────────────
        # Populated by _refresh_spectral_catalog() after catalog encoding.
        # Used by _compute_momentum_bonus() for the neural attention bonus signal.
        self._cached_neural_attention: Dict[str, float] = {}

        # ── MCTS planner (Gap #5) ─────────────────────────────────────────────
        # Drives neural-MCTS rollouts in _make_plans(). Falls back to static
        # chain builder when None. _MCTSPlanner has no required constructor args.
        self._mcts_planner: Optional[Any] = (
            _MCTSPlanner()
            if _LISAN_PRESCIENT_AVAILABLE and _MCTSPlanner is not None
            else None
        )

        # ── Thompson contextual bandit (Gap #7) ───────────────────────────────
        # Stochastic reliability sampling in _reliability_sampled(). Enables
        # organic exploration of under-sampled tools via Beta distribution draws.
        self._thompson_bandit: Optional[Any] = (
            _ThompsonContextualBandit()
            if _LISAN_PRESCIENT_AVAILABLE and _ThompsonContextualBandit is not None
            else None
        )

        # ── SessionMomentum V3 manifold delegate (Gap #8) ────────────────────
        # Wasserstein change-point detection + 7-signal momentum. Delegates from
        # both _update_session_momentum() and _compute_momentum_bonus().
        self._session_momentum: Optional[Any] = (
            SessionMomentum(category_graph=self.category_graph, logger=self.logger)
            if _LISAN_PRESCIENT_AVAILABLE and SessionMomentum is not None
            else None
        )

        subsystem_tags = []
        if self._mcts_planner is not None:
            subsystem_tags.append("mcts")
        if self._thompson_bandit is not None:
            subsystem_tags.append("thompson")
        if self._session_momentum is not None:
            subsystem_tags.append("session_momentum_v3")

        # ── Post-init spectral refresh ────────────────────────────────────────
        # _refresh_spectral_catalog() is called early during _load_catalog()
        # before the digital twin and momentum subsystems exist.  This second
        # call runs with all subsystems live so the neural embedding cache,
        # spectral decomposer, and SessionMomentum manifold are populated on
        # startup rather than waiting for the first catalog mutation.
        self._refresh_spectral_catalog()

        self.logger.info(
            "ExoskeletonTool ready: %d indexed tools, %d golden paths, %d active plans%s%s",
            len(self.tool_catalog),
            len(self.golden_paths),
            len(self._active_plans),
            ", neural_twin=active" if self._digital_twin is not None else "",
            (", subsystems=[" + ",".join(subsystem_tags) + "]") if subsystem_tags else "",
        )

    def _tokenize(self, text: str) -> List[str]:
        if not isinstance(text, str):
            return []
        return [token.lower() for token in self.TOKEN_PATTERN.findall(text)]

    def _load_json(self, path: Path, default: Any) -> Any:
        try:
            if not path.exists():
                return default
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            self.logger.warning("Failed to load %s: %s", path, exc)
            return default

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        last_error: Optional[Exception] = None

        # Cross-process safe write strategy for Windows:
        # 1) write to unique temp file (pid+thread+uuid),
        # 2) atomically replace target,
        # 3) retry on transient file locking errors.
        for attempt in range(8):
            tmp_path = path.parent / (
                f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
            )
            try:
                with open(tmp_path, "w", encoding="utf-8") as handle:
                    handle.write(serialized)
                os.replace(tmp_path, path)
                return
            except OSError as exc:
                last_error = exc
                win_error = getattr(exc, "winerror", None)
                transient = isinstance(exc, PermissionError) or win_error in {5, 32}
                if not transient:
                    raise
                time.sleep(0.02 * (attempt + 1))
            finally:
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                except OSError:
                    pass

        if last_error is not None:
            raise last_error

    def _append_jsonl(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        row = json.dumps(payload, ensure_ascii=False) + "\n"
        for attempt in range(8):
            try:
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write(row)
                return
            except OSError as exc:
                win_error = getattr(exc, "winerror", None)
                transient = isinstance(exc, PermissionError) or win_error in {5, 32}
                if not transient:
                    raise
                time.sleep(0.01 * (attempt + 1))

    def _tool_category(self, tool_name: str, description: str) -> str:
        name = tool_name.lower()
        desc = description.lower()
        if name.startswith("bb7_exo_"):
            return "exoskeleton"
        if "memory" in name:
            return "memory"
        if any(
            marker in name for marker in ["session", "workflow", "insight", "focus"]
        ):
            return "sessions"
        if any(
            marker in name
            for marker in ["project", "dependencies", "recent_changes", "code_metrics"]
        ):
            return "project_context"
        if any(
            marker in name
            for marker in [
                "analyze",
                "audit",
                "security",
                "python_execute",
                "optimization",
                "adaptive",
            ]
        ):
            return "analysis"
        if any(
            marker in name
            for marker in [
                "fetch",
                "download",
                "check_url",
                "search_web",
                "extract_links",
            ]
        ):
            return "web"
        if any(
            marker in name
            for marker in [
                "read_file",
                "write_file",
                "append_file",
                "list_directory",
                "search_files",
                "get_file_info",
            ]
        ):
            return "files"
        if any(
            marker in name
            for marker in [
                "run_command",
                "terminal",
                "list_processes",
                "get_system_info",
            ]
        ):
            return "execution"
        if any(
            marker in name
            for marker in ["screen", "window", "screenshot", "click", "find_on_screen"]
        ):
            return "visual"
        if name == "ping_server":
            return "system"
        if "web" in desc or "url" in desc:
            return "web"
        if "memory" in desc:
            return "memory"
        return "misc"

    def _load_catalog(self) -> None:
        manifest = self._load_json(self.manifest_path, {})
        tools = manifest.get("tools", []) if isinstance(manifest, dict) else []
        if not isinstance(tools, list):
            tools = []

        catalog: Dict[str, Dict[str, Any]] = {}
        token_docs: List[List[str]] = []

        for entry in tools:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            description = str(entry.get("description", "")).strip()
            schema = (
                entry.get("input_schema", {})
                if isinstance(entry.get("input_schema"), dict)
                else {}
            )
            properties = (
                schema.get("properties", {})
                if isinstance(schema.get("properties"), dict)
                else {}
            )
            required = (
                schema.get("required", [])
                if isinstance(schema.get("required"), list)
                else []
            )
            required_params = [p for p in required if isinstance(p, str)]

            tokens = self._tokenize(
                " ".join([name, description, " ".join(properties.keys())])
            )
            token_docs.append(tokens)
            category = self._tool_category(name, description)
            catalog[name] = {
                "name": name,
                "description": description,
                "category": category,
                "required_params": required_params,
                "token_counts": Counter(tokens),
            }

        doc_count = max(1, len(token_docs))
        freq: Dict[str, int] = defaultdict(int)
        for tokens in token_docs:
            for token in set(tokens):
                freq[token] += 1
        idf = {
            token: math.log((1.0 + doc_count) / (1.0 + count)) + 1.0
            for token, count in freq.items()
        }

        self.tool_catalog = catalog
        self.idf = idf

    def _get_manifest_mtime(self) -> Optional[float]:
        """Return manifest mtime when available, otherwise None."""
        try:
            if self.manifest_path.exists():
                return float(self.manifest_path.stat().st_mtime)
        except Exception:
            return None
        return None

    def _refresh_catalog_from_manifest_if_changed(
        self, force: bool = False
    ) -> Dict[str, Any]:
        """Refresh manifest-derived catalog when manifest changes, preserving priors."""
        current_mtime = self._get_manifest_mtime()
        previous_mtime = getattr(self, "_catalog_manifest_mtime", None)
        changed = bool(force) or (current_mtime != previous_mtime)
        if not changed:
            return {
                "reloaded": False,
                "manifest_mtime": current_mtime,
                "indexed_tools": len(self.tool_catalog),
            }

        # Reload base catalog from manifest, then re-ensure priors.
        self._load_catalog()
        self._refresh_spectral_catalog()
        with self._state_lock:
            self._ensure_tool_priors()
            self._save_state()

        self._catalog_manifest_mtime = current_mtime
        return {
            "reloaded": True,
            "manifest_mtime": current_mtime,
            "indexed_tools": len(self.tool_catalog),
        }

    def _tool_prior_diagnostics(self) -> Dict[str, Any]:
        """Summarize alpha/beta persistence health for quick bootstrap visibility."""
        priors = self.state.get("tool_priors", {})
        if not isinstance(priors, dict):
            priors = {}

        alphas: List[float] = []
        betas: List[float] = []
        zero_alpha_or_beta = 0
        cold_start = 0

        for prior in priors.values():
            if not isinstance(prior, dict):
                continue
            alpha = float(prior.get("alpha", 1.0))
            beta = float(prior.get("beta", 1.0))
            alphas.append(alpha)
            betas.append(beta)
            if alpha <= 0.0 or beta <= 0.0:
                zero_alpha_or_beta += 1
            if abs(alpha - 1.0) < 1e-9 and abs(beta - 1.0) < 1e-9:
                cold_start += 1

        return {
            "tool_prior_count": len(alphas),
            "alpha_min": min(alphas) if alphas else None,
            "alpha_max": max(alphas) if alphas else None,
            "beta_min": min(betas) if betas else None,
            "beta_max": max(betas) if betas else None,
            "zero_alpha_or_beta_count": zero_alpha_or_beta,
            "cold_start_count": cold_start,
            "state_file": str(self.state_file),
        }

    def _required_params_from_tool_info(self, tool_info: Dict[str, Any]) -> List[str]:
        """Extract required parameters from legacy and schema-style metadata."""
        params = tool_info.get("parameters")
        if isinstance(params, list) and params:
            required_params = [
                str(p.get("name", "")).strip()
                for p in params
                if isinstance(p, dict) and p.get("required")
            ]
            return [name for name in required_params if name]
        if isinstance(params, dict):
            schema_required = params.get("required", [])
            return [r for r in schema_required if isinstance(r, str)]

        for schema_key in ("inputSchema", "input_schema"):
            schema = tool_info.get(schema_key)
            if isinstance(schema, dict):
                schema_required = schema.get("required", [])
                return [r for r in schema_required if isinstance(r, str)]

        return []

    def _rebuild_idf(self) -> None:
        """Rebuild IDF weights from the current tool catalog."""
        token_docs = [
            list(info.get("token_counts", {}).keys())
            for info in self.tool_catalog.values()
        ]
        doc_count = max(1, len(token_docs))
        freq: Dict[str, int] = defaultdict(int)
        for tokens in token_docs:
            for token in set(tokens):
                freq[token] += 1
        self.idf = {
            token: math.log((1.0 + doc_count) / (1.0 + count)) + 1.0
            for token, count in freq.items()
        }
        self._refresh_spectral_catalog()

    def _refresh_spectral_catalog(self) -> None:
        """Keep lisan's spectral decomposer aligned with the live tool catalog."""
        if not getattr(self, "_lisan_available", _LISAN_AVAILABLE) or self._spectral_decomposer is None:
            return
        try:
            self._spectral_decomposer.rebuild_idf(self.tool_catalog)
        except Exception as exc:
            self.logger.debug("Spectral catalog refresh failed: %s", exc)

        # ── Muad'Dib: inject neural embeddings into spectral decomposer ─────────
        # bb7_dt_encode_catalog() encodes the full tool catalog in one forward pass,
        # returning per-tool 512-dim vectors.  These feed two consumers:
        #   1. _spectral_decomposer.inject_neural_embeddings() — 30% neural blend
        #      in spectral_similarity() for intent matching.
        #   2. _cached_neural_attention — per-category mean L1-norm, normalized,
        #      injected into the SessionMomentum manifold for the spectral graph
        #      momentum signal (Gap #6 fix).
        twin = getattr(self, "_digital_twin", None)
        if twin is not None and hasattr(twin, "bb7_dt_encode_catalog"):
            try:
                tool_names = list(self.tool_catalog.keys())
                if tool_names:
                    tool_categories = {
                        n: info.get("category", "misc")
                        for n, info in self.tool_catalog.items()
                    }
                    encode_result = twin.bb7_dt_encode_catalog(tool_names, tool_categories)
                    if isinstance(encode_result, dict) and encode_result.get("ok"):
                        embeddings: Dict[str, Any] = encode_result.get("embeddings", {})
                        if embeddings:
                            # ── Consumer 1: spectral decomposer neural blend ──
                            self._spectral_decomposer.inject_neural_embeddings(embeddings)
                            self.logger.debug(
                                "Neural embeddings injected into spectral decomposer (%d tools)",
                                len(embeddings),
                            )

                            # ── Consumer 2: per-category attention weights ────
                            # Mean L1-norm of embedding vectors grouped by category,
                            # normalized to [0, 1].  These weight the neural attention
                            # bonus in _compute_momentum_bonus() and feed the
                            # SessionMomentum manifold's inject_neural_attention().
                            cat_sum: Dict[str, float] = defaultdict(float)
                            cat_cnt: Dict[str, int] = defaultdict(int)
                            for tool_name, vec in embeddings.items():
                                cat = self.tool_catalog.get(tool_name, {}).get("category", "misc")
                                l1_norm = sum(abs(x) for x in vec) / max(1, len(vec))
                                cat_sum[cat] += l1_norm
                                cat_cnt[cat] += 1

                            cat_attn = {
                                cat: cat_sum[cat] / max(1, cat_cnt[cat])
                                for cat in cat_sum
                            }
                            max_v = max(cat_attn.values()) if cat_attn else 1.0
                            normalized: Dict[str, float] = {
                                cat: val / max(1e-9, max_v)
                                for cat, val in cat_attn.items()
                            }
                            self._cached_neural_attention = normalized

                            # ── Consumer 2b: push into SessionMomentum manifold ─
                            sm = getattr(self, "_session_momentum", None)
                            if sm is not None:
                                try:
                                    sm._manifold.inject_neural_attention(normalized)
                                    self.logger.debug(
                                        "Neural attention injected into SessionMomentum "
                                        "manifold (%d categories)",
                                        len(normalized),
                                    )
                                except Exception as _sm_inject_err:
                                    self.logger.debug(
                                        "Manifold neural attention inject failed: %s",
                                        _sm_inject_err,
                                    )
            except Exception as _embed_err:
                self.logger.warning(
                    "Neural embedding injection failed (non-fatal): %s", _embed_err
                )

    def attach_live_tools_provider(
        self, provider: Callable[[], Dict[str, Any]]
    ) -> None:
        """Attach a callable that returns the server's current live tool registry."""
        if not callable(provider):
            raise TypeError("provider must be callable")
        self._live_tools_provider = provider
        self._last_live_sync_ts = 0.0

    def _maybe_sync_live_tools(
        self, force: bool = False, min_interval_sec: float = 2.0
    ) -> Dict[str, int]:
        """
        Sync catalog from live registry when provider is attached.
        Uses a short interval guard to avoid redundant rebuilds on rapid calls.
        """
        if self._live_tools_provider is None:
            return {"added": 0, "updated": 0}
        now = time.time()
        if (not force) and ((now - self._last_live_sync_ts) < float(min_interval_sec)):
            return {"added": 0, "updated": 0}
        try:
            live_tools = self._live_tools_provider()
            if not isinstance(live_tools, dict):
                return {"added": 0, "updated": 0}
            counts = self.sync_from_live_tools(live_tools)
            self._last_live_sync_ts = now
            return counts
        except Exception as exc:
            self.logger.warning("Live tool sync from provider failed: %s", exc)
            return {"added": 0, "updated": 0}

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "updated_at": time.time(),
            "tool_priors": {},
            "chain_priors": {},
            "intent_to_tool_mappings": {},
            "failure_recovery_strategies": {},
            "recent_outcomes": [],
            "discovered_macros": [],
        }

    def _load_state(self) -> Dict[str, Any]:
        state = self._load_json(self.state_file, self._default_state())
        if not isinstance(state, dict):
            state = self._default_state()
        state.setdefault("version", 1)
        state.setdefault("updated_at", time.time())
        state.setdefault("tool_priors", {})
        state.setdefault("chain_priors", {})
        state.setdefault("intent_to_tool_mappings", {})
        state.setdefault("failure_recovery_strategies", {})
        state.setdefault("recent_outcomes", [])
        state.setdefault("discovered_macros", [])
        return state

    def _save_state(self) -> None:
        self.state["updated_at"] = time.time()
        try:
            self._write_json(self.state_file, self.state)
        except Exception as exc:
            # Persistence failures should not disable tool registration.
            self.logger.warning(
                "Failed to persist exoskeleton state to %s: %s", self.state_file, exc
            )
        # Piggyback: persist neural twin checkpoint alongside exo state
        twin = getattr(self, "_digital_twin", None)
        if twin is not None:
            try:
                twin.bb7_dt_save()
            except Exception as e:
                self.logger.warning("DigitalTwinTool save failed (non-fatal): %s", e)

    def _ensure_tool_priors(self) -> None:
        priors = self.state.get("tool_priors", {})
        for tool_name in self.tool_catalog.keys():
            if tool_name not in priors:
                priors[tool_name] = {
                    "alpha": 1.0,
                    "beta": 1.0,
                    "successes": 0,
                    "failures": 0,
                    "last_error": "",
                }
        self.state["tool_priors"] = priors

    @staticmethod
    def _is_valid_golden_path_entry(path_name: str, path_data: Any) -> bool:
        """Return True only for executable golden-path workflow entries."""
        if not isinstance(path_name, str) or path_name.startswith("_"):
            return False
        if not isinstance(path_data, dict):
            return False
        chain = path_data.get("chain")
        if not isinstance(chain, list) or not chain:
            return False
        if not all(isinstance(step, str) and step.strip() for step in chain):
            return False
        priors = path_data.get("priors")
        if not isinstance(priors, dict):
            return False
        try:
            alpha = float(priors["alpha"])
            beta = float(priors["beta"])
        except (KeyError, TypeError, ValueError):
            return False
        return alpha > 0.0 and beta > 0.0

    def _filter_golden_paths(self, raw_paths: Any) -> Dict[str, Dict[str, Any]]:
        """Strip metadata/corrupt entries from executable routing maps."""
        if not isinstance(raw_paths, dict):
            return {}
        return {
            path_name: path_data
            for path_name, path_data in raw_paths.items()
            if self._is_valid_golden_path_entry(path_name, path_data)
        }

    # ------------------------------------------------------------------ #
    #  GOLDEN PATHS — Pre-trained workflow intelligence                    #
    # ------------------------------------------------------------------ #

    def _seed_golden_paths(self) -> None:
        """Seed chain priors with golden path data on first run or when new paths added.

        Provides pre-trained expertise so the system routes intelligently from
        the very first interaction instead of requiring 10-20 trial-and-error
        calls for priors to converge past Beta(1,1).
        """
        seeded = 0
        for path_name, path_data in self._filter_golden_paths(self.golden_paths).items():
            chain = path_data.get("chain", [])
            if not chain:
                continue
            chain_key = " > ".join(chain)
            existing = self.state["chain_priors"].get(chain_key, {})
            existing_trials = int(existing.get("successes", 0)) + int(
                existing.get("failures", 0)
            )
            if existing_trials >= 3:
                continue  # Already has real observation data — don't overwrite
            alpha = float(path_data.get("priors", {}).get("alpha", 1.0))
            beta = float(path_data.get("priors", {}).get("beta", 1.0))
            self.state["chain_priors"][chain_key] = {
                "alpha": alpha,
                "beta": beta,
                "successes": max(0, int(alpha) - 1),
                "failures": max(0, int(beta) - 1),
                "seeded_from": path_name,
                "seeded_at": time.time(),
            }
            seeded += 1
        if seeded:
            self.logger.info("Seeded %d golden paths into chain priors", seeded)

    def _promote_successful_chain_to_workflow(self, chain_key: str) -> None:
        """Promote a frequently successful chain to auto-discovered workflow.

        Uses auto_tool_module's SQLite pattern storage when available for
        sophisticated efficiency tracking.
        """
        if chain_key in self.auto_discovered_workflows:
            return

        prior = self.state.get("chain_priors", {}).get(chain_key)
        if not prior:
            return

        successes = int(prior.get("successes", 0))
        failures = int(prior.get("failures", 0))

        if successes < 5:
            return

        # If auto_tool_module available, record as sophisticated pattern
        if self._auto_tool is not None:
            try:
                import sqlite3

                conn = sqlite3.connect(str(self._auto_tool.patterns_db))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO workflow_patterns 
                    (id, pattern_type, pattern_data, frequency, efficiency_score)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        f"chain_{abs(hash(chain_key)) % 100000}",
                        "tool_chain",
                        json.dumps(
                            {
                                "chain": chain_key.split(" > "),
                                "successes": successes,
                                "failures": failures,
                                "source": "exoskeleton_auto_discovery",
                            }
                        ),
                        successes,
                        successes / max(1, successes + failures),
                    ),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                self.logger.debug(f"Failed to record pattern in auto_tool: {e}")

        chain = chain_key.split(" > ")
        alpha = float(prior.get("alpha", 1.0))
        beta = float(prior.get("beta", 1.0))
        reliability = alpha / max(0.0001, alpha + beta)

        workflow_name = f"auto_{chain[0].replace('bb7_', '')}_{len(chain)}step"

        self.auto_discovered_workflows[chain_key] = {
            "name": workflow_name,
            "chain": chain,
            "description": f"Auto-discovered workflow from {successes} successful executions",
            "use_cases": [f"execute {' + '.join(chain[:2])}"],
            "tags": ["auto-discovered", "proven"],
            "priors": {"alpha": alpha, "beta": beta},
            "successes": successes,
            "reliability": reliability,
            "discovered_at": time.time(),
        }
        self._write_json(self._auto_discovered_file, self.auto_discovered_workflows)
        self.logger.info(
            "Promoted chain to auto-discovered workflow: %s", workflow_name
        )

        # ── Auto-promote to golden_paths.json ─────────────────────────────
        # Only promote if reliability is high enough and chain is novel
        if reliability >= 0.75 and len(chain) >= 2:
            self._auto_promote_to_golden_paths(
                workflow_name=workflow_name,
                chain=chain,
                alpha=alpha,
                beta=beta,
                reliability=reliability,
                successes=successes,
                failures=failures,
            )

    def _auto_promote_to_golden_paths(
        self,
        workflow_name: str,
        chain: List[str],
        alpha: float,
        beta: float,
        reliability: float,
        successes: int,
        failures: int,
    ) -> None:
        """
        Auto-promote a proven chain to golden_paths.json for session-start routing.

        This closes the loop: discovered chains become part of the canonical
        golden path set, ensuring the system learns from its own successes.
        """
        # Check if we're likely to corrupt the golden_paths.json
        if (
            not hasattr(self, "golden_paths_file")
            or not self.golden_paths_file.exists()
        ):
            return

        try:
            current_golden = self._load_json(self.golden_paths_file, {})
            if not isinstance(current_golden, dict):
                current_golden = {}
            current_golden_runtime = self._filter_golden_paths(current_golden)
            auto_path_key = f"auto_discovered_{workflow_name}"

            # Avoid duplicating existing executable paths while preserving raw metadata if present.
            if auto_path_key in current_golden_runtime:
                return
            for existing in current_golden_runtime.values():
                if isinstance(existing, dict) and existing.get("chain") == chain:
                    return

            # Create new golden path entry
            current_golden[auto_path_key] = {
                "chain": chain,
                "priors": {"alpha": alpha, "beta": beta},
                "description": f"Auto-discovered from {successes} successful executions (reliability={reliability:.2%})",
                "use_cases": [f"auto-execute {chain[0]} → {' → '.join(chain[1:])}"],
                "tags": ["auto-discovered", "proven", "autonomous-discovery"],
                "estimated_tokens": 500 + len(chain) * 100,
                "avg_latency_seconds": 2.0 * len(chain),
                "prerequisites": [],
                "expected_outputs": ["executed_chain", "reflection"],
                "auto_discovered": True,
                "discovery_timestamp": time.time(),
                "success_count": successes,
            }

            self._write_json(self.golden_paths_file, current_golden)
            self.golden_paths = self._filter_golden_paths(current_golden)
            if self._golden_oracle is not None:
                try:
                    self._golden_oracle.golden_paths = dict(self.golden_paths)
                    if hasattr(self._golden_oracle, "_rebuild_spectral_index"):
                        self._golden_oracle._rebuild_spectral_index()
                except Exception as _oracle_sync_err:
                    self.logger.debug(
                        "GoldenPathOracle refresh failed after auto-promotion: %s",
                        _oracle_sync_err,
                    )
            self.logger.info(
                "Auto-promoted %s to golden_paths.json (reliability=%.2f%%)",
                auto_path_key,
                reliability * 100,
            )

            # Re-seed the chain priors so it's immediately available
            chain_key = " > ".join(chain)
            if chain_key not in self.state.get("chain_priors", {}):
                self.state.setdefault("chain_priors", {})[chain_key] = {
                    "alpha": alpha,
                    "beta": beta,
                    "successes": successes,
                    "failures": failures,
                    "seeded_from": "auto_promotion",
                    "seeded_at": time.time(),
                }
                self._save_state()

        except Exception as _promo_err:
            self.logger.debug(
                "Auto-promotion to golden_paths failed (non-fatal): %s", _promo_err
            )

    def _normalize_golden_match(
        self,
        match: Optional[Dict[str, Any]],
        fallback_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Normalize golden-path payloads to always expose both name and path_name."""
        if not isinstance(match, dict):
            return None
        normalized = dict(match)
        canonical_name = str(
            normalized.get("path_name")
            or normalized.get("name")
            or fallback_name
            or ""
        ).strip()
        if canonical_name:
            normalized["path_name"] = canonical_name
            normalized["name"] = canonical_name
        chain = normalized.get("chain")
        if not isinstance(chain, list):
            normalized["chain"] = []
        return normalized

    def _match_golden_path(self, intent: str) -> Optional[Dict[str, Any]]:
        """Find the best golden path or auto-discovered workflow for an intent."""
        # Spectral oracle (lisan) first
        if self._golden_oracle is not None:
            try:
                oracle_match = self._golden_oracle.match_golden_path(intent)
                normalized_oracle = self._normalize_golden_match(oracle_match)
                if normalized_oracle is not None:
                    return normalized_oracle
            except Exception as _oracle_err:
                self.logger.debug(
                    "GoldenPathOracle match failed, using keyword fallback: %s",
                    _oracle_err,
                )

        intent_lower = intent.lower()
        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0

        all_workflows: Dict[str, Dict[str, Any]] = {}
        for key, value in self.golden_paths.items():
            if isinstance(value, dict):
                all_workflows[key] = value
        for key, value in self.auto_discovered_workflows.items():
            if isinstance(value, dict):
                all_workflows[f"auto:{key}"] = value

        for key, path_data in all_workflows.items():
            use_case_hits = 0
            for uc in path_data.get("use_cases", []):
                uc_lower = str(uc).lower()
                if uc_lower and (uc_lower in intent_lower or intent_lower in uc_lower):
                    use_case_hits += 1
            tag_hits = 0
            for tag in path_data.get("tags", []):
                tag_lower = str(tag).lower()
                if tag_lower and (tag_lower in intent_lower or intent_lower in tag_lower):
                    tag_hits += 1
            score = use_case_hits * 2.0 + tag_hits * 1.0
            if score > best_score:
                best_score = score
                fallback_name = str(path_data.get("name") or key.replace("auto:", "")).strip()
                best_match = self._normalize_golden_match(path_data, fallback_name=fallback_name)

        return best_match if best_score >= 1.0 else None

    # ------------------------------------------------------------------ #
    #  MOMENTUM TRACKING — Session-aware contextual flow                   #
    # ------------------------------------------------------------------ #

    def _initialize_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Create default category transition probabilities.

        Connected categories (per ``category_graph``) start at 1.0;
        unconnected start at 0.1 so they aren't completely invisible.
        """
        categories = list(self.category_graph.keys())
        matrix: Dict[str, Dict[str, float]] = {}
        for from_cat in categories:
            neighbors = self.category_graph.get(from_cat, set())
            matrix[from_cat] = {
                to_cat: (1.0 if (to_cat in neighbors or to_cat == from_cat) else 0.1)
                for to_cat in categories
            }
        return matrix

    def _update_session_momentum(self, tool_name: str, intent: str) -> None:
        """Track session-level tool usage for momentum-aware scoring.

        Called automatically during ``bb7_exo_reflect``.  Maintains recency
        lists, full sequence, category transition learning, and active-
        workflow detection.
        """
        now = time.time()
        category = self.tool_catalog.get(tool_name, {}).get("category", "misc")

        # Recent tools ring buffer (last 5)
        self.session_state["recent_tools"].append(
            {
                "tool": tool_name,
                "category": category,
                "timestamp": now,
                "intent": intent,
            }
        )
        self.session_state["recent_tools"] = self.session_state["recent_tools"][-5:]

        # Recent categories (deduplicated, most-recent-first, max 3)
        cats = self.session_state["recent_categories"]
        if category in cats:
            cats.remove(category)
        cats.insert(0, category)
        self.session_state["recent_categories"] = cats[:3]

        # Full session sequence (unbounded within a process lifetime)
        self.session_state["tool_sequence"].append(
            {
                "tool": tool_name,
                "category": category,
                "timestamp": now,
            }
        )

        # Intent history
        self.session_state["intent_history"].append(
            {
                "intent": intent,
                "timestamp": now,
            }
        )

        # Online transition-probability learning
        seq = self.session_state["tool_sequence"]
        if len(seq) >= 2:
            prev_cat = seq[-2]["category"]
            curr_cat = category
            if prev_cat in self.category_transitions:
                self.category_transitions[prev_cat][curr_cat] = (
                    self.category_transitions[prev_cat].get(curr_cat, 0.1) + 0.1
                )
                row_sum = sum(self.category_transitions[prev_cat].values()) or 1.0
                self.category_transitions[prev_cat] = {
                    k: v / row_sum
                    for k, v in self.category_transitions[prev_cat].items()
                }
                # Persist learned transitions periodically (every 10 updates)
                if len(seq) % 10 == 0:
                    self._write_json(self._transitions_file, self.category_transitions)

        # Detect active workflow
        self._detect_active_workflow()

        # ── SessionMomentum V3 manifold delegate ────────────────────────────
        # The inline session_state updates above maintain backward-compatible
        # state for _compute_momentum_bonus().  SessionMomentum.update() runs
        # the Wasserstein change-point detection, exponential attention decay,
        # and golden-path detection in the topological manifold so the V3
        # 7-signal bonus is available at next _compute_momentum_bonus() call.
        if self._session_momentum is not None:
            category = self.tool_catalog.get(tool_name, {}).get("category", "misc")
            try:
                self._session_momentum.update(
                    tool_name, category, intent, self.golden_paths
                )
            except Exception as _sm_err:
                self.logger.debug("SessionMomentum.update failed (non-fatal): %s", _sm_err)

    def _detect_active_workflow(self) -> None:
        """Check if the current tool sequence matches a golden path prefix.

        If detected, store the remaining steps + confidence so momentum
        scoring can boost the next logical tool.
        """
        seq = self.session_state["tool_sequence"]
        if len(seq) < 2:
            self.session_state["active_workflow"] = None
            return
        recent = [t["tool"] for t in seq[-4:]]
        for path_name, path_data in self._filter_golden_paths(self.golden_paths).items():
            golden = path_data.get("chain", [])
            for offset in range(len(golden) - len(recent) + 1):
                if golden[offset : offset + len(recent)] == recent:
                    position = offset + len(recent)
                    remaining = golden[position:]
                    alpha = float(path_data.get("priors", {}).get("alpha", 1.0))
                    beta = float(path_data.get("priors", {}).get("beta", 1.0))
                    self.session_state["active_workflow"] = {
                        "name": path_name,
                        "chain": golden,
                        "position": position,
                        "remaining": remaining,
                        "confidence": alpha / max(0.0001, alpha + beta),
                    }
                    return
        self.session_state["active_workflow"] = None

    def _compute_momentum_bonus(self, tool_name: str, tool_category: str) -> float:
        """Compute momentum-based score bonus for a tool.

        Returns a float in ``[0.0, 0.30]`` combining:
        - Active-workflow position bonus (up to +0.20)
        - Category adjacency bonus (+0.12)
        - Same-category continuation (+0.08)
        - Learned transition probability (+0.08)
        - Category recency decay (+0.05)
        - Neural attention bonus (up to +0.05, Muad'Dib Phase 3)

        Capped at 0.30 to avoid overwhelming semantic/reliability signals.
        """
        if not self.session_state["recent_tools"]:
            return 0.0
        bonus = 0.0

        # 1. Active workflow bonus (strongest signal)
        wf = self.session_state["active_workflow"]
        if wf and tool_name in wf.get("remaining", []):
            bonus += 0.20 * wf.get("confidence", 0.5)

        # 2. Category adjacency / continuation
        last_cat = self.session_state["recent_tools"][-1]["category"]
        if tool_category in self.category_graph.get(last_cat, set()):
            bonus += 0.12
        elif tool_category == last_cat:
            bonus += 0.08

        # 3. Learned transition probability
        tp = self.category_transitions.get(last_cat, {}).get(tool_category, 0.0)
        if tp > 0.5:
            bonus += min(0.08, (tp - 0.5) * 0.16)

        # 4. Recency decay
        rcats = self.session_state["recent_categories"]
        if tool_category in rcats:
            bonus += 0.05 * (0.6 ** rcats.index(tool_category))

        # 5. Neural attention bonus (Muad'Dib Phase 3)
        neural_attn = getattr(self, "_cached_neural_attention", {})
        if isinstance(neural_attn, dict) and tool_category in neural_attn:
            bonus += min(0.05, float(neural_attn[tool_category]) * 0.05)

        # 6. SessionMomentum V3 signal — Wasserstein change-point + 7-signal blend
        # The V3 manifold computes a richer momentum bonus incorporating
        # spectral graph momentum, exponential attention decay, and topological
        # change-point detection.  We take max(symbolic, V3) rather than
        # adding, so a strong V3 signal replaces a weak symbolic one without
        # double-counting.
        if self._session_momentum is not None and self._session_momentum.recent_tools:
            try:
                sm_bonus = self._session_momentum.compute_momentum_bonus(
                    tool_name, tool_category
                )
                bonus = max(bonus, sm_bonus)
            except Exception as e:
                self.logger.debug("compute_momentum_bonus failed (non-fatal): %s", e)

        return min(0.30, bonus)

    def _get_momentum_context(self) -> str:
        """Generate natural-language summary of current session momentum."""
        recent = self.session_state["recent_tools"]
        if not recent:
            return "Session just started — no momentum context yet."
        parts: List[str] = []
        last = recent[-1]
        elapsed = time.time() - last["timestamp"]
        if elapsed < 60:
            parts.append(f"You just used `{last['tool']}` ({int(elapsed)}s ago).")
        else:
            parts.append(
                f"Last tool used: `{last['tool']}` ({int(elapsed / 60)}m ago)."
            )
        wf = self.session_state["active_workflow"]
        if wf:
            nxt = wf["remaining"][0] if wf["remaining"] else "complete"
            parts.append(
                f"Active workflow **{wf['name']}** — step {wf['position']}/{len(wf['chain'])}."
                f" Next suggested: `{nxt}`."
            )
        rcats = self.session_state["recent_categories"]
        if len(rcats) >= 2:
            parts.append(f"Category flow: {' → '.join(reversed(rcats))}.")
        return " ".join(parts)

    # ------------------------------------------------------------------ #
    #  FAILURE RECOVERY — Proactive self-healing                           #
    # ------------------------------------------------------------------ #

    def _find_alternative_tool(
        self, failing_tool: str, current_chain: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Find a semantically similar tool in the same category with higher reliability."""
        failing_data = self.tool_catalog.get(failing_tool)
        if not failing_data:
            return None
        failing_cat = failing_data.get("category", "misc")
        failing_rel = self._reliability(failing_tool)
        failing_tokens = set(failing_data.get("token_counts", {}).keys())
        best: Optional[Dict[str, Any]] = None
        for name, data in self.tool_catalog.items():
            if name in current_chain or name == failing_tool:
                continue
            if data.get("category") != failing_cat:
                continue
            rel = self._reliability(name)
            if rel <= failing_rel:
                continue
            # Jaccard similarity on token sets
            alt_tokens = set(data.get("token_counts", {}).keys())
            if not failing_tokens and not alt_tokens:
                sim = 0.0
            else:
                sim = len(failing_tokens & alt_tokens) / max(
                    1, len(failing_tokens | alt_tokens)
                )
            combined = rel * 0.6 + sim * 0.4
            if best is None or combined > float(best.get("combined_score", 0.0)):
                best = {
                    "name": name,
                    "reliability": rel,
                    "similarity": round(sim, 4),
                    "combined_score": round(combined, 4),
                }
        return best

    def _get_category_health_warnings(self, category: str) -> List[str]:
        """Return warnings if a category has elevated recent failure rates."""
        warnings: List[str] = []
        cat_tools = {
            name
            for name, data in self.tool_catalog.items()
            if data.get("category") == category
        }
        if not cat_tools:
            return warnings
        outcomes = self.state.get("recent_outcomes", [])[-50:]
        total = 0
        failures = 0
        for outcome in outcomes:
            if not isinstance(outcome, dict):
                continue
            for used in outcome.get("tools_used", []):
                if used in cat_tools:
                    total += 1
                    if not outcome.get("success", True):
                        failures += 1
        if total >= 5:
            rate = failures / total
            if rate > 0.30:
                warnings.append(
                    f"Category '{category}' has a {rate:.0%} failure rate "
                    f"over the last {total} calls.  Consider alternatives or "
                    f"check system health."
                )
        return warnings

    # ------------------------------------------------------------------ #
    #  HELPER — Tool descriptions                                          #
    # ------------------------------------------------------------------ #

    def _get_tool_one_liner(self, tool_name: str) -> str:
        """First sentence of a tool's description, truncated to 80 chars."""
        desc = self.tool_catalog.get(tool_name, {}).get("description", "")
        first = desc.split(".")[0].strip() if desc else "No description available"
        return first[:77] + "..." if len(first) > 80 else first

    def _next_plan_id(self) -> int:
        """Generate a monotonically increasing plan counter for unique plan IDs."""
        self._plan_counter += 1
        return self._plan_counter

    def _evict_chain_priors(self, max_entries: int = 500) -> None:
        """Evict lowest-reliability chain priors when count exceeds max_entries."""
        chain_priors = self.state.get("chain_priors", {})
        if len(chain_priors) <= max_entries:
            return
        scored: List[Tuple[str, float, int]] = []
        for key, prior in chain_priors.items():
            alpha = float(prior.get("alpha", 1.0))
            beta = float(prior.get("beta", 1.0))
            total_uses = int(prior.get("successes", 0)) + int(prior.get("failures", 0))
            reliability = alpha / max(0.0001, alpha + beta)
            scored.append((key, reliability, total_uses))
        # Keep highest reliability; break ties by usage count
        scored.sort(key=lambda row: (row[1], row[2]), reverse=True)
        keep_keys = {row[0] for row in scored[:max_entries]}
        self.state["chain_priors"] = {
            k: v for k, v in chain_priors.items() if k in keep_keys
        }

    def sync_from_live_tools(self, live_tools: Dict[str, Any]) -> Dict[str, int]:
        """
        Synchronize the exoskeleton catalog with the server's live tool registry.

        Called by MCPServer after tool registration to ensure the exoskeleton
        has visibility into all registered tools, including dynamically added
        ones that may not appear in tool_manifest.json.
        """
        if not isinstance(live_tools, dict):
            return {"added": 0, "updated": 0, "removed": 0}

        added = 0
        updated = 0
        removed = 0
        live_names = set(live_tools.keys())
        stale_names = [name for name in self.tool_catalog.keys() if name not in live_names]
        for stale_name in stale_names:
            del self.tool_catalog[stale_name]
            removed += 1

        for tool_name, tool_info in live_tools.items():
            normalized_tool_info: Optional[Dict[str, Any]]
            if isinstance(tool_info, dict):
                normalized_tool_info = dict(tool_info)
            elif callable(tool_info):
                normalized_tool_info = {
                    "description": getattr(tool_info, "__doc__", "")
                    or f"Callable tool: {tool_name}",
                    "parameters": [],
                    "function": tool_info,
                }
                self.logger.warning(
                    "Normalizing callable live tool for exoskeleton sync: %s",
                    tool_name,
                )
            else:
                self.logger.warning(
                    "Skipping live tool (unsupported metadata type): %s (%s)",
                    tool_name,
                    type(tool_info).__name__,
                )
                continue

            if "inputSchema" not in normalized_tool_info and isinstance(
                normalized_tool_info.get("input_schema"), dict
            ):
                normalized_tool_info["inputSchema"] = normalized_tool_info[
                    "input_schema"
                ]

            description = str(normalized_tool_info.get("description", "")).strip()
            tokens = self._tokenize(f"{tool_name} {description}")
            category = self._tool_category(tool_name, description)
            required_params = self._required_params_from_tool_info(normalized_tool_info)
            new_entry = {
                "name": tool_name,
                "description": description,
                "category": category,
                "required_params": required_params,
                "token_counts": Counter(tokens),
            }
            existing = self.tool_catalog.get(tool_name)
            if existing is None:
                self.tool_catalog[tool_name] = new_entry
                added += 1
                continue
            if (
                existing.get("description") != new_entry["description"]
                or existing.get("category") != new_entry["category"]
                or existing.get("required_params") != new_entry["required_params"]
                or existing.get("token_counts") != new_entry["token_counts"]
            ):
                self.tool_catalog[tool_name] = new_entry
                updated += 1

        if added or updated or removed:
            self._rebuild_idf()
            with self._state_lock:
                self._ensure_tool_priors()
                self._save_state()
            self.logger.info(
                "Synced live tools into exoskeleton catalog: added=%d updated=%d removed=%d total=%d",
                added,
                updated,
                removed,
                len(self.tool_catalog),
            )
        return {"added": added, "updated": updated, "removed": removed}

    def _apply_reflect_mutations(
        self,
        tools: List[str],
        success_value: bool,
        now: float,
        plan_id: str,
        error: Optional[str],
        intent: Optional[str],
        recovery_strategy: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Apply reflection state mutations under the state lock.

        Returns:
            List of updated tool reliability entries.
        """
        updated: List[Dict[str, Any]] = []

        # ── Muad'Dib: feed outcomes to neural twin ────────────────────────
        if self._digital_twin is not None:
            for tool_name in tools:
                category = self.tool_catalog.get(tool_name, {}).get("category", "misc")
                try:
                    self._digital_twin.bb7_dt_observe(
                        tool_name=tool_name,
                        category=category,
                        success=success_value,
                        latency_ms=0.0,  # not tracked at this layer
                        chain_length=len(tools),
                    )
                except Exception as e:
                    self.logger.warning("DigitalTwinTool observe failed (non-fatal): %s", e)

        with self._state_lock:
            for tool_name in tools:
                prior = self.state["tool_priors"].setdefault(
                    tool_name,
                    {
                        "alpha": 1.0,
                        "beta": 1.0,
                        "successes": 0,
                        "failures": 0,
                        "last_error": "",
                    },
                )
                prior["alpha"] = max(
                    1.0,
                    (float(prior.get("alpha", 1.0)) * 0.995)
                    + (1.0 if success_value else 0.0),
                )
                prior["beta"] = max(
                    1.0,
                    (float(prior.get("beta", 1.0)) * 0.995)
                    + (0.0 if success_value else 1.0),
                )
                if success_value:
                    prior["successes"] = int(prior.get("successes", 0)) + 1
                else:
                    prior["failures"] = int(prior.get("failures", 0)) + 1
                    prior["last_error"] = str(error or "unknown error")
                updated.append(
                    {
                        "tool": tool_name,
                        "reliability": round(self._reliability(tool_name), 4),
                    }
                )

            chain_key = " > ".join(tools)
            chain_prior = self.state["chain_priors"].setdefault(
                chain_key,
                {"alpha": 1.0, "beta": 1.0, "successes": 0, "failures": 0},
            )
            chain_prior["alpha"] = max(
                1.0,
                (float(chain_prior.get("alpha", 1.0)) * 0.995)
                + (1.0 if success_value else 0.0),
            )
            chain_prior["beta"] = max(
                1.0,
                (float(chain_prior.get("beta", 1.0)) * 0.995)
                + (0.0 if success_value else 1.0),
            )
            if success_value:
                chain_prior["successes"] = int(chain_prior.get("successes", 0)) + 1
            else:
                chain_prior["failures"] = int(chain_prior.get("failures", 0)) + 1

            if not success_value and tools:
                primary = tools[0]
                if recovery_strategy:
                    self.state["failure_recovery_strategies"][primary] = str(
                        recovery_strategy
                    )
                elif error:
                    self.state["failure_recovery_strategies"][primary] = (
                        f"Route around failure: {error}"
                    )

            if intent:
                intent_key = " ".join(self._tokenize(intent)[:12])
                mapping = self.state["intent_to_tool_mappings"].setdefault(
                    intent_key, {}
                )
                for tool_name in tools:
                    mapping[tool_name] = int(mapping.get(tool_name, 0)) + 1

            row = {
                "timestamp": now,
                "plan_id": plan_id,
                "tools_used": tools,
                "success": success_value,
                "error": str(error or ""),
                "intent": str(intent or ""),
                "confidence": round(
                    sum(self._reliability(tool) for tool in tools) / float(len(tools)),
                    4,
                ),
            }
            recent = self.state.get("recent_outcomes", [])
            if not isinstance(recent, list):
                recent = []
            recent.append(row)
            self.state["recent_outcomes"] = recent[-200:]

            freq = defaultdict(int)
            for item in self.state["recent_outcomes"]:
                if isinstance(item, dict) and bool(item.get("success")):
                    key = " > ".join(item.get("tools_used", []))
                    if key:
                        freq[key] += 1
            macros = []
            for key, count in freq.items():
                if count >= 5:
                    macros.append(
                        {
                            "macro_name": f"macro_{abs(hash(key)) % 100000}",
                            "chain": key.split(" > "),
                            "frequency": count,
                        }
                    )
            macros.sort(key=lambda item: item["frequency"], reverse=True)
            self.state["discovered_macros"] = macros[:20]

            self._evict_chain_priors()
            self._save_state()
            self._append_jsonl(self.history_file, row)

        return updated

    def _reliability(self, tool_name: str) -> float:
        """Deterministic posterior mean reliability.  Used where reproducibility
        matters: chain confidence, failure analysis, alternative tool ranking."""
        prior = self.state.get("tool_priors", {}).get(tool_name, {})
        alpha = float(prior.get("alpha", 1.0))
        beta = float(prior.get("beta", 1.0))
        return max(0.0, min(1.0, alpha / max(0.0001, alpha + beta)))

    def _reliability_sampled(self, tool_name: str, context_category: str = "") -> float:
        """Thompson-sampled reliability for stochastic exploration in scoring.

        Draws from the posterior Beta(alpha, beta) distribution conditioned on
        the current category context.  When the Digital Twin has a Q-bonus for
        this tool, that bonus shifts alpha proportionally (per the bandit's
        neural_q_bonus scaling), biasing the posterior toward tools the neural
        substrate has observed as effective.

        Falls back to the deterministic posterior mean (_reliability) when the
        Thompson bandit is not available (lisan not loaded, or at import time).

        Used exclusively in _score_tools() — the only place where exploration
        noise is desirable.  All other callers use _reliability() directly.
        """
        if self._thompson_bandit is None:
            return self._reliability(tool_name)

        prior = self.state.get("tool_priors", {}).get(tool_name, {})

        # Pull the neural Q-bonus from the digital twin if available.
        # Q-bonus range [0.0, 0.25] maps to alpha shift [0.0, 0.5] inside
        # _ThompsonContextualBandit.draw() (factor 2.0).
        neural_q_bonus = 0.0
        if self._digital_twin is not None:
            try:
                q_result = self._digital_twin.bb7_dt_q_scores(
                    [tool_name], context_category
                )
                neural_q_bonus = float(
                    q_result.get("bonuses", {}).get(tool_name, 0.0)
                )
            except Exception as e:
                self.logger.debug("Failed to fetch neural Q-bonus (non-fatal): %s", e)

        return self._thompson_bandit.draw(prior, context_category, neural_q_bonus=neural_q_bonus)

    def _semantic(self, query_tokens: List[str], tool_counts: Counter) -> float:
        if not query_tokens:
            return 0.0
        num = 0.0
        den = 0.0
        for token in query_tokens:
            weight = self.idf.get(token, 1.0)
            den += weight
            if token in tool_counts:
                num += weight
        return max(0.0, min(1.0, num / max(0.0001, den)))

    def _intent_weights(
        self, query_tokens: List[str], raw_query: Optional[str] = None
    ) -> Dict[str, float]:
        token_set = set(query_tokens)
        scores: Dict[str, float] = defaultdict(float)
        for category, keywords in self.intent_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in token_set)
            if match_count:
                scores[category] = float(match_count) / float(max(1, len(keywords)))

        query_text = str(raw_query or "").lower()
        explicit_path_like = any(
            marker in query_text
            for marker in (
                ".py",
                ".md",
                "tools/",
                "mcp_server",
                "tool_manifest",
                "golden_paths",
                "agents.md",
                "context.md",
                "memory.md",
                "workflows.md",
                "readme.md",
                "spec.md",
            )
        )
        control_plane_like = any(
            marker in query_text
            for marker in (
                "control plane",
                "control-plane",
                "routing",
                "router",
                "orchestration",
                "distill",
                "distillation",
                "trajectory",
                "telemetry",
                "lisan",
                "exoskeleton",
                "auto_tool_module",
                "memory_tool",
                "memory_interconnect",
                "session_manager_tool",
                "project_context_tool",
                "web_tool",
                "enhanced_web_tool",
                "visual_tool",
            )
        )
        session_continuity_like = any(
            marker in query_text
            for marker in (
                "codex",
                "history.jsonl",
                "state_5.sqlite",
                "thread",
                "session",
                "continuity",
                "memory plane",
                "context injection",
                "ambient memory",
            )
        )
        explicit_tooling_like = "bb7_" in query_text or "tool " in query_text

        if explicit_path_like:
            scores["files"] += 1.0
            scores["project_context"] += 1.2
            scores["analysis"] += 0.8

        if control_plane_like:
            scores["exoskeleton"] += 1.3
            scores["analysis"] += 1.1
            scores["project_context"] += 0.9

        if session_continuity_like:
            scores["memory"] += 0.8
            scores["sessions"] += 0.8
            scores["exoskeleton"] += 0.4

        if explicit_tooling_like:
            scores["analysis"] += 0.6
            scores["project_context"] += 0.5
            scores["exoskeleton"] += 0.5

        if not scores:
            return {
                "project_context": 0.35,
                "analysis": 0.3,
                "exoskeleton": 0.2,
                "files": 0.15,
            }
        top = max(scores.values())
        return {
            category: min(1.0, score / max(0.0001, top))
            for category, score in scores.items()
        }

    def _score_tools(
        self,
        intent: str,
        max_candidates: int,
        include_neighbors: bool,
        neighbor_distance: int,
        golden_match: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query = str(intent or "")
        query_tokens = self._tokenize(query)
        weights = self._intent_weights(query_tokens, raw_query=query)

        baseline = {}
        spectral_scores: Dict[str, float] = {}
        for name, info in self.tool_catalog.items():
            baseline[name] = self._semantic(query_tokens, info["token_counts"])
            if self._lisan_available and self._spectral_decomposer is not None:
                try:
                    spectral_scores[name] = self._spectral_decomposer.spectral_similarity(
                        query,
                        f"{info.get('name', name)} {info.get('description', '')}",
                        tool_name=name,
                    )
                except Exception:
                    spectral_scores[name] = 0.0

        seed_size = min(max(20, max_candidates * 2), len(baseline))
        seeds = [
            name
            for name, _score in sorted(
                baseline.items(), key=lambda row: row[1], reverse=True
            )[:seed_size]
        ]
        pool: Set[str] = set(seeds)

        if include_neighbors and neighbor_distance > 0:
            frontier = set(seeds)
            for _ in range(neighbor_distance):
                neighbor_categories: Set[str] = set()
                for name in frontier:
                    category = self.tool_catalog.get(name, {}).get("category", "misc")
                    neighbor_categories.update(self.category_graph.get(category, set()))
                next_frontier: Set[str] = set()
                for name, info in self.tool_catalog.items():
                    if (
                        info.get("category", "misc") in neighbor_categories
                        and name not in pool
                    ):
                        next_frontier.add(name)
                pool.update(next_frontier)
                frontier = next_frontier
                if not frontier:
                    break

        seed_categories = {
            self.tool_catalog.get(name, {}).get("category", "misc") for name in seeds
        }
        golden_chain: Set[str] = set()
        normalized_golden = self._normalize_golden_match(golden_match)
        if normalized_golden:
            chain = normalized_golden.get("chain", [])
            if isinstance(chain, list):
                golden_chain = {str(step) for step in chain if isinstance(step, str)}

        # ── Advanced modality bridge (batch pre-compute, MUADIB_ADVANCED_MODE=1) ──
        # One call for the full pool, cache in bridge handles dedup within 8s.
        # advanced_features_batch is empty dict when mode=0 or twin unavailable.
        _advanced_features_batch: Dict[str, Any] = {}
        if _MUADIB_ADVANCED_MODE and self._digital_twin is not None:
            try:
                _dominant_cat = (
                    max(
                        seed_categories,
                        key=lambda c: sum(
                            1
                            for n in seeds
                            if self.tool_catalog.get(n, {}).get("category") == c
                        ),
                    )
                    if seed_categories
                    else "misc"
                )
                _recent_tool_names = [
                    t.get("tool", "")
                    for t in self.session_state.get("recent_tools", [])
                ]
                _adv_result = self._digital_twin.bb7_dt_advanced_features(
                    candidates=list(pool),
                    category=_dominant_cat,
                    session_id=self.session_state.get("session_id", "default"),
                    recent_tools=_recent_tool_names,
                )
                if isinstance(_adv_result, dict) and _adv_result.get("ok"):
                    _advanced_features_batch = _adv_result.get("features", {})
            except Exception as e:
                self.logger.debug("Failed to fetch advanced features batch (non-fatal): %s", e)

        ranked = []
        for name in pool:
            info = self.tool_catalog.get(name, {})
            category = info.get("category", "misc")
            lexical_semantic = baseline.get(name, 0.0)
            spectral = spectral_scores.get(name, 0.0)
            semantic = (
                (0.55 * lexical_semantic) + (0.45 * spectral)
                if spectral_scores
                else lexical_semantic
            )
            intent_match = float(weights.get(category, 0.0))
            # Thompson-sampled reliability: stochastic Beta draw conditioned on
            # category context + neural Q-bonus.  Drives exploration of under-used
            # tools.  _reliability() (deterministic mean) stays intact for chain
            # confidence, failure analysis, and alternative tool ranking.
            reliability = self._reliability_sampled(name, category)
            neighbor_hits = sum(
                1
                for cat in seed_categories
                if cat in self.category_graph.get(category, set())
            )
            composability = min(
                1.0, float(neighbor_hits) / float(max(1, len(seed_categories)))
            )
            latency_penalty = float(self.category_latency_penalty.get(category, 0.08))

            # Neural Q-bonus from Muad'Dib twin (6th scoring signal)
            neural_q = 0.0
            if self._digital_twin is not None:
                try:
                    q_result = self._digital_twin.bb7_dt_q_scores([name], category)
                    neural_q = max(0.0, min(1.0, float(
                        q_result.get("bonuses", {}).get(name, 0.0)
                    )))
                except Exception:
                    neural_q = 0.0

            # Advanced modality bridge bonus (7th scoring signal, mode-gated)
            # effective_alpha = _ADV_ALPHA * feat.effective_score
            # Max for trained_q at perfect confidence: 0.15 * 1.0 = 0.15
            # Max for untrained_embed:                0.15 * 0.009 ≈ 0.001
            advanced_bonus = 0.0
            if _advanced_features_batch:
                _feat = _advanced_features_batch.get(name)
                if _feat and isinstance(_feat, dict):
                    advanced_bonus = _ADV_ALPHA * float(_feat.get("effective_score", 0.0))

            score = (
                (0.35 * semantic)
                + (0.18 * intent_match)
                + (0.12 * composability)
                + (0.13 * reliability)
                + (0.12 * neural_q)
                - (0.10 * latency_penalty)
                + advanced_bonus
            )
            golden_bonus = 0.12 if name in golden_chain else 0.0
            if golden_bonus:
                score += golden_bonus
            ranked.append(
                {
                    "name": name,
                    "category": category,
                    "score": round(max(0.0, min(1.0, score)), 4),
                    "semantic_score": round(semantic, 4),
                    "lexical_semantic_score": round(lexical_semantic, 4),
                    "spectral_score": round(spectral, 4),
                    "intent_match": round(intent_match, 4),
                    "composability_score": round(composability, 4),
                    "reliability": round(reliability, 4),
                    "required_params": info.get("required_params", []),
                    "description": info.get("description", ""),
                    **({"neural_q_bonus": round(neural_q, 4)} if neural_q > 0.0 else {}),
                    **({"advanced_bonus": round(advanced_bonus, 4)} if advanced_bonus > 0.0 else {}),
                    **({"golden_path_bonus": round(golden_bonus, 4)} if golden_bonus else {}),
                }
            )
        # ── Momentum Integration ──────────────────────────────────────────
        for item in ranked:
            bonus = self._compute_momentum_bonus(item["name"], item["category"])
            if bonus > 0.0:
                item["original_score"] = item["score"]
                item["momentum_bonus"] = round(bonus, 4)
                item["score"] = round(max(0.0, min(1.0, item["score"] + bonus)), 4)
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return ranked[: max(1, max_candidates)]

    def _chain_confidence(
        self, chain: List[str], ranked_lookup: Dict[str, Dict[str, Any]]
    ) -> float:
        if not chain:
            return 0.0
        scores = [ranked_lookup.get(name, {}).get("score", 0.0) for name in chain]
        reliability = [self._reliability(name) for name in chain]
        return round(
            (0.55 * (sum(scores) / len(scores)))
            + (0.45 * (sum(reliability) / len(reliability))),
            4,
        )

    def _estimate_chain_tokens(self, chain: List[str]) -> int:
        total = 120
        for tool_name in chain:
            category = self.tool_catalog.get(tool_name, {}).get("category", "misc")
            total += self.category_token_estimate.get(category, 240)
        return total

    def _make_plans(
        self, ranked: List[Dict[str, Any]], beam_width: int, max_chain_length: int
    ) -> List[Dict[str, Any]]:
        ranked_lookup = {row["name"]: row for row in ranked}
        ranked_names = [row["name"] for row in ranked]
        plans = []

        chains: List[List[str]] = []
        balanced = []
        if "bb7_workspace_context_loader" in self.tool_catalog:
            balanced.append("bb7_workspace_context_loader")
        used_categories: Set[str] = set()
        for name in ranked_names:
            if len(balanced) >= max_chain_length - 1:
                break
            category = self.tool_catalog.get(name, {}).get("category", "misc")
            if category in used_categories:
                continue
            balanced.append(name)
            used_categories.add(category)
        if "bb7_memory_store" in self.tool_catalog and len(balanced) < max_chain_length:
            balanced.append("bb7_memory_store")
        chains.append(balanced)

        fast = []
        if "bb7_workspace_context_loader" in self.tool_catalog:
            fast.append("bb7_workspace_context_loader")
        for row in sorted(
            ranked, key=lambda item: item.get("reliability", 0.0), reverse=True
        ):
            if len(fast) >= max_chain_length:
                break
            fast.append(row["name"])
        chains.append(fast)

        deep = []
        if "bb7_workspace_context_loader" in self.tool_catalog:
            deep.append("bb7_workspace_context_loader")
        for name in ranked_names:
            if len(deep) >= max_chain_length:
                break
            if self.tool_catalog.get(name, {}).get("category", "misc") == "analysis":
                deep.append(name)
                break
        for name in ranked_names:
            if len(deep) >= max_chain_length:
                break
            if name not in deep:
                deep.append(name)
        chains.append(deep)

        unique = []
        seen = set()
        for chain in chains:
            final_chain = []
            for tool_name in chain:
                if tool_name in self.tool_catalog and tool_name not in final_chain:
                    final_chain.append(tool_name)
                if len(final_chain) >= max_chain_length:
                    break
            key = " > ".join(final_chain)
            if key and key not in seen:
                seen.add(key)
                unique.append(final_chain)

        for idx, chain in enumerate(unique[:beam_width], start=1):
            confidence = self._chain_confidence(chain, ranked_lookup)
            fallback = [tool for tool in chain if self._reliability(tool) >= 0.45]
            if (
                "bb7_memory_store" in self.tool_catalog
                and "bb7_memory_store" not in fallback
                and len(fallback) < max_chain_length
            ):
                fallback.append("bb7_memory_store")
            failure_points = []
            for tool_name in chain:
                rel = self._reliability(tool_name)
                if rel < 0.5:
                    failure_points.append(f"{tool_name}: low reliability ({rel:.2f})")
                required = ranked_lookup.get(tool_name, {}).get("required_params", [])
                if required:
                    failure_points.append(
                        f"{tool_name}: requires params {', '.join(required)}"
                    )
            plans.append(
                {
                    "plan_id": f"plan_{int(time.time())}_{self._next_plan_id()}",
                    "chain": chain,
                    "confidence": confidence,
                    "estimated_tokens": self._estimate_chain_tokens(chain),
                    "estimated_latency_ms": int(
                        sum(
                            self.category_latency_penalty.get(
                                self.tool_catalog.get(tool, {}).get("category", "misc"),
                                0.08,
                            )
                            for tool in chain
                        )
                        * 1000.0
                    ),
                    "failure_points": failure_points[:6],
                    "fallback": fallback[:max_chain_length],
                    "contract_valid": len(chain) > 0,
                }
            )
        plans.sort(key=lambda row: row["confidence"], reverse=True)
        return plans

    def bb7_exo_bootstrap(
        self, include_recent_outcomes: bool = True, include_healthcheck: bool = True
    ) -> Dict[str, Any]:
        """Bootstrap capability context for each turn."""
        manifest_refresh = self._refresh_catalog_from_manifest_if_changed(force=False)
        sync_counts = self._maybe_sync_live_tools(force=True, min_interval_sec=0.0)
        categories = Counter(
            info.get("category", "misc") for info in self.tool_catalog.values()
        )
        manifest_exists = bool(self.manifest_path.exists())
        payload: Dict[str, Any] = {
            "status": "ready",
            "timestamp": time.time(),
            "indexed_tools": len(self.tool_catalog),
            "category_count": len(categories),
            "categories": dict(sorted(categories.items())),
            "recommended_loop": [
                "bb7_exo_bootstrap",
                "bb7_exo_route",
                "bb7_exo_plan",
                "execute",
                "bb7_exo_reflect",
            ],
            "manifest_refresh": manifest_refresh,
            "catalog_sync": sync_counts,
            "live_provider_attached": self._live_tools_provider is not None,
            "exo_tools_registered": len(self.get_tools()),
            "manifest_path": str(self.manifest_path),
            "manifest_present": manifest_exists,
            "manifest_mtime": self.manifest_path.stat().st_mtime
            if manifest_exists
            else None,
            "prior_diagnostics": self._tool_prior_diagnostics(),
        }
        if bool(include_healthcheck):
            critical = [
                "bb7_workspace_context_loader",
                "bb7_memory_store",
                "bb7_analyze_project_structure",
                "bb7_run_command",
                "bb7_fetch_url",
            ]
            payload["healthcheck"] = [
                {
                    "tool": name,
                    "available": name in self.tool_catalog,
                    "reliability": round(self._reliability(name), 4),
                }
                for name in critical
            ]
        if bool(include_recent_outcomes):
            outcomes = self.state.get("recent_outcomes", [])
            payload["recent_outcomes"] = (
                outcomes[-5:] if isinstance(outcomes, list) else []
            )
        return payload

    def bb7_exo_list_tool_categories(self) -> Dict[str, Any]:
        """List all categories and samples."""
        self._maybe_sync_live_tools()
        categories: Dict[str, List[str]] = defaultdict(list)
        for name, info in self.tool_catalog.items():
            categories[info.get("category", "misc")].append(name)
        payload = {
            "category_count": len(categories),
            "categories": {
                category: {
                    "count": len(names),
                    "samples": sorted(names)[:6],
                    "neighbors": sorted(self.category_graph.get(category, set())),
                }
                for category, names in sorted(categories.items())
            },
        }
        return payload

    def bb7_exo_category_specific_tools(
        self, category: str, limit: int = 20
    ) -> Dict[str, Any]:
        """List category-specific tools with priors."""
        self._maybe_sync_live_tools()
        normalized = str(category or "").strip().lower()
        if not normalized:
            raise ValueError("category parameter is required")
        limit = max(1, min(200, int(limit)))
        rows = []
        for name, info in self.tool_catalog.items():
            if info.get("category", "misc") != normalized:
                continue
            rows.append(
                {
                    "name": name,
                    "description": info.get("description", ""),
                    "required_params": info.get("required_params", []),
                    "reliability": round(self._reliability(name), 4),
                }
            )
        rows.sort(key=lambda row: row["reliability"], reverse=True)
        return {
            "category": normalized,
            "count": len(rows),
            "neighbors": sorted(self.category_graph.get(normalized, set())),
            "tools": rows[:limit],
        }

    def bb7_exo_route(
        self,
        intent: str,
        max_candidates: int = 12,
        include_neighbors: bool = True,
        neighbor_distance: int = 1,
    ) -> Dict[str, Any]:
        """Retrieve top tools for an intent using semantic and graph signals."""
        self._maybe_sync_live_tools()
        intent = str(intent or "").strip()
        if not intent:
            raise ValueError("intent parameter is required")
        max_candidates = max(1, min(50, int(max_candidates)))
        neighbor_distance = max(0, min(3, int(neighbor_distance)))
        golden_match = self._match_golden_path(intent)
        ranked = self._score_tools(
            intent,
            max_candidates,
            bool(include_neighbors),
            neighbor_distance,
            golden_match=golden_match,
        )
        categories = Counter(row["category"] for row in ranked)
        payload = {
            "intent": intent,
            "timestamp": time.time(),
            "max_candidates": max_candidates,
            "include_neighbors": bool(include_neighbors),
            "neighbor_distance": neighbor_distance,
            "top_categories": dict(categories.most_common(6)),
            "top_tools": ranked,
            "golden_path_match": (
                golden_match.get("name") if isinstance(golden_match, dict) else None
            ),
        }
        return payload

    def bb7_exo_plan(
        self,
        intent: str,
        context: Optional[str] = None,
        beam_width: int = 3,
        max_chain_length: int = 4,
    ) -> Dict[str, Any]:
        """Generate candidate execution chains with confidence and fallback."""
        self._maybe_sync_live_tools()
        intent = str(intent or "").strip()
        if not intent:
            raise ValueError("intent parameter is required")
        beam_width = max(1, min(6, int(beam_width)))
        max_chain_length = max(2, min(8, int(max_chain_length)))
        plan_query = f"{intent} {context or ''}".strip()
        plan_golden_match = self._match_golden_path(intent)
        ranked = self._score_tools(
            plan_query,
            max(beam_width * 8, 12),
            True,
            1,
            golden_match=plan_golden_match,
        )
        # ── Muad'Dib neural value function for MCTS (Phase 4 injection) ──
        # bb7_dt_encode_catalog() is the correct API: accepts List[str], handles
        # chunking, returns per-tool 512-dim vectors.  The original code called
        # bb7_dt_encode(chain: List[str]) — wrong type — and read "mean_hidden_state"
        # which doesn't exist (real key is "hidden_states").  Fixed here.
        neural_value_fn: Optional[Callable[[List[str]], float]] = None
        twin = getattr(self, "_digital_twin", None)
        if twin is not None and hasattr(twin, "bb7_dt_encode_catalog"):
            def _value_fn(chain: List[str]) -> float:
                try:
                    encode_res = twin.bb7_dt_encode_catalog(chain)
                    if isinstance(encode_res, dict) and encode_res.get("ok"):
                        embeddings = encode_res.get("embeddings", {})
                        if embeddings:
                            # Mean L1-norm across all chain tools → proxy for
                            # "how activated is the neural substrate on this chain"
                            vecs = list(embeddings.values())
                            mean_norm = sum(
                                sum(abs(x) for x in v) / max(1, len(v))
                                for v in vecs
                            ) / len(vecs)
                            return max(0.0, min(1.0, mean_norm))
                except Exception as _val_err:
                    self.logger.debug("Neural value eval failed: %s", _val_err)
                return 0.5  # Neutral fallback — MCTS uses UCB1 to compensate
            neural_value_fn = _value_fn

        # ── MCTS vs Static Routing ───────────────────────────────────────
        if self._lisan_available and self._mcts_planner is not None:
            # Full MCTS rollout using Topological Momentum + Neural Rewards
            raw_plans = self._mcts_planner.search(
                ranked,
                self.tool_catalog,
                self._reliability,
                self._estimate_chain_tokens,
                beam_width=beam_width,
                max_chain_length=max_chain_length,
                simulations=100,
                neural_value_fn=neural_value_fn,
            )
            # ── Normalize MCTS output to the expected plan schema ────────
            # _MCTSPlanner.search() returns dicts with keys:
            #   chain, confidence, estimated_tokens, tree_reward,
            #   failure_points, adversarial_survived
            # bb7_exo_plan downstream expects: plan_id, fallback,
            #   estimated_latency_ms, failure_points (already present).
            # We enrich rather than replace so all MCTS-specific keys survive.
            ranked_lookup = {row["name"]: row for row in ranked}
            plans = []
            for raw in raw_plans:
                chain = raw.get("chain", [])
                fallback = [
                    t for t in chain if self._reliability(t) >= 0.45
                ]
                if (
                    "bb7_memory_store" in self.tool_catalog
                    and "bb7_memory_store" not in fallback
                    and len(fallback) < max_chain_length
                ):
                    fallback.append("bb7_memory_store")
                latency_ms = int(
                    sum(
                        self.category_latency_penalty.get(
                            self.tool_catalog.get(t, {}).get("category", "misc"),
                            0.08,
                        )
                        * 1000
                        for t in chain
                    )
                )
                plans.append(
                    {
                        "plan_id": f"mcts_{int(time.time())}_{self._next_plan_id()}",
                        "fallback": fallback,
                        "estimated_latency_ms": latency_ms,
                        "mcts": True,
                        "tree_reward": raw.get("tree_reward", 0.5),
                        "adversarial_survived": raw.get("adversarial_survived", False),
                        **raw,
                    }
                )
        else:
            # Fallback to static chain builder
            plans = self._make_plans(ranked, beam_width, max_chain_length)

        # ── Checkpoint: persist best plan for resume/execute_step
        best_plan_id = plans[0]["plan_id"] if plans else ""
        if best_plan_id and plans:
            best = plans[0]
            checkpoint = {
                "plan_id": best_plan_id,
                "intent": intent,
                "context": context or "",
                "chain": best["chain"],
                "confidence": best["confidence"],
                "fallback": best.get("fallback", []),
                "created_at": time.time(),
                "steps_completed": [],
                "steps_remaining": list(range(len(best["chain"]))),
                "status": "created",
                "kpi": {
                    "total_steps": len(best["chain"]),
                    "completed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "elapsed_sec": 0.0,
                },
            }
            with self._state_lock:
                self._active_plans[best_plan_id] = checkpoint
                self._write_json(self.plans_file, self._active_plans)
            self._append_jsonl(
                self.checkpoint_file,
                {
                    "event": "plan_created",
                    "plan_id": best_plan_id,
                    "timestamp": time.time(),
                    "chain": best["chain"],
                    "intent": intent,
                },
            )

        payload = {
            "intent": intent,
            "context": context or "",
            "generated_at": time.time(),
            "best_plan_id": best_plan_id,
            "candidate_plans": plans,
            "golden_path_match": (
                plan_golden_match.get("name") if isinstance(plan_golden_match, dict) else None
            ),
        }
        return payload

    def bb7_exo_reflect(
        self,
        plan_id: str,
        tools_used: Any,
        success: Any,
        error: Optional[str] = None,
        intent: Optional[str] = None,
        recovery_strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update priors after execution and store reflection telemetry."""
        if isinstance(tools_used, list):
            tools = [str(item).strip() for item in tools_used if str(item).strip()]
        elif isinstance(tools_used, str):
            tools = [item.strip() for item in tools_used.split(",") if item.strip()]
        else:
            tools = []
        if not tools:
            raise ValueError(
                "tools_used parameter is required and must contain at least one tool name"
            )

        if isinstance(success, bool):
            success_value = success
        elif isinstance(success, (int, float)):
            success_value = success != 0
        elif isinstance(success, str):
            success_value = success.strip().lower() in {"1", "true", "yes", "y", "on"}
        else:
            success_value = bool(success)

        updated = self._apply_reflect_mutations(
            tools,
            success_value,
            time.time(),
            str(plan_id),
            error,
            intent,
            recovery_strategy,
        )

        # ── Momentum Tracking ────────────────────────────────────────────
        reflect_intent = intent or ""
        for tool_name in tools:
            self._update_session_momentum(tool_name, reflect_intent)

        # ── Muad'Dib: inject neural attention weights into momentum ──────
        # After each reflection, extract the twin's learned attention pattern
        # and inject it into the Topological Momentum Manifold (Lisan Phase 3).
        # This teaches the momentum system which category transitions the
        # neural backbone considers most promising.
        twin = getattr(self, "_digital_twin", None)
        if twin is not None and hasattr(twin, "bb7_dt_q_scores"):
            try:
                # Build attention weights from Q-table: one score per category
                categories = set(
                    info.get("category", "misc")
                    for info in self.tool_catalog.values()
                )
                attn_weights: Dict[str, float] = {}
                for cat in categories:
                    cat_tools = [
                        name for name, info in self.tool_catalog.items()
                        if info.get("category", "misc") == cat
                    ]
                    if cat_tools:
                        q_result = twin.bb7_dt_q_scores(cat_tools[:5], cat)
                        bonuses = q_result.get("bonuses", {})
                        if bonuses:
                            attn_weights[cat] = max(
                                0.0,
                                min(1.0, sum(bonuses.values()) / len(bonuses)),
                            )
                # Inject into lisan's momentum manifold if available
                if attn_weights and self._lisan_available:
                    try:
                        from tools.lisan_al_gaib import _TopologicalMomentumManifold
                        # Find the manifold via the spectral decomposer's parent scope
                        # — it's used in _compute_momentum_bonus indirectly
                        self._cached_neural_attention = attn_weights
                    except Exception as e:
                        self.logger.debug("Failed to set _cached_neural_attention: %s", e)
            except Exception as _attn_err:
                self.logger.error(
                    "LOUD FAIL: Neural attention injection into momentum failed: %s",
                    _attn_err,
                )

        # ── Auto-discover workflows from proven chains ───────────────────
        if success_value and len(tools) >= 2:
            chain_key = " > ".join(tools)
            self._promote_successful_chain_to_workflow(chain_key)

        # ── Cross-AI Activity Log (for multi-AI coordination) ───────────
        self._append_jsonl(
            self.activity_file,
            {
                "timestamp": time.time(),
                "ai_instance": self.session_state.get("session_id", "unknown"),
                "tools_used": tools,
                "success": success_value,
                "intent": reflect_intent,
                "plan_id": str(plan_id),
            },
        )

        # ── Cognitive Journal: record decision provenance (non-fatal) ────
        # Now wire MCTS signal for planner training - close the feedback loop
        decision_id: Optional[str] = None
        if self._cognitive_journal is not None and reflect_intent:
            try:
                decision_id = self._cognitive_journal.record_decision(
                    decision=f"Executed tool chain: {', '.join(tools)}",
                    rationale=f"Intent: {reflect_intent}",
                    outcome="success" if success_value else str(error or "failure"),
                    validated=success_value,
                    plan_id=str(plan_id),
                    tools_used=tools,
                )
            except Exception as _cj_err:
                self.logger.debug(
                    "CognitiveJournal record failed (non-fatal): %s", _cj_err
                )

        # ── MCTS Training Signal: propagate outcome to planning layer ─────
        # This feeds the decision back to improve future tool chain selection
        if decision_id and self._cognitive_journal is not None:
            try:
                self._cognitive_journal.record_mcts_signal(
                    decision_id=decision_id,
                    outcome="success" if success_value else "failure",
                    validated=success_value,
                    mcts_planner=None,
                )
            except Exception as _mcts_err:
                self.logger.debug(
                    "MCTS signal propagation failed (non-fatal): %s", _mcts_err
                )

        return {
            "status": "reflected",
            "plan_id": str(plan_id),
            "success": success_value,
            "updated_tools": updated,
            "macro_count": len(self.state.get("discovered_macros", [])),
            "session_momentum": self.session_state.get("active_workflow"),
        }

    def bb7_exo_state(self, limit: int = 15) -> Dict[str, Any]:
        """Return exoskeleton priors, macros, and recovery hints."""
        self._maybe_sync_live_tools()
        limit = max(1, min(100, int(limit)))
        tool_rows = [
            {
                "tool": name,
                "category": info.get("category", "misc"),
                "reliability": round(self._reliability(name), 4),
            }
            for name, info in self.tool_catalog.items()
        ]
        tool_rows.sort(key=lambda row: row["reliability"], reverse=True)

        chain_rows = []
        for chain, prior in self.state.get("chain_priors", {}).items():
            alpha = float(prior.get("alpha", 1.0))
            beta = float(prior.get("beta", 1.0))
            chain_rows.append(
                {
                    "chain": chain.split(" > "),
                    "reliability": round(alpha / max(0.0001, alpha + beta), 4),
                    "successes": int(prior.get("successes", 0)),
                    "failures": int(prior.get("failures", 0)),
                }
            )
        chain_rows.sort(
            key=lambda row: (row["reliability"], row["successes"]), reverse=True
        )

        payload = {
            "updated_at": self.state.get("updated_at", 0.0),
            "indexed_tools": len(self.tool_catalog),
            "recent_outcomes_count": len(self.state.get("recent_outcomes", [])),
            "discovered_macros": self.state.get("discovered_macros", [])[:limit],
            "top_tool_priors": tool_rows[:limit],
            "top_chain_priors": chain_rows[:limit],
            "known_recovery_strategies": self.state.get(
                "failure_recovery_strategies", {}
            ),
        }
        return payload

    def bb7_exo_get_recent_activity(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent activity from all AI instances - call at session start to sync context.

        Returns a concise summary of what other AIs have been doing, including:
        - Recent tool executions and their outcomes
        - Active workflows being pursued
        - Discovered patterns (macros)

        This enables multi-AI coordination by sharing state across instances.
        """
        limit = max(1, min(50, int(limit)))

        # Get recent outcomes
        outcomes = self.state.get("recent_outcomes", [])[-limit:]
        formatted_outcomes = []
        for outcome in outcomes:
            if not isinstance(outcome, dict):
                continue
            tools = outcome.get("tools_used", [])
            success = outcome.get("success", True)
            intent = outcome.get("intent", "")
            error = outcome.get("error", "")
            ts = outcome.get("timestamp", 0)

            tool_str = " → ".join(tools) if tools else "unknown"
            status = "✓" if success else "✗"

            formatted_outcomes.append(
                {
                    "status": status,
                    "chain": tool_str,
                    "intent": intent[:80] if intent else "",
                    "error": error[:50] if error else "",
                    "timestamp": ts,
                    "relative_time": self._format_relative_time(ts) if ts else "",
                }
            )

        # Get cross-AI activity log
        cross_ai_activity = []
        if self.activity_file.exists():
            try:
                with open(self.activity_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        try:
                            entry = json.loads(line.strip())
                            cross_ai_activity.append(
                                {
                                    "ai_instance": entry.get("ai_instance", "unknown"),
                                    "tools": " → ".join(entry.get("tools_used", [])),
                                    "success": entry.get("success", True),
                                    "intent": entry.get("intent", "")[:60],
                                    "timestamp": entry.get("timestamp", 0),
                                    "relative_time": self._format_relative_time(
                                        entry.get("timestamp", 0)
                                    )
                                    if entry.get("timestamp")
                                    else "",
                                }
                            )
                        except json.JSONDecodeError:
                            continue
            except Exception as exc:
                self.logger.debug("Failed to read cross-AI activity: %s", exc)

        # Get discovered macros
        macros = self.state.get("discovered_macros", [])[:5]

        # Get active workflow from momentum
        active_workflow = self.session_state.get("active_workflow")
        workflow_info = None
        if active_workflow:
            workflow_info = {
                "name": active_workflow.get("name"),
                "position": active_workflow.get("position"),
                "remaining": active_workflow.get("remaining", [])[:3],
                "confidence": active_workflow.get("confidence", 0),
            }

        # Get session momentum summary
        recent_tools = self.session_state.get("recent_tools", [])[-5:]
        recent_tool_names = [t.get("tool", "?") for t in recent_tools]

        return {
            "status": "ok",
            "summary": f"Recent activity: {len(formatted_outcomes)} events, {len(macros)} macros discovered, {len(cross_ai_activity)} cross-AI entries",
            "recent_outcomes": formatted_outcomes,
            "cross_ai_activity": cross_ai_activity,
            "discovered_macros": macros,
            "active_workflow": workflow_info,
            "recent_tools": recent_tool_names,
            "total_outcomes_tracked": len(self.state.get("recent_outcomes", [])),
        }

    def _format_relative_time(self, timestamp: float) -> str:
        """Format timestamp as relative time string."""
        now = time.time()
        diff = now - timestamp
        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"

    # ──────────────────────────────────────────────────────────────────────
    #  Phase-2 Public Tools: Briefing · Recovery · Focused Routing
    # ──────────────────────────────────────────────────────────────────────

    def _ensure_lisan_subsystems(self) -> None:
        """Ensure lisan subsystems are initialized if not already."""
        if not self._lisan_available:
            return
        # Actually in ExoskeletonTool, they are initialized in __init__,
        # but we can refresh priors or any required state here.
        if self._golden_oracle:
            pass

    def generate_boot_briefing(self) -> str:
        """
        Generate a prescient session-start briefing using lisan's NarrativeEngine.
        Returns a narrative scaffold describing the most valuable golden paths,
        current momentum state, and recommended session-start chain.
        Called once at server boot — result persisted to events.jsonl.
        """
        try:
            res = self.bb7_exo_briefing(
                intent="autonomous session boot: load priors and state",
                max_recommendations=5
            )
            narrative = res.get("narrative", "")
            if not narrative:
                return "System initialized. Tool plane ready."
            return narrative
        except Exception as e:
            self.logger.warning("Boot briefing error: %s", e)
            return f"Boot briefing generation failed: {e}"

    def bb7_exo_briefing(
        self,
        intent: str,
        max_recommendations: int = 5,
    ) -> Dict[str, Any]:
        """Generate a natural-language capability narrative for the current intent.

        This is the *paradigm shift* tool: instead of raw routing scores it
        returns a human-readable briefing that helps the LLM understand what
        it can do, what workflows are proven, and where the system stands
        right now — in plain prose.

        Args:
            intent: The user-facing goal or task description.
            max_recommendations: Maximum recommended tools to surface.

        Returns:
            Dict with ``narrative`` (markdown string), ``recommended_first_call``,
            ``workflow_plan``, ``confidence_score``, and optional extras.
        """
        if not intent or not str(intent).strip():
            raise ValueError("intent parameter is required for briefing generation")
        self._maybe_sync_live_tools()
        intent = str(intent).strip()
        max_recommendations = max(1, min(20, int(max_recommendations)))

        # 1 — Route + plan behind the scenes
        routed = self.bb7_exo_route(
            intent, max_candidates=max_recommendations * 2, include_neighbors=True
        )
        plans = self.bb7_exo_plan(intent, beam_width=3, max_chain_length=5)

        # 2 — Golden path match
        golden = self._match_golden_path(intent)

        # 3 — Momentum context
        momentum_ctx = self._get_momentum_context()

        # 4 — Build narrative sections
        sections: List[str] = []

        # ── Intent Understanding
        sections.append(f"## Intent\n\n> {intent}\n")

        # ── Session Momentum
        if momentum_ctx:
            sections.append(f"## Session Context\n\n{momentum_ctx}\n")

        # ── Proven Workflow (if golden path matched)
        if golden:
            path_name = golden.get("name") or golden.get("path_name") or "workflow"
            path_desc = golden.get("description", "")
            steps_md = "\n".join(
                f"  {idx + 1}. `{step}`"
                for idx, step in enumerate(golden.get("chain", []))
            )
            sections.append(
                f"## Proven Workflow: *{path_name}*\n\n"
                f"{path_desc}\n\n"
                f"**Steps:**\n{steps_md}\n"
            )

        # ── Top Recommendations (concise table)
        top_tools = routed.get(
            "top_tools", routed.get("ranked_tools", routed.get("tools", []))
        )[:max_recommendations]
        if top_tools:
            lines = [
                "## Recommended Tools\n",
                "| # | Tool | Score | Reliability | Why |",
                "|---|------|-------|-------------|-----|",
            ]
            for idx, t in enumerate(top_tools, 1):
                one_liner = self._get_tool_one_liner(t["name"])
                rel_pct = f"{t.get('reliability', 0) * 100:.0f}%"
                score_pct = f"{t.get('score', 0) * 100:.0f}%"
                lines.append(
                    f"| {idx} | `{t['name']}` | {score_pct} | {rel_pct} | {one_liner} |"
                )
            sections.append("\n".join(lines) + "\n")

        # ── Plans summary
        plan_list = plans.get("candidate_plans", plans.get("plans", []))
        if plan_list:
            best = plan_list[0]
            chain_str = " → ".join(best.get("chain", []))
            conf = best.get("confidence", 0)
            sections.append(
                f"## Best Plan\n\n`{chain_str}` — confidence **{conf * 100:.0f}%**, "
                f"~{best.get('estimated_tokens', '?')} tokens\n"
            )

        # ── Health warnings for relevant categories
        seen_categories = {t.get("category") for t in top_tools if t.get("category")}
        warnings: List[str] = []
        for cat in seen_categories:
            w = self._get_category_health_warnings(cat)
            if w:
                warnings.extend(w)
        if warnings:
            sections.append(
                "## ⚠ Health Warnings\n\n"
                + "\n".join(f"- {w}" for w in warnings)
                + "\n"
            )

        # ── Exploration hints (low-usage but relevant categories)
        all_cats = set(self.category_graph.keys())
        used_cats = {t.get("category") for t in top_tools}
        unexplored = sorted(all_cats - used_cats)[:3]
        if unexplored:
            hints = ", ".join(f"`{c}`" for c in unexplored)
            sections.append(
                f"## Explore\n\nUnder-utilised categories that might help: {hints}\n"
            )

        narrative = "\n".join(sections)
        first_call = top_tools[0]["name"] if top_tools else None
        best_plan = plan_list[0] if plan_list else None
        overall_conf = best_plan.get("confidence", 0.0) if best_plan else 0.0

        return {
            "narrative": narrative,
            "recommended_first_call": first_call,
            "workflow_plan": best_plan,
            "confidence_score": round(overall_conf, 4),
            "golden_path_matched": (
                (golden.get("name") or golden.get("path_name")) if golden else None
            ),
            "exploration_suggestions": unexplored,
            "tool_count": len(top_tools),
        }

    def bb7_exo_preemptive_recovery(
        self,
        intent: str,
        risk_tolerance: str = "moderate",
    ) -> Dict[str, Any]:
        """Analyse a planned workflow for failure risks *before* execution.

        Scans the best plan for each step's reliability, finds alternatives
        for weak links, and generates risk-aware recommendations.

        Args:
            intent: The task intent to plan for.
            risk_tolerance: One of ``conservative``, ``moderate``, ``aggressive``.

        Returns:
            Dict with per-step risk analysis, alternatives, and overall
            risk score.
        """
        if not intent or not str(intent).strip():
            raise ValueError("intent parameter is required for preemptive recovery")
        self._maybe_sync_live_tools()
        intent = str(intent).strip()
        risk_tolerance = str(risk_tolerance).strip().lower()
        if risk_tolerance not in {"conservative", "moderate", "aggressive"}:
            risk_tolerance = "moderate"

        threshold_map = {"conservative": 0.80, "moderate": 0.60, "aggressive": 0.40}
        reliability_threshold = threshold_map[risk_tolerance]

        plans = self.bb7_exo_plan(intent, beam_width=3, max_chain_length=6)
        plan_list = plans.get("candidate_plans", plans.get("plans", []))
        if not plan_list:
            return {
                "status": "no_plans",
                "message": "No executable plans generated for this intent.",
                "risk_score": 1.0,
                "steps": [],
            }

        primary_plan = plan_list[0]
        chain = primary_plan.get("chain", [])
        step_analysis: List[Dict[str, Any]] = []
        risk_flags = 0

        for idx, tool_name in enumerate(chain):
            rel = self._reliability(tool_name)
            cat = self.tool_catalog.get(tool_name, {}).get("category", "misc")
            health_warnings = self._get_category_health_warnings(cat)
            at_risk = rel < reliability_threshold

            step_info: Dict[str, Any] = {
                "step": idx + 1,
                "tool": tool_name,
                "category": cat,
                "reliability": round(rel, 4),
                "status": "at_risk" if at_risk else "healthy",
            }

            if at_risk:
                risk_flags += 1
                alt = self._find_alternative_tool(tool_name, chain)
                if alt:
                    step_info["alternative"] = alt["name"]
                    step_info["alternative_reliability"] = round(alt["reliability"], 4)
                    step_info["recommendation"] = (
                        f"Consider swapping `{tool_name}` for `{alt['name']}` "
                        f"(reliability {alt['reliability'] * 100:.0f}% vs "
                        f"{rel * 100:.0f}%)"
                    )
                else:
                    step_info["recommendation"] = (
                        f"`{tool_name}` is below threshold ({rel * 100:.0f}%) "
                        f"with no same-category alternative. Proceed with caution."
                    )

            if health_warnings:
                step_info["health_warnings"] = health_warnings

            step_analysis.append(step_info)

        overall_risk = round(risk_flags / max(1, len(chain)), 4)

        # Fallback plans summary
        fallback_summaries = []
        for alt_plan in plan_list[1:]:
            fallback_summaries.append(
                {
                    "chain": alt_plan.get("chain", []),
                    "confidence": alt_plan.get("confidence", 0),
                }
            )

        return {
            "status": "analyzed",
            "risk_tolerance": risk_tolerance,
            "reliability_threshold": reliability_threshold,
            "overall_risk_score": overall_risk,
            "risky_step_count": risk_flags,
            "total_steps": len(chain),
            "primary_plan_confidence": primary_plan.get("confidence", 0),
            "steps": step_analysis,
            "fallback_plans": fallback_summaries,
        }

    def bb7_exo_route_focused(
        self,
        intent: str,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """Progressive-disclosure routing: return only the top-N tools with
        a single sentence each, plus a hint about how many more are available.

        This is for contexts where token economy matters — the LLM gets a
        tight, actionable list instead of a full routing dump.

        Args:
            intent: The task intent.
            top_n: Number of tools to surface (default 5).

        Returns:
            Dict with ``focused_tools``, ``total_available``, and
            ``expansion_hint``.
        """
        if not intent or not str(intent).strip():
            raise ValueError("intent parameter is required for focused routing")
        self._maybe_sync_live_tools()
        intent = str(intent).strip()
        top_n = max(1, min(15, int(top_n)))

        full = self.bb7_exo_route(intent, max_candidates=50, include_neighbors=True)
        all_tools = full.get(
            "top_tools", full.get("ranked_tools", full.get("tools", []))
        )
        focused = []
        for t in all_tools[:top_n]:
            focused.append(
                {
                    "name": t["name"],
                    "score": t.get("score", 0),
                    "one_liner": self._get_tool_one_liner(t["name"]),
                }
            )

        remaining = max(0, len(all_tools) - top_n)
        hint = (
            f"{remaining} more tools available — call bb7_exo_route for full list."
            if remaining > 0
            else "All matching tools shown."
        )

        return {
            "focused_tools": focused,
            "shown": len(focused),
            "total_available": len(all_tools),
            "expansion_hint": hint,
        }

    # ──────────────────────────────────────────────────────────────────────
    #  Phase-3 SOTA++ Tools: Execute · Resume · KPI
    # ──────────────────────────────────────────────────────────────────────

    def bb7_exo_execute_step(
        self,
        plan_id: str,
        step_index: int,
        tool_name: Optional[str] = None,
        result_summary: str = "",
        success: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Record step execution in a checkpointed plan.

        This does NOT execute the tool itself — the LLM runs the tool and then
        calls this to log the outcome. The checkpoint is updated atomically so
        plans survive crashes.

        Args:
            plan_id: Plan identifier from bb7_exo_plan.
            step_index: 0-based step index in the chain.
            tool_name: Tool that was executed (auto-resolved from chain if omitted).
            result_summary: Brief summary of the step outcome.
            success: Whether the step succeeded.
            dry_run: If True, preview the checkpoint mutation without persisting.

        Returns:
            Updated plan checkpoint with KPI.
        """
        plan_id = str(plan_id or "").strip()
        if not plan_id:
            raise ValueError("plan_id is required")

        with self._state_lock:
            plan = self._active_plans.get(plan_id)
            if not plan:
                return {
                    "status": "error",
                    "error": f"Plan '{plan_id}' not found. Available: {list(self._active_plans.keys())[:5]}",
                }

            step_index = int(step_index)
            chain = plan.get("chain", [])
            if step_index < 0 or step_index >= len(chain):
                return {
                    "status": "error",
                    "error": f"step_index {step_index} out of range [0, {len(chain) - 1}]",
                }

            resolved_tool = tool_name or chain[step_index]
            success_val = bool(success)

            step_record = {
                "step_index": step_index,
                "tool": resolved_tool,
                "success": success_val,
                "summary": str(result_summary)[:500],
                "timestamp": time.time(),
            }

            if dry_run:
                return {
                    "status": "dry_run",
                    "plan_id": plan_id,
                    "would_record": step_record,
                    "current_progress": f"{plan['kpi']['completed']}/{plan['kpi']['total_steps']}",
                }

            plan["steps_completed"].append(step_record)
            if step_index in plan["steps_remaining"]:
                plan["steps_remaining"].remove(step_index)
            plan["kpi"]["completed"] += 1
            if not success_val:
                plan["kpi"]["failed"] += 1
            plan["kpi"]["elapsed_sec"] = round(
                time.time() - plan.get("created_at", time.time()),
                2,
            )

            # Update plan status
            if not plan["steps_remaining"]:
                plan["status"] = "completed"
            elif plan["kpi"]["failed"] > len(chain) // 2:
                plan["status"] = "degraded"
            else:
                plan["status"] = "in_progress"

            self._active_plans[plan_id] = plan
            self._write_json(self.plans_file, self._active_plans)

        # Checkpoint log
        self._append_jsonl(
            self.checkpoint_file,
            {
                "event": "step_executed",
                "plan_id": plan_id,
                "step_index": step_index,
                "tool": resolved_tool,
                "success": success_val,
                "timestamp": time.time(),
            },
        )

        return {
            "status": plan["status"],
            "plan_id": plan_id,
            "step_recorded": step_record,
            "steps_remaining": plan["steps_remaining"],
            "kpi": plan["kpi"],
            "next_tool": chain[plan["steps_remaining"][0]]
            if plan["steps_remaining"]
            else None,
        }

    def bb7_exo_resume_plan(self, plan_id: str) -> Dict[str, Any]:
        """Resume a checkpointed plan from where it left off.

        Returns the plan state, completed steps, remaining steps, and the
        next tool to execute. Call this at session start to continue
        interrupted multi-step workflows.

        Args:
            plan_id: Plan identifier to resume.

        Returns:
            Plan checkpoint with next-action guidance.
        """
        plan_id = str(plan_id or "").strip()
        if not plan_id:
            # List available plans
            with self._state_lock:
                available = []
                for pid, p in self._active_plans.items():
                    available.append(
                        {
                            "plan_id": pid,
                            "intent": p.get("intent", ""),
                            "status": p.get("status", "unknown"),
                            "progress": f"{p['kpi']['completed']}/{p['kpi']['total_steps']}",
                            "created_at": p.get("created_at", 0),
                        }
                    )
            return {
                "status": "listing",
                "message": "No plan_id specified. Available plans:",
                "available_plans": sorted(
                    available, key=lambda x: x["created_at"], reverse=True
                )[:10],
            }

        with self._state_lock:
            plan = self._active_plans.get(plan_id)

        if not plan:
            return {
                "status": "error",
                "error": f"Plan '{plan_id}' not found.",
            }

        chain = plan.get("chain", [])
        remaining = plan.get("steps_remaining", [])
        completed = plan.get("steps_completed", [])

        next_step = None
        next_tool = None
        if remaining:
            next_step = remaining[0]
            next_tool = chain[next_step] if next_step < len(chain) else None

        return {
            "status": plan.get("status", "unknown"),
            "plan_id": plan_id,
            "intent": plan.get("intent", ""),
            "context": plan.get("context", ""),
            "chain": chain,
            "next_step_index": next_step,
            "next_tool": next_tool,
            "steps_completed": completed,
            "steps_remaining": remaining,
            "kpi": plan.get("kpi", {}),
            "fallback_chain": plan.get("fallback", []),
            "created_at": plan.get("created_at", 0),
            "age_sec": round(time.time() - plan.get("created_at", time.time()), 1),
        }

    def bb7_exo_kpi_report(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a KPI report for one or all active plans.

        Provides completion rate, success rate, elapsed time, throughput,
        and health assessment for each plan.

        Args:
            plan_id: Specific plan to report on. If omitted, reports all active plans.

        Returns:
            KPI report with per-plan metrics and aggregate stats.
        """
        with self._state_lock:
            if plan_id:
                plan = self._active_plans.get(str(plan_id).strip())
                if not plan:
                    return {"status": "error", "error": f"Plan '{plan_id}' not found."}
                plans_to_report = {str(plan_id).strip(): plan}
            else:
                plans_to_report = dict(self._active_plans)

        if not plans_to_report:
            return {
                "status": "empty",
                "message": "No active plans. Use bb7_exo_plan to create one.",
            }

        reports = []
        total_completed = 0
        total_failed = 0
        total_steps = 0

        for pid, plan in plans_to_report.items():
            kpi = plan.get("kpi", {})
            completed = kpi.get("completed", 0)
            failed = kpi.get("failed", 0)
            total = kpi.get("total_steps", 1)
            elapsed = kpi.get("elapsed_sec", 0)

            completion_pct = round(completed / max(total, 1) * 100, 1)
            success_rate = round((completed - failed) / max(completed, 1) * 100, 1)
            throughput = round(completed / max(elapsed, 0.01), 3)  # steps/sec

            health = "healthy"
            if plan.get("status") == "degraded":
                health = "degraded"
            elif failed > 0 and success_rate < 50:
                health = "critical"
            elif failed > 0:
                health = "warning"

            reports.append(
                {
                    "plan_id": pid,
                    "intent": plan.get("intent", "")[:80],
                    "status": plan.get("status", "unknown"),
                    "health": health,
                    "completion_pct": completion_pct,
                    "success_rate_pct": success_rate,
                    "completed_steps": completed,
                    "failed_steps": failed,
                    "total_steps": total,
                    "remaining": len(plan.get("steps_remaining", [])),
                    "elapsed_sec": elapsed,
                    "throughput_steps_per_sec": throughput,
                    "created_at": plan.get("created_at", 0),
                }
            )

            total_completed += completed
            total_failed += failed
            total_steps += total

        aggregate = {
            "total_plans": len(reports),
            "aggregate_completion_pct": round(
                total_completed / max(total_steps, 1) * 100,
                1,
            ),
            "aggregate_success_rate_pct": round(
                (total_completed - total_failed) / max(total_completed, 1) * 100,
                1,
            ),
            "total_steps_executed": total_completed,
            "total_failures": total_failed,
        }

        return {
            "status": "ok",
            "reports": reports,
            "aggregate": aggregate,
        }

    def bb7_exo_suggest_next(
        self,
        current_tool: Optional[str] = None,
        current_category: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Orchestration prediction: suggest next tools/actions given current context.

        This is the key orchestration tool - given what just happened (current_tool)
        or what you're trying to do (intent), it predicts the logical next steps
        by combining:
        - Category transition probabilities from momentum tracking
        - Golden path / auto-discovered workflow continuity
        - Cross-category dependencies (memory→analysis→execution chains)

        Args:
            current_tool: Tool that was just executed (for momentum prediction)
            current_category: Category of current work (alternative to current_tool)
            intent: Optional intent to find next steps for

        Returns:
            Dict with suggested next tools, predicted workflows, and orchestration hints.
        """
        self._maybe_sync_live_tools()

        suggestions: List[Dict[str, Any]] = []

        # 1. Workflow continuation - what comes next in active golden paths?
        active_wf = self.session_state.get("active_workflow")
        if active_wf and active_wf.get("remaining"):
            for tool_name in active_wf["remaining"][:2]:
                if tool_name in self.tool_catalog:
                    suggestions.append(
                        {
                            "tool": tool_name,
                            "reason": "workflow_continuation",
                            "workflow": active_wf.get("name"),
                            "position": active_wf.get("position", 0) + 1,
                            "confidence": active_wf.get("confidence", 0.5),
                        }
                    )

        # 2. Category transition from momentum
        if current_tool:
            current_cat = self.tool_catalog.get(current_tool, {}).get(
                "category", "misc"
            )
        elif current_category:
            current_cat = current_category
        else:
            current_cat = None

        if current_cat and current_cat in self.category_transitions:
            transitions = self.category_transitions[current_cat]
            sorted_cats = sorted(transitions.items(), key=lambda x: x[1], reverse=True)

            for next_cat, prob in sorted_cats[:3]:
                if next_cat == current_cat:
                    continue
                # Find best tool in that category
                cat_tools = [
                    (n, self._reliability(n))
                    for n, info in self.tool_catalog.items()
                    if info.get("category") == next_cat
                ]
                if cat_tools:
                    cat_tools.sort(key=lambda x: x[1], reverse=True)
                    best_tool, rel = cat_tools[0]
                    suggestions.append(
                        {
                            "tool": best_tool,
                            "reason": "category_transition",
                            "from_category": current_cat,
                            "to_category": next_cat,
                            "probability": round(prob, 3),
                            "reliability": round(rel, 3),
                        }
                    )

        # 3. Intent-based suggestions if provided
        if intent:
            suggest_match = self._match_golden_path(intent)
            routed = self._score_tools(
                intent,
                max_candidates=5,
                include_neighbors=True,
                neighbor_distance=1,
                golden_match=suggest_match,
            )
            for t in routed[:3]:
                # Avoid duplicates
                if not any(s.get("tool") == t["name"] for s in suggestions):
                    suggestions.append(
                        {
                            "tool": t["name"],
                            "reason": "intent_match",
                            "score": t.get("score", 0),
                            "category": t.get("category"),
                        }
                    )

        # 4. Cross-tool orchestration hints - memory+journal+analysis combos
        memory_tools = [
            n for n, i in self.tool_catalog.items() if "memory" in i.get("category", "")
        ]
        journal_tools = [
            n for n, i in self.tool_catalog.items() if "journal" in n.lower()
        ]
        analysis_tools = [
            n for n, i in self.tool_catalog.items() if i.get("category") == "analysis"
        ]

        orchestration_patterns = []
        if current_tool and any(m in current_tool.lower() for m in ["memory", "store"]):
            if analysis_tools:
                orchestration_patterns.append(
                    {
                        "pattern": "memory → analysis",
                        "next_categories": ["analysis"],
                        "rationale": "After storing, analyze implications",
                    }
                )
        if current_tool and any(
            j in current_tool.lower() for j in ["journal", "decision"]
        ):
            if memory_tools:
                orchestration_patterns.append(
                    {
                        "pattern": "journal → memory",
                        "next_categories": ["memory"],
                        "rationale": "Persist decision context to memory",
                    }
                )

        return {
            "status": "ok",
            "current_tool": current_tool,
            "current_category": current_cat,
            "suggestions": suggestions[:6],
            "orchestration_patterns": orchestration_patterns,
            "active_workflow": active_wf.get("name") if active_wf else None,
            "momentum_context": self._get_momentum_context(),
        }

    # ── Lisan al-Gaib MCP Tools ───────────────────────────────────────────── #

    def bb7_lisan_recall(
        self,
        context: str,
        max_memories: int = 5,
        include_plans: bool = True,
        include_activity: bool = True,
        include_decisions: bool = True,
    ) -> Dict[str, Any]:
        """
        Context Resurrection: single-call session recovery for long-horizon tasks.

        Aggregates:
          1. Relevant memories via BM25 (calls bb7_memory_surface_context directly)
          2. Active plans from checkpoint (active_plans.json)
          3. Recent cross-AI activity (cross_ai_activity.jsonl)
          4. Session momentum state
          5. Relevant prior decisions (CognitiveJournalSubsystem)

        Returns a single LLM-ready context blob plus structured fields.
        Replaces bb7_journal_surface_relevant for session resumption.
        """
        max_memories = max(1, min(20, int(max_memories)))
        sections: List[str] = [
            f"## Context Resurrection — {time.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        recall_failures: List[str] = []

        # 1. Memories (via live tools provider if available)
        memories_raw: List[str] = []
        try:
            memory_text = ""
            if self._live_tools_provider is not None:
                live = self._live_tools_provider()
                surf_tool = live.get("bb7_memory_surface_context")
                if surf_tool and callable(surf_tool.get("function")):
                    raw = surf_tool["function"](
                        context_text=context, max_results=max_memories
                    )
                    memory_text = str(raw) if raw else ""
            if memory_text:
                sections.append(f"### Surfaced Memories\n{memory_text}")
                memories_raw = [memory_text]
        except Exception as _mem_err:
            failure = f"memory surface failed: {_mem_err}"
            recall_failures.append(failure)
            self.logger.error("bb7_lisan_recall %s", failure)

        # 2. Active plans
        active_plans_list: List[Dict[str, Any]] = []
        if include_plans:
            try:
                for pid, plan in list(self._active_plans.items())[:3]:
                    steps = plan.get("steps", [])
                    completed = sum(1 for s in steps if s.get("status") == "completed")
                    active_plans_list.append(
                        {
                            "plan_id": pid,
                            "goal": plan.get("goal", "")[:100],
                            "progress": f"{completed}/{len(steps)} steps",
                            "created_at": plan.get("created_at", 0),
                        }
                    )
                if active_plans_list:
                    plan_lines = ["### Active Plans"]
                    for p in active_plans_list:
                        plan_lines.append(
                            f"- **{p['plan_id']}**: {p['goal']} ({p['progress']})"
                        )
                    sections.append("\n".join(plan_lines))
            except Exception as _plan_err:
                failure = f"active plan recall failed: {_plan_err}"
                recall_failures.append(failure)
                self.logger.error("bb7_lisan_recall %s", failure)

        # 3. Cross-AI activity
        cross_ai: List[Dict[str, Any]] = []
        if include_activity and self.activity_file.exists():
            try:
                with open(self.activity_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines[-5:]:
                    try:
                        entry = json.loads(line.strip())
                        cross_ai.append(
                            {
                                "ai_instance": entry.get("ai_instance", "unknown"),
                                "tools": " → ".join(entry.get("tools_used", [])),
                                "success": entry.get("success", True),
                                "intent": entry.get("intent", "")[:60],
                            }
                        )
                    except Exception as line_err:
                        failure = f"cross-AI activity parse failed: {line_err}"
                        recall_failures.append(failure)
                        self.logger.error("bb7_lisan_recall %s", failure)
                if cross_ai:
                    act_lines = ["### Recent Activity"]
                    for a in cross_ai:
                        status = "OK" if a["success"] else "FAIL"
                        act_lines.append(f"- {status} `{a['tools']}` — {a['intent']}")
                    sections.append("\n".join(act_lines))
            except Exception as _act_err:
                failure = f"cross-AI activity recall failed: {_act_err}"
                recall_failures.append(failure)
                self.logger.error("bb7_lisan_recall %s", failure)

        # 4. Momentum
        momentum_str = self._get_momentum_context()
        if (
            momentum_str
            and momentum_str != "Session just started — no momentum context yet."
        ):
            sections.append(f"### Session Momentum\n{momentum_str}")

        # 5. Prior decisions
        prior_decisions: List[Dict[str, Any]] = []
        if include_decisions and self._cognitive_journal is not None:
            try:
                prior_decisions = self._cognitive_journal.surface_relevant(
                    context, max_results=max_memories
                )
                if prior_decisions:
                    dec_lines = ["### Prior Decisions"]
                    for d in prior_decisions[:5]:
                        status = (
                            "OK"
                            if d.get("validated")
                            else ("FAIL" if d.get("validated") is False else "PENDING")
                        )
                        dec_lines.append(f"- {status} {d.get('decision', '')[:80]}")
                    sections.append("\n".join(dec_lines))
            except Exception as _dec_err:
                failure = f"decision recall failed: {_dec_err}"
                recall_failures.append(failure)
                self.logger.error("bb7_lisan_recall %s", failure)

        # 6. Orchestration suggestions — what comes next?
        suggest_next: List[Dict[str, Any]] = []
        try:
            suggest_result = self.bb7_exo_suggest_next(
                current_category="memory",  # Context-agnostic default
                intent=context,
            )
            suggest_next = suggest_result.get("suggested_tools", [])[:3]
            if suggest_next:
                suggest_lines = ["### Suggested Next Steps"]
                for s in suggest_next:
                    tool = s.get("tool", "unknown")
                    reason = s.get("reason", "")[:60]
                    suggest_lines.append(f"- **{tool}**: {reason}")
                sections.append("\n".join(suggest_lines))
        except Exception as _sug_err:
            failure = f"suggest_next failed: {_sug_err}"
            recall_failures.append(failure)
            self.logger.error("bb7_lisan_recall %s", failure)

        if recall_failures:
            sections.append("### Recall Failures\n" + "\n".join(f"- {f}" for f in recall_failures))

        context_blob = "\n\n".join(sections)

        return {
            "status": "ok",
            "session_id": self.session_state.get("session_id", "unknown"),
            "context_blob": context_blob,
            "memories": memories_raw,
            "active_plans": active_plans_list,
            "cross_ai_activity": cross_ai,
            "momentum": momentum_str,
            "prior_decisions": prior_decisions,
            "suggested_next": suggest_next,
            "recall_failures": recall_failures,
            "recall_timestamp": time.time(),
        }

    def bb7_lisan_distill(
        self,
        trajectory: Any,
        source_plane: str = "bb7_agent_harness",
        session_id: Optional[str] = None,
        total_tokens: int = 0,
        latency_seconds: float = 0.0,
        tool_error_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Explicit distillation: log a complete LLM trajectory for RFT.

        Called by bb7_agent_run after completing a task (success or max-iterations).
        Trajectory is a list of role/content/tool_calls dicts (standard chat format).
        """
        if self._distillation is None:
            return {
                "status": "unavailable",
                "reason": "DistillationSubsystem not initialized",
            }

        if not isinstance(trajectory, list):
            return {
                "status": "error",
                "reason": f"trajectory must be a list, got {type(trajectory).__name__}",
            }

        effective_session = session_id or self.session_state.get(
            "session_id", "unknown"
        )
        telemetry = {
            "total_tokens": int(total_tokens),
            "latency_seconds": float(latency_seconds),
            "tool_error_count": int(tool_error_count),
        }
        trajectory_id = self._distillation.log_full_trajectory(
            source_plane=source_plane,
            session_id=effective_session,
            trajectory=trajectory,
            telemetry=telemetry,
        )
        heuristics = self._distillation._evaluate_heuristics(trajectory, telemetry)
        return {
            "status": "logged",
            "trajectory_id": trajectory_id,
            "heuristics": heuristics,
            "session_id": effective_session,
            "trajectory_length": len(trajectory),
        }

    def bb7_lisan_intend(
        self,
        user_message: str,
        verbosity: str = "normal",
    ) -> Dict[str, Any]:
        """
        Expose spectral intent analysis as a direct MCP tool.

        Makes lisan's routing reasoning VISIBLE to the AI using MCP.
        Returns decomposed intents, confidence scores, recommended tool categories,
        momentum bonus, and golden path match.
        """
        query = str(user_message or "").strip()
        if not query:
            raise ValueError("user_message is required")

        category_scores: Dict[str, float] = defaultdict(float)
        routing_mode = "keyword_fallback"
        sorted_intents: List[Tuple[str, float]] = []

        if self._lisan_available and self._spectral_decomposer is not None and self.tool_catalog:
            routing_mode = "spectral"
            for tool_name, info in self.tool_catalog.items():
                category = info.get("category", "misc")
                try:
                    similarity = self._spectral_decomposer.spectral_similarity(
                        query,
                        f"{info.get('name', tool_name)} {info.get('description', '')}",
                    )
                except Exception:
                    similarity = 0.0
                category_scores[category] += similarity
            if category_scores:
                gated = self._spectral_decomposer.entropy_gate(category_scores)
                sorted_intents = sorted(gated.items(), key=lambda x: x[1], reverse=True)

        if not sorted_intents:
            query_tokens = self._tokenize(query)
            intent_scores = self._intent_weights(query_tokens, raw_query=query)
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_intents:
            sorted_intents = [("misc", 1.0)]

        primary_intent = sorted_intents[0][0]
        decomposed = [
            {"category": cat, "score": round(float(score), 4)}
            for cat, score in sorted_intents
            if float(score) > 0.0
        ]
        recommended_cats = [d["category"] for d in decomposed[:3]]
        momentum_bonus = self._compute_momentum_bonus(primary_intent, primary_intent)

        golden_match: Optional[str] = None
        try:
            match = self._match_golden_path(query)
            if match:
                golden_match = (
                    match.get("name")
                    or match.get("path_name")
                    or match.get("description", "")[:80]
                )
        except Exception as e:
            self.logger.warning("Failed to match golden path in routing (non-fatal): %s", e)

        result: Dict[str, Any] = {
            "decomposed_intents": decomposed,
            "primary_intent": primary_intent,
            "recommended_tool_categories": recommended_cats,
            "momentum_bonus": round(momentum_bonus, 4),
            "golden_path_match": golden_match,
            "spectral_available": self._lisan_available,
            "routing_mode": routing_mode,
        }

        if verbosity == "detailed" and self._lisan_available:
            try:
                engine = NarrativeEngine(self.tool_catalog, self.logger)
                top_tools = self._score_tools(
                    query,
                    max_candidates=5,
                    include_neighbors=False,
                    neighbor_distance=1,
                    golden_match=match if "match" in locals() else None,
                )[:5]
                result["narrative"] = engine.generate_briefing(
                    intent=query,
                    intent_category=primary_intent,
                    top_tools=top_tools,
                    best_chain=None,
                    golden_match=None,
                    momentum=None,
                    include_exploration=False,
                    verbosity="normal",
                    tool_priors=self.state.get("tool_priors", {}),
                )
            except Exception as _narr_err:
                self.logger.debug("NarrativeEngine briefing failed: %s", _narr_err)
                result["narrative"] = ""

        return result

    def bb7_dt_advanced_features(
        self,
        candidates: List[str],
        category: str = "misc",
        session_id: Optional[str] = None,
        recent_tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Query Muad'Dib advanced modality features for candidate tools.

        Wraps DigitalTwinTool.bb7_dt_advanced_features with session defaults.
        Returns per-tool provenance-tagged scores when MUADIB_ADVANCED_MODE=1.
        Always safe to call — returns {ok: False, reason: ...} when bridge is off.
        """
        if self._digital_twin is None:
            return {"ok": False, "reason": "neural_twin_unavailable", "features": {}}
        effective_session = session_id or self.session_state.get("session_id", "default")
        effective_recent = recent_tools or [
            t.get("tool", "") for t in self.session_state.get("recent_tools", [])
        ]
        return self._digital_twin.bb7_dt_advanced_features(
            candidates=list(candidates),
            category=str(category),
            session_id=str(effective_session),
            recent_tools=list(effective_recent),
        )

    def bb7_dt_self_play(
        self,
        episodes: int = 32,
        max_steps: int = 4,
        learning_rate: Optional[float] = None,
        promote: bool = False,
        update_qtable: bool = False,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run Muad'Dib self-play against the live tool catalog.

        This wrapper preserves the one-plane invariant: the digital twin uses
        the exoskeleton's already-loaded live catalog, trains an isolated
        candidate self-play head, saves safetensors weights, and promotes only
        after a complete checkpoint write when promotion is explicitly requested.
        """
        if self._digital_twin is None:
            return {"ok": False, "reason": "neural_twin_unavailable"}
        effective_session = session_id or self.session_state.get(
            "session_id", "muadib_self_play"
        )
        return self._digital_twin.bb7_dt_self_play(
            tool_catalog=self.tool_catalog,
            episodes=int(episodes),
            max_steps=int(max_steps),
            learning_rate=learning_rate,
            promote=bool(promote),
            update_qtable=bool(update_qtable),
            session_id=str(effective_session),
        )

    def bb7_dt_self_play_lock(
        self,
        locked: bool = True,
        reason: str = "",
        operator: str = "exoskeleton",
    ) -> Dict[str, Any]:
        """
        Lock/unlock Muad'Dib self-play active-head promotion.

        This does not stop candidate self-play. It pins the active/champion
        self-play head so continuous cadence archives candidates without
        swapping the live in-memory head or active checkpoint pointer.
        """
        if self._digital_twin is None:
            return {"ok": False, "reason": "neural_twin_unavailable"}
        return self._digital_twin.bb7_dt_self_play_lock(
            locked=bool(locked),
            reason=str(reason or ""),
            operator=str(operator or "exoskeleton"),
        )

    def bb7_dt_checkpoint_status(self) -> Dict[str, Any]:
        """Inspect Muad'Dib tokenizer/self-play checkpoint state."""
        if self._digital_twin is None:
            return {"ok": False, "reason": "neural_twin_unavailable"}
        return self._digital_twin.bb7_dt_checkpoint_status()

    def get_tools(self) -> Dict[str, Callable]:
        """Return exoskeleton tool definitions."""
        return {
            "bb7_exo_bootstrap": {
                "function": self.bb7_exo_bootstrap,
                "description": "Bootstrap capability-aware context for the exoskeleton control loop.",
                "parameters": [
                    {
                        "name": "include_recent_outcomes",
                        "description": "Include recent reflection outcomes.",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "include_healthcheck",
                        "description": "Include critical tool health summary.",
                        "type": "boolean",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_list_tool_categories": {
                "function": self.bb7_exo_list_tool_categories,
                "description": "List canonical capability categories and counts.",
                "parameters": [],
            },
            "bb7_exo_category_specific_tools": {
                "function": self.bb7_exo_category_specific_tools,
                "description": "List tools in a category with reliability priors.",
                "parameters": [
                    {
                        "name": "category",
                        "description": "Category to inspect.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "limit",
                        "description": "Maximum rows to return.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_route": {
                "function": self.bb7_exo_route,
                "description": "Intent-conditioned retrieval with semantic and graph scoring.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "Intent to route.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "max_candidates",
                        "description": "Maximum candidate tools.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "include_neighbors",
                        "description": "Expand via category graph.",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "neighbor_distance",
                        "description": "Neighbor hop distance.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_plan": {
                "function": self.bb7_exo_plan,
                "description": "Generate candidate tool chains with confidence and fallback.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "Intent to plan for.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "context",
                        "description": "Optional context.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "beam_width",
                        "description": "Number of candidate plans.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "max_chain_length",
                        "description": "Maximum chain length.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_reflect": {
                "function": self.bb7_exo_reflect,
                "description": "Reflect outcomes and update tool/chain priors.",
                "parameters": [
                    {
                        "name": "plan_id",
                        "description": "Plan identifier.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "tools_used",
                        "description": "Executed tools as a list or comma-separated string.",
                        "type": "array",
                        "required": True,
                    },
                    {
                        "name": "success",
                        "description": "Execution success value.",
                        "type": "boolean",
                        "required": True,
                    },
                    {
                        "name": "error",
                        "description": "Optional error details.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "intent",
                        "description": "Optional intent for mapping reinforcement.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "recovery_strategy",
                        "description": "Optional explicit recovery strategy.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_state": {
                "function": self.bb7_exo_state,
                "description": "Inspect exoskeleton state, priors, and discovered macros.",
                "parameters": [
                    {
                        "name": "limit",
                        "description": "Maximum rows per section.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_briefing": {
                "function": self.bb7_exo_briefing,
                "description": "Generate a natural-language capability narrative with proven workflows, recommendations, and health warnings for the given intent.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "The user-facing goal or task description.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "max_recommendations",
                        "description": "Maximum recommended tools to surface (default 5).",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_preemptive_recovery": {
                "function": self.bb7_exo_preemptive_recovery,
                "description": "Analyse a planned workflow for failure risks before execution and suggest alternatives for weak links.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "The task intent to plan for.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "risk_tolerance",
                        "description": "Risk tolerance: conservative, moderate, or aggressive.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_route_focused": {
                "function": self.bb7_exo_route_focused,
                "description": "Progressive-disclosure routing: top-N tools with one-liner descriptions and expansion hint.",
                "parameters": [
                    {
                        "name": "intent",
                        "description": "The task intent.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "top_n",
                        "description": "Number of tools to surface (default 5).",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_suggest_next": {
                "function": self.bb7_exo_suggest_next,
                "description": "Orchestration prediction: suggest next tools/actions given current context. Key for chaining memory→analysis→execution workflows.",
                "parameters": [
                    {
                        "name": "current_tool",
                        "description": "Tool that was just executed (for momentum prediction).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "current_category",
                        "description": "Category of current work (alternative to current_tool).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "intent",
                        "description": "Optional intent to find next steps for.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_get_recent_activity": {
                "function": self.bb7_exo_get_recent_activity,
                "description": "Get recent activity from all AI instances - call at session start to sync context with other AIs.",
                "parameters": [
                    {
                        "name": "limit",
                        "description": "Number of recent events to return (default 10).",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_execute_step": {
                "function": self.bb7_exo_execute_step,
                "description": (
                    "Record a step execution in a checkpointed plan. Call AFTER running "
                    "the tool to log the outcome. Checkpoints persist across crashes."
                ),
                "parameters": [
                    {
                        "name": "plan_id",
                        "description": "Plan identifier from bb7_exo_plan.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "step_index",
                        "description": "0-based step index in the chain.",
                        "type": "number",
                        "required": True,
                    },
                    {
                        "name": "tool_name",
                        "description": "Tool that was executed (auto-resolved from chain if omitted).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "result_summary",
                        "description": "Brief summary of the step outcome.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "success",
                        "description": "Whether the step succeeded.",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "dry_run",
                        "description": "Preview checkpoint mutation without persisting.",
                        "type": "boolean",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_resume_plan": {
                "function": self.bb7_exo_resume_plan,
                "description": (
                    "Resume a checkpointed plan from where it left off. Returns next "
                    "tool to execute and full progress state. Call at session start to "
                    "continue interrupted workflows. Omit plan_id to list all plans."
                ),
                "parameters": [
                    {
                        "name": "plan_id",
                        "description": "Plan identifier to resume (omit to list all).",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_exo_kpi_report": {
                "function": self.bb7_exo_kpi_report,
                "description": (
                    "Generate a KPI report for one or all active plans. Shows completion "
                    "rate, success rate, throughput, health assessment, and aggregate stats."
                ),
                "parameters": [
                    {
                        "name": "plan_id",
                        "description": "Specific plan to report on (omit for all).",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            # ── Lisan al-Gaib tools ───────────────────────────────────────── #
            "bb7_lisan_recall": {
                "function": self.bb7_lisan_recall,
                "description": (
                    "Context Resurrection: single-call long-horizon session recovery. "
                    "Combines relevant memories (BM25), active plan checkpoints, "
                    "cross-AI activity, session momentum, and prior decisions into "
                    "one LLM-ready context blob. "
                    "Call at session start instead of bb7_memory_surface_context + "
                    "bb7_exo_get_recent_activity separately."
                ),
                "parameters": [
                    {
                        "name": "context",
                        "description": "Current task description or session context text.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "max_memories",
                        "description": "Max memories to surface (default 5).",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "include_plans",
                        "description": "Include active plan checkpoints (default true).",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "include_activity",
                        "description": "Include cross-AI activity (default true).",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "include_decisions",
                        "description": "Include prior decisions from cognitive journal (default true).",
                        "type": "boolean",
                        "required": False,
                    },
                ],
            },
            "bb7_lisan_distill": {
                "function": self.bb7_lisan_distill,
                "description": (
                    "Explicit distillation: log a complete LLM trajectory "
                    "(role/content/tool_calls list) to the RFT training dataset. "
                    "Call after bb7_agent_run completes a task. "
                    "Trajectory format: [{role: user/assistant/tool, content: str, tool_calls: [...]}]."
                ),
                "parameters": [
                    {
                        "name": "trajectory",
                        "description": "List of message dicts (role/content/tool_calls).",
                        "type": "array",
                        "required": True,
                    },
                    {
                        "name": "source_plane",
                        "description": "Origin identifier (default: bb7_agent_harness).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "session_id",
                        "description": "Session identifier (auto-detected if omitted).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "total_tokens",
                        "description": "Total tokens consumed by the trajectory.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "latency_seconds",
                        "description": "Total wall-clock seconds.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "tool_error_count",
                        "description": "Number of tool errors encountered.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_lisan_intend": {
                "function": self.bb7_lisan_intend,
                "description": (
                    "Expose spectral intent analysis as a direct tool. "
                    "Given a user message, returns: decomposed intents with confidence scores, "
                    "recommended tool categories, momentum bonus, and golden path match. "
                    "Makes lisan's routing reasoning VISIBLE. "
                    "Use to verify the system's intent interpretation before routing with bb7_exo_route."
                ),
                "parameters": [
                    {
                        "name": "user_message",
                        "description": "The user's natural language message or task description.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "verbosity",
                        "description": "Output verbosity: minimal | normal | detailed (default: normal).",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            # ── Muad'Dib advanced features ────────────────────────────────── #
            "bb7_dt_advanced_features": {
                "function": self.bb7_dt_advanced_features,
                "description": (
                    "Query Muad'Dib advanced modality features for candidate tools. "
                    "Returns per-tool provenance-tagged scores (trained_q from Q-table, "
                    "trained_cooccur from observation buffer, untrained_embed from embed table). "
                    "Requires MUADIB_ADVANCED_MODE=1 to return real signals; "
                    "returns {ok: false, reason: bridge_disabled} otherwise. "
                    "Use for routing signal inspection and integration validation."
                ),
                "parameters": [
                    {
                        "name": "candidates",
                        "description": "List of tool names to evaluate.",
                        "type": "array",
                        "required": True,
                    },
                    {
                        "name": "category",
                        "description": "Tool category context (default: misc).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "session_id",
                        "description": "Session identifier (defaults to active session).",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "recent_tools",
                        "description": "Recent tool names for co-occurrence signal (defaults to session history).",
                        "type": "array",
                        "required": False,
                    },
                ],
            },
            "bb7_dt_self_play": {
                "function": self.bb7_dt_self_play,
                "description": (
                    "Run bounded Muad'Dib self-play against the live tool catalog. "
                    "Trains an isolated candidate policy/value head, saves real tensor "
                    "weights as safetensors, and promotes only when explicitly requested "
                    "after a complete atomic checkpoint write. JSON is metadata/ledger only."
                ),
                "parameters": [
                    {
                        "name": "episodes",
                        "description": "Number of bounded self-play episodes (default: 32, max: 512).",
                        "type": "integer",
                        "required": False,
                    },
                    {
                        "name": "max_steps",
                        "description": "Tools per simulated episode (default: 4, max bounded by self-play config).",
                        "type": "integer",
                        "required": False,
                    },
                    {
                        "name": "learning_rate",
                        "description": "Optional AdamW learning rate override.",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "promote",
                        "description": "Request promotion of the complete candidate safetensors checkpoint to active head (default false / archive-only). Ignored when the active promotion lock is set.",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "update_qtable",
                        "description": "Whether synthetic self-play should also update the real Q-table (default false).",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "session_id",
                        "description": "Session identifier for optional synthetic Q-table observations.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_dt_self_play_lock": {
                "function": self.bb7_dt_self_play_lock,
                "description": (
                    "Lock or unlock Muad'Dib self-play active-head promotion. "
                    "Continuous self-play may still train/archive candidate safetensors "
                    "checkpoints while the active/champion head is locked."
                ),
                "parameters": [
                    {
                        "name": "locked",
                        "description": "True to pin active/champion weights; false to allow promotion again.",
                        "type": "boolean",
                        "required": False,
                    },
                    {
                        "name": "reason",
                        "description": "Optional operator-readable reason persisted to checkpoint metadata.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "operator",
                        "description": "Optional actor/source label for the lock mutation.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_dt_checkpoint_status": {
                "function": self.bb7_dt_checkpoint_status,
                "description": (
                    "Inspect Muad'Dib tokenizer and self-play checkpoint state, including "
                    "active safetensors pointers, promotion-lock state, and legacy .pt "
                    "migration fallback files."
                ),
                "parameters": [],
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tool = ExoskeletonTool()
    print(json.dumps(tool.bb7_exo_bootstrap(), indent=2))
    print(
        json.dumps(
            tool.bb7_exo_route("debug async web failures and store findings in memory"),
            indent=2,
        )
    )
    print(
        json.dumps(
            tool.bb7_exo_plan(
                "analyze project and validate tool execution reliability"
            ),
            indent=2,
        )
    )
