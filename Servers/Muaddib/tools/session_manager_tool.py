#!/usr/bin/env python3
"""
Enhanced Session Manager Tool - Auto-memory formation and cross-system intelligence
Integrates with enhanced memory system for automatic insight capture
"""

import json
import logging
import time
import uuid
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
import threading
import hashlib
import re
from collections import Counter, defaultdict

# Import enhanced memory tool
try:
    from tools.memory_tool import EnhancedMemoryTool

    ENHANCED_MEMORY_AVAILABLE = True
except ImportError:
    ENHANCED_MEMORY_AVAILABLE = False
    EnhancedMemoryTool = None


class EnhancedSessionTool:
    """Enhanced cognitive session management with automatic memory formation"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        configured_data_dir = os.environ.get(
            "SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"
        ).strip()
        if not configured_data_dir:
            configured_data_dir = "/home/daeron/Somnus-MCP/data"
        base_data_dir = Path(data_dir or configured_data_dir).expanduser().resolve()
        self.sessions_dir = base_data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Initialize enhanced memory integration
        if ENHANCED_MEMORY_AVAILABLE and EnhancedMemoryTool:
            self.memory_tool = EnhancedMemoryTool(
                storage_file=str(base_data_dir / "memory_store.json")
            )
        else:
            self.memory_tool = None
            self.logger.warning("Enhanced memory tool not available")

        # Session files
        self.index_file = self.sessions_dir / "session_index.json"
        self.patterns_file = self.sessions_dir / "learned_patterns.json"
        self.intelligence_file = self.sessions_dir / "session_intelligence.json"

        # Current session state
        self.current_session_id = None
        self.current_session = None
        self._lock = threading.Lock()

        # Auto-memory formation settings
        self.auto_memory_thresholds = {
            "insight_keywords": [
                "discovered",
                "learned",
                "realized",
                "found",
                "solution",
                "breakthrough",
            ],
            "decision_keywords": [
                "decided",
                "chosen",
                "selected",
                "committed",
                "determined",
            ],
            "problem_keywords": [
                "error",
                "bug",
                "issue",
                "problem",
                "failed",
                "broken",
            ],
            "success_keywords": [
                "working",
                "fixed",
                "resolved",
                "completed",
                "successful",
            ],
            "pattern_keywords": [
                "pattern",
                "always",
                "typically",
                "usually",
                "consistently",
            ],
        }

        # Load learned patterns
        self.learned_patterns = self._load_learned_patterns()
        self.session_intelligence = self._load_session_intelligence()

        self.logger.info(
            "Enhanced session manager initialized with auto-memory formation"
        )

    def _read_json_file(self, path: Path, default: Any, label: str) -> Any:
        """Read JSON with light retry handling for transient Windows file-lock races."""
        for attempt in range(5):
            try:
                if not path.exists():
                    return default
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                return default
            except json.JSONDecodeError as e:
                if attempt < 2:
                    time.sleep(0.05 * (attempt + 1))
                    continue
                self.logger.error(f"Failed to load {label}: {e}")
                return default
            except Exception as e:
                winerror = getattr(e, "winerror", None)
                if isinstance(e, PermissionError) or winerror in {5, 32}:
                    time.sleep(0.05 * (attempt + 1))
                    continue
                self.logger.error(f"Failed to load {label}: {e}")
                return default
        return default

    def _write_json_atomic(
        self,
        path: Path,
        payload: Any,
        label: str,
    ) -> None:
        """Atomically persist JSON with unique temp files and retry/backoff on Windows locks."""
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        last_error: Optional[Exception] = None

        for attempt in range(8):
            tmp = path.with_name(
                f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
            )
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(serialized)
                os.replace(tmp, path)
                return
            except Exception as e:
                last_error = e
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass

                winerror = getattr(e, "winerror", None)
                if isinstance(e, PermissionError) or winerror in {5, 32}:
                    time.sleep(0.05 * (attempt + 1))
                    continue
                raise

        if last_error is not None:
            raise last_error

    def _with_file_lock(
        self,
        path: Path,
        label: str,
        action: Callable[[], Any],
        timeout_seconds: float = 15.0,
    ) -> Any:
        """Serialize cross-process updates with a lightweight sidecar lock file."""
        lock_path = path.with_name(f"{path.name}.lock")
        deadline = time.monotonic() + timeout_seconds

        backoff = 0.001

        while True:
            lock_fd: Optional[int] = None
            acquired = False
            try:
                lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                acquired = True
                with os.fdopen(lock_fd, "w", encoding="utf-8") as lock_handle:
                    lock_fd = None
                    lock_handle.write(
                        json.dumps(
                            {
                                "pid": os.getpid(),
                                "thread": threading.get_ident(),
                                "label": label,
                                "acquired_at": time.time(),
                            },
                            ensure_ascii=False,
                        )
                    )
                return action()
            except FileExistsError:
                try:
                    if lock_path.exists():
                        age_seconds = time.time() - lock_path.stat().st_mtime
                        if age_seconds > 120:
                            lock_path.unlink()
                            continue
                except OSError:
                    pass

                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for lock on {label}")
                time.sleep(backoff)
                backoff = min(0.05, backoff * 1.5)
            finally:
                if lock_fd is not None:
                    os.close(lock_fd)
                if acquired:
                    try:
                        if lock_path.exists():
                            lock_path.unlink()
                    except OSError:
                        pass

    def _merge_session_index(self, current: Any, incoming: Any) -> Dict[str, Any]:
        """Preserve concurrently-added index keys while letting incoming values win on conflicts."""
        merged = {"sessions": {}, "active_threads": {}, "patterns": {}}

        if isinstance(current, dict):
            for key in merged.keys():
                if isinstance(current.get(key), dict):
                    merged[key].update(current[key])

        if isinstance(incoming, dict):
            for key in merged.keys():
                if isinstance(incoming.get(key), dict):
                    merged[key].update(incoming[key])

        return merged

    def _merge_memory_index(self, current: Any, incoming: Any) -> Dict[str, Any]:
        """Union shared memory/session mappings so concurrent non-overlapping links survive."""
        merged = {"memory_to_sessions": {}, "session_memories": {}}

        for source in (current, incoming):
            if not isinstance(source, dict):
                continue
            for bucket in merged.keys():
                if not isinstance(source.get(bucket), dict):
                    continue
                for key, values in source[bucket].items():
                    existing_values = merged[bucket].setdefault(key, [])
                    if not isinstance(values, list):
                        continue
                    for value in values:
                        if value not in existing_values:
                            existing_values.append(value)

        return merged

    def _mutate_active_session(
        self,
        label: str,
        mutator: Callable[[Dict[str, Any], float], str],
    ) -> str:
        """Reload, mutate, and persist the active session under a cross-process file lock."""
        if not self.current_session_id:
            return "No active session. Start a session first with bb7_start_session."

        session_id = self.current_session_id
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return f"Session {session_id} not found."

        try:
            with self._lock:

                def action() -> Tuple[Optional[Dict[str, Any]], str]:
                    session = self._read_json_file(session_file, None, label)
                    if not isinstance(session, dict):
                        return (
                            None,
                            "Failed to load current session. Please start a new session.",
                        )

                    self.current_session_id = session_id
                    self.current_session = session
                    response = mutator(session, time.time())
                    self._write_json_atomic(session_file, session, label)
                    return session, response

                session, response = self._with_file_lock(session_file, label, action)
                if isinstance(session, dict):
                    self.current_session = session
                return response
        except Exception as e:
            self.logger.error(f"Failed to mutate {label}: {e}")
            return f"Error updating current session: {str(e)}"

    def _load_learned_patterns(self) -> Dict[str, Any]:
        """Load previously learned patterns from sessions"""
        return self._read_json_file(
            self.patterns_file,
            {
                "successful_workflows": [],
                "common_obstacles": [],
                "productivity_patterns": [],
                "decision_patterns": [],
                "learning_accelerators": [],
            },
            "learned patterns",
        )

    def _save_learned_patterns(self):
        """Save learned patterns to disk"""
        try:
            self._with_file_lock(
                self.patterns_file,
                "learned patterns",
                lambda: self._write_json_atomic(
                    self.patterns_file,
                    self.learned_patterns,
                    "learned patterns",
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to save learned patterns: {e}")

    def _load_session_intelligence(self) -> Dict[str, Any]:
        """Load session intelligence data"""
        return self._read_json_file(
            self.intelligence_file,
            {
                "session_success_predictors": {},
                "optimal_session_lengths": {},
                "focus_transition_patterns": {},
                "energy_level_correlations": {},
                "goal_achievement_factors": {},
            },
            "session intelligence",
        )

    def _save_session_intelligence(self):
        """Save session intelligence data"""
        try:
            self._with_file_lock(
                self.intelligence_file,
                "session intelligence",
                lambda: self._write_json_atomic(
                    self.intelligence_file,
                    self.session_intelligence,
                    "session intelligence",
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to save session intelligence: {e}")

    def _calculate_content_importance(self, content: str, context_type: str) -> float:
        """Calculate importance score for content based on various factors"""
        importance = 0.5  # Base importance
        content_lower = content.lower()

        # Context type multipliers
        context_multipliers = {
            "insight": 0.8,
            "decision": 0.7,
            "breakthrough": 0.9,
            "obstacle": 0.6,
            "solution": 0.8,
            "pattern": 0.7,
            "goal": 0.6,
        }

        importance *= context_multipliers.get(context_type, 1.0)

        # Keyword-based importance boosts
        for keyword_type, keywords in self.auto_memory_thresholds.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > 0:
                importance += min(matches * 0.1, 0.3)

        # Length and complexity factors
        if len(content) > 100:
            importance += 0.1
        if len(content) > 500:
            importance += 0.1

        # Technical content indicators
        tech_indicators = [
            "code",
            "function",
            "class",
            "method",
            "api",
            "database",
            "server",
            "client",
        ]
        tech_matches = sum(
            1 for indicator in tech_indicators if indicator in content_lower
        )
        if tech_matches > 0:
            importance += min(tech_matches * 0.05, 0.2)

        return min(importance, 1.0)

    def _is_memory_worthy(self, event_type: str, content: str) -> bool:
        """Determine if an event should be automatically stored in memory"""
        if not content or len(content.strip()) < 10:
            return False

        content_lower = content.lower()

        # Always capture high-value event types
        high_value_types = [
            "breakthrough",
            "major_decision",
            "critical_insight",
            "solution_found",
        ]
        if event_type in high_value_types:
            return True

        # Check for important keywords
        for keyword_type, keywords in self.auto_memory_thresholds.items():
            if any(keyword in content_lower for keyword in keywords):
                return True

        # Check for patterns we've learned are important
        for pattern in self.learned_patterns.get("learning_accelerators", []):
            if pattern.get("trigger_phrase", "").lower() in content_lower:
                return True

        # Length-based importance (longer descriptions often more important)
        if len(content) > 200:
            return True

        return False

    def _auto_capture_memory(
        self,
        event_type: str,
        content: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ):
        """Automatically create memory entries for significant events"""
        if not self.memory_tool or not self._is_memory_worthy(event_type, content):
            return

        try:
            # Generate intelligent memory key
            session_prefix = (
                f"session_{self.current_session_id[:8]}"
                if self.current_session_id
                else "global"
            )
            timestamp = int(time.time())
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            memory_key = f"{session_prefix}_{event_type}_{timestamp}_{content_hash}"

            # Calculate importance
            importance = self._calculate_content_importance(content, event_type)

            # Determine category
            category_mapping = {
                "insight": "insights",
                "decision": "decisions",
                "breakthrough": "insights",
                "obstacle": "solutions",
                "solution": "solutions",
                "pattern": "patterns",
                "goal": "goals",
            }
            category = category_mapping.get(event_type, "sessions")

            # Generate smart tags
            tags = [event_type, "auto_generated"]
            if self.current_session_id:
                tags.append(f"session_{self.current_session_id[:8]}")

            # Add contextual tags
            if additional_context:
                if additional_context.get("focus_areas"):
                    tags.extend(additional_context["focus_areas"][:3])
                if additional_context.get("energy_level"):
                    tags.append(f"energy_{additional_context['energy_level']}")

            # Enhanced content with context
            enhanced_content = content
            if additional_context:
                context_info = []
                if additional_context.get("session_goal"):
                    context_info.append(
                        f"Session Goal: {additional_context['session_goal']}"
                    )
                if additional_context.get("current_focus"):
                    context_info.append(
                        f"Focus: {', '.join(additional_context['current_focus'])}"
                    )
                if additional_context.get("timestamp"):
                    dt = datetime.fromtimestamp(additional_context["timestamp"])
                    context_info.append(f"Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

                if context_info:
                    enhanced_content += f"\n\nContext: {' | '.join(context_info)}"

            # Store in enhanced memory
            result = self.memory_tool.store(
                memory_key,
                enhanced_content,
                category=category,
                importance=importance,
                tags=tags,
            )

            self.logger.info(
                f"Auto-captured memory: {memory_key} (importance: {importance:.2f})"
            )

        except Exception as e:
            self.logger.error(f"Failed to auto-capture memory: {e}")

    def _analyze_session_patterns(self, session: Dict[str, Any]):
        """Analyze session for patterns and learning opportunities"""
        try:
            # Extract session metrics
            session_duration = session.get(
                "last_updated", session.get("created", 0)
            ) - session.get("created", 0)
            events = session.get("episodic", {}).get("events", [])
            insights = session.get("semantic", {}).get("key_insights", [])
            workflows = session.get("procedural", {}).get("workflows", [])

            # Identify successful patterns
            if (
                len(insights) > 3 and session_duration > 1800
            ):  # 30 minutes with multiple insights
                success_pattern = {
                    "pattern_type": "high_insight_session",
                    "duration": session_duration,
                    "insight_count": len(insights),
                    "goal": session.get("goal", ""),
                    "focus_areas": session.get("metadata", {}).get(
                        "attention_focus", []
                    ),
                    "energy_levels": self._extract_energy_progression(events),
                    "identified_at": time.time(),
                }

                self.learned_patterns["successful_workflows"].append(success_pattern)

                # Store pattern in memory
                self._auto_capture_memory(
                    "pattern",
                    f"Identified successful session pattern: {success_pattern['pattern_type']} - "
                    f"Duration {session_duration / 60:.1f}min with {len(insights)} insights",
                    {"pattern_data": success_pattern},
                )

            # Identify obstacle patterns
            obstacle_events = [
                e for e in events if e.get("type") in ["problem", "error", "obstacle"]
            ]
            if len(obstacle_events) > 2:
                obstacle_pattern = {
                    "pattern_type": "recurring_obstacles",
                    "obstacles": [e.get("description", "") for e in obstacle_events],
                    "session_context": session.get("goal", ""),
                    "identified_at": time.time(),
                }

                self.learned_patterns["common_obstacles"].append(obstacle_pattern)

        except Exception as e:
            self.logger.error(f"Error analyzing session patterns: {e}")

    def _extract_energy_progression(self, events: List[Dict[str, Any]]) -> List[str]:
        """Extract energy level progression from events"""
        energy_levels = []
        for event in events:
            if event.get("type") == "focus_shift" and event.get("details", {}).get(
                "energy"
            ):
                energy_levels.append(event["details"]["energy"])
        return energy_levels

    def bb7_start_session(
        self, goal: str, context: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> str:
        """Start a new enhanced cognitive session with intelligence"""
        with self._lock:
            session_id = str(uuid.uuid4())
            timestamp = time.time()

            # Analyze previous sessions for recommendations
            recommendations = self._generate_session_recommendations(goal)

            # Create enhanced session structure
            session = {
                "id": session_id,
                "created": timestamp,
                "last_updated": timestamp,
                "status": "active",
                "goal": goal,
                "context": context or "",
                "tags": tags or [],
                # Enhanced cognitive architecture
                "episodic": {
                    "events": [],
                    "timeline": [],
                    "achievements": [],
                    "obstacles": [],
                    "breakthroughs": [],
                },
                "semantic": {
                    "concepts": {},
                    "relationships": [],
                    "key_insights": [],
                    "decision_rationale": {},
                    "knowledge_connections": [],
                },
                "procedural": {
                    "workflows": [],
                    "commands_used": [],
                    "patterns_discovered": [],
                    "automation_opportunities": [],
                    "learned_shortcuts": [],
                },
                # Enhanced metadata
                "metadata": {
                    "environment_state": self._capture_environment_state(),
                    "attention_focus": [],
                    "energy_level": "high",
                    "momentum": "starting",
                    "predicted_success_factors": recommendations.get(
                        "success_factors", []
                    ),
                    "recommended_focus_duration": recommendations.get(
                        "optimal_duration", 60
                    ),
                    "similar_past_sessions": recommendations.get(
                        "similar_sessions", []
                    ),
                },
                # Intelligence tracking
                "intelligence": {
                    "auto_captured_memories": 0,
                    "pattern_matches": recommendations.get("pattern_matches", []),
                    "learning_opportunities": [],
                    "cross_session_connections": [],
                },
            }

            # Save session
            session_file = self.sessions_dir / f"{session_id}.json"
            self._with_file_lock(
                session_file,
                f"session {session_id}",
                lambda: self._write_json_atomic(
                    session_file,
                    session,
                    f"session {session_id}",
                ),
            )

            # Update index
            index = self._load_index()
            index["sessions"][session_id] = {
                "goal": goal,
                "created": timestamp,
                "status": "active",
                "tags": tags or [],
                "file": str(session_file),
                "predicted_success": recommendations.get("success_probability", 0.5),
            }
            self._save_index(index)

            # Set as current session
            self.current_session_id = session_id
            self.current_session = session

            # Auto-capture session start
            self._auto_capture_memory(
                "session_start",
                f"Started new session: {goal}" + (f" - {context}" if context else ""),
                {
                    "session_goal": goal,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "recommendations": recommendations,
                },
            )

            # Proactive memory surfacing - surface relevant memories for this session context
            if self.memory_tool and hasattr(self.memory_tool, "surface_context"):
                try:
                    surfacing_context = f"Current session goal: {goal}"
                    if context:
                        surfacing_context += f" Context: {context}"
                    if tags:
                        surfacing_context += f" Tags: {', '.join(tags)}"

                    memory_context = self.memory_tool.surface_context(
                        surfacing_context, max_results=3
                    )
                    if (
                        memory_context
                        and not memory_context.startswith("No relevant")
                        and not memory_context.startswith("Error")
                    ):
                        session["proactive_memories"] = memory_context
                        # Update session file with proactive memories
                        self._with_file_lock(
                            session_file,
                            f"session {session_id}",
                            lambda: self._write_json_atomic(
                                session_file,
                                session,
                                f"session {session_id}",
                            ),
                        )
                except Exception as surfacing_error:
                    self.logger.error(
                        "Proactive memory surfacing failed for session %s: %s",
                        session_id,
                        surfacing_error,
                    )

            # Format response with intelligence
            response = f"Enhanced Session Started: {goal}\n"
            response += f"Session ID: {session_id}\n"

            if recommendations.get("success_factors"):
                response += "\nSuccess Factors (based on past sessions):\n"
                for factor in recommendations["success_factors"][:3]:
                    response += f"  - {factor}\n"

            if recommendations.get("optimal_duration"):
                response += (
                    f"\nRecommended Focus Duration: {recommendations['optimal_duration']} minutes\n"
                )

            if recommendations.get("similar_sessions"):
                response += (
                    f"\nFound {len(recommendations['similar_sessions'])} similar past sessions for reference\n"
                )

            response += "\nAuto-memory formation enabled - insights will be captured automatically."

            # Include proactive memories in response if available
            if session.get("proactive_memories"):
                response += "\n\nRelevant memories from previous sessions:\n"
                # Extract key lines from memory surfacing output
                mem_lines = session["proactive_memories"].split("\n")
                for line in mem_lines[1:]:  # Skip header
                    if line.strip():
                        response += f"  {line}\n"

            self.logger.info(f"Started enhanced session: {session_id}")
            return response

    def _generate_session_recommendations(self, goal: str) -> Dict[str, Any]:
        """Generate intelligent recommendations based on past sessions"""
        recommendations = {
            "success_factors": [],
            "optimal_duration": 60,
            "similar_sessions": [],
            "pattern_matches": [],
            "success_probability": 0.5,
        }

        try:
            # Analyze goal for keywords and context
            goal_words = set(goal.lower().split())

            # Find similar past sessions
            index = self._load_index()
            similar_sessions = []

            for session_id, session_info in index.get("sessions", {}).items():
                past_goal = session_info.get("goal", "").lower()
                past_words = set(past_goal.split())

                # Calculate similarity
                intersection = goal_words & past_words
                if (
                    intersection
                    and len(intersection) / len(goal_words | past_words) > 0.3
                ):
                    similar_sessions.append(
                        {
                            "session_id": session_id,
                            "goal": session_info.get("goal", ""),
                            "similarity": len(intersection)
                            / len(goal_words | past_words),
                        }
                    )

            recommendations["similar_sessions"] = sorted(
                similar_sessions, key=lambda x: x["similarity"], reverse=True
            )[:5]

            # Extract success factors from learned patterns
            for pattern in self.learned_patterns.get("successful_workflows", []):
                if any(word in pattern.get("goal", "").lower() for word in goal_words):
                    recommendations["success_factors"].extend(
                        pattern.get("focus_areas", [])
                    )
                    if pattern.get("duration"):
                        recommendations["optimal_duration"] = max(
                            recommendations["optimal_duration"],
                            pattern["duration"] // 60,
                        )

            # Remove duplicates and limit
            recommendations["success_factors"] = list(
                set(recommendations["success_factors"])
            )[:5]

            # Calculate success probability based on similar sessions and patterns
            if similar_sessions:
                recommendations["success_probability"] = min(
                    0.9, 0.5 + len(similar_sessions) * 0.1
                )

        except Exception as e:
            self.logger.error(f"Error generating session recommendations: {e}")

        return recommendations

    def bb7_log_event(
        self,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Enhanced event logging with auto-memory formation"""

        def mutate(session: Dict[str, Any], timestamp: float) -> str:
            timestamp = time.time()
            event = {
                "timestamp": timestamp,
                "type": event_type,
                "description": description,
                "details": details or {},
                "auto_analyzed": False,
            }

            # Enhanced event categorization
            if event_type in ["breakthrough", "major_insight", "critical_discovery"]:
                session["episodic"]["breakthroughs"].append(event)
                # Auto-capture breakthrough
                self._auto_capture_memory(
                    "breakthrough",
                    description,
                    {
                        "session_goal": session.get("goal"),
                        "current_focus": session.get("metadata", {}).get(
                            "attention_focus", []
                        ),
                        "timestamp": timestamp,
                    },
                )
                event["auto_analyzed"] = True

            elif event_type in ["obstacle", "problem", "error", "blocker"]:
                session["episodic"]["obstacles"].append(event)

            elif event_type in ["achievement", "milestone", "completion"]:
                session["episodic"]["achievements"].append(event)
                # Auto-capture achievement
                self._auto_capture_memory(
                    "achievement",
                    description,
                    {"session_goal": session.get("goal"), "timestamp": timestamp},
                )
                event["auto_analyzed"] = True

            # Add to main event log
            session["episodic"]["events"].append(event)
            session["episodic"]["timeline"].append(
                {"time": timestamp, "event": event_type, "summary": description[:100]}
            )

            # Intelligent event analysis
            if self._should_auto_capture(event_type, description):
                self._auto_capture_memory(
                    event_type,
                    description,
                    {
                        "session_goal": session.get("goal"),
                        "current_focus": session.get("metadata", {}).get(
                            "attention_focus", []
                        ),
                        "energy_level": session.get("metadata", {}).get("energy_level"),
                        "timestamp": timestamp,
                    },
                )
                event["auto_analyzed"] = True
                session["intelligence"]["auto_captured_memories"] += 1

            session["last_updated"] = timestamp

            response = f"📝 Event logged: {description}"
            if event["auto_analyzed"]:
                response += f"\n🧠 Auto-captured in memory (total: {session['intelligence']['auto_captured_memories']})"

            self.logger.info(f"Enhanced event logged: {event_type} - {description}")
            return response

        return self._mutate_active_session(
            f"current session {self.current_session_id}",
            mutate,
        )

    def _should_auto_capture(self, event_type: str, description: str) -> bool:
        """Enhanced logic for determining auto-capture worthiness"""
        # Always capture certain event types
        auto_capture_types = [
            "breakthrough",
            "major_insight",
            "critical_discovery",
            "achievement",
            "milestone",
            "decision",
            "solution",
        ]
        if event_type in auto_capture_types:
            return True

        # Use existing memory worthiness logic
        return self._is_memory_worthy(event_type, description)

    def bb7_capture_insight(
        self, insight: str, concept: str, relationships: Optional[List[str]] = None
    ) -> str:
        """Enhanced insight capture with auto-memory and relationship tracking"""

        def mutate(session: Dict[str, Any], timestamp: float) -> str:
            timestamp = time.time()

            # Enhanced semantic memory storage
            insight_entry = {
                "timestamp": timestamp,
                "insight": insight,
                "concept": concept,
                "relationships": relationships or [],
                "confidence": self._calculate_insight_confidence(insight, concept),
                "session_context": {
                    "goal": session.get("goal"),
                    "focus_areas": session.get("metadata", {}).get(
                        "attention_focus", []
                    ),
                    "energy_level": session.get("metadata", {}).get("energy_level"),
                },
            }

            session["semantic"]["key_insights"].append(insight_entry)

            # Update concept network
            if concept not in session["semantic"]["concepts"]:
                session["semantic"]["concepts"][concept] = {
                    "defined": timestamp,
                    "insights": [],
                    "related_to": relationships or [],
                    "importance_score": 0.5,
                    "evolution": [],
                }

            concept_data = session["semantic"]["concepts"][concept]
            concept_data["insights"].append(insight)
            concept_data["importance_score"] = min(
                1.0, concept_data["importance_score"] + 0.1
            )
            concept_data["evolution"].append(
                {"timestamp": timestamp, "type": "insight_added", "content": insight}
            )

            # Add enhanced relationships
            if relationships:
                for related_concept in relationships:
                    relationship = {
                        "from": concept,
                        "to": related_concept,
                        "timestamp": timestamp,
                        "context": insight,
                        "strength": self._calculate_relationship_strength(
                            concept, related_concept, insight
                        ),
                    }
                    session["semantic"]["relationships"].append(relationship)

                    # Cross-connect concepts
                    session["semantic"]["knowledge_connections"].append(
                        {
                            "concepts": [concept, related_concept],
                            "connection_type": "insight_based",
                            "evidence": insight,
                            "timestamp": timestamp,
                        }
                    )

            # Auto-capture high-value insights
            importance = self._calculate_content_importance(insight, "insight")
            if importance > 0.6:
                self._auto_capture_memory(
                    "insight",
                    f"💡 {concept}: {insight}",
                    {
                        "concept": concept,
                        "relationships": relationships,
                        "session_goal": session.get("goal"),
                        "confidence": insight_entry["confidence"],
                        "timestamp": timestamp,
                    },
                )
                session["intelligence"]["auto_captured_memories"] += 1

            session["last_updated"] = timestamp

            response = f"💡 Insight captured: {insight}"
            if importance > 0.6:
                response += f"\n🧠 Auto-stored in memory (importance: {importance:.2f})"
            if relationships:
                response += f"\n🔗 Connected to: {', '.join(relationships)}"

            self.logger.info(f"Enhanced insight captured: {concept} - {insight}")
            return response

        return self._mutate_active_session(
            f"current session {self.current_session_id}",
            mutate,
        )

    def _calculate_insight_confidence(self, insight: str, concept: str) -> float:
        """Calculate confidence score for an insight"""
        confidence = 0.5

        # Length and detail factors
        if len(insight) > 50:
            confidence += 0.1
        if len(insight) > 150:
            confidence += 0.1

        # Specificity indicators
        specific_words = [
            "because",
            "due to",
            "results in",
            "causes",
            "leads to",
            "enables",
        ]
        if any(word in insight.lower() for word in specific_words):
            confidence += 0.2

        # Evidence indicators
        evidence_words = ["tested", "verified", "confirmed", "observed", "measured"]
        if any(word in insight.lower() for word in evidence_words):
            confidence += 0.2

        return min(confidence, 1.0)

    def _calculate_relationship_strength(
        self, concept1: str, concept2: str, context: str
    ) -> float:
        """Calculate strength of relationship between concepts"""
        strength = 0.5

        # Co-occurrence in context
        if concept1.lower() in context.lower() and concept2.lower() in context.lower():
            strength += 0.3

        # Strong relationship indicators
        strong_indicators = [
            "causes",
            "enables",
            "requires",
            "depends on",
            "results in",
        ]
        if any(indicator in context.lower() for indicator in strong_indicators):
            strength += 0.3

        return min(strength, 1.0)

    def bb7_get_session_insights(self, session_id: Optional[str] = None) -> str:
        """Get comprehensive insights about a session"""
        target_session_id = session_id or self.current_session_id

        if not target_session_id:
            return "No session specified and no active session"

        session_file = self.sessions_dir / f"{target_session_id}.json"
        if not session_file.exists():
            return f"Session {target_session_id} not found"

        try:
            session = self._read_json_file(
                session_file,
                None,
                f"session insights {target_session_id}",
            )
            if not isinstance(session, dict):
                return f"Failed to load session {target_session_id}"

            insights = []
            insights.append(f"🧠 Session Intelligence Report: {target_session_id[:8]}")
            insights.append("=" * 60)

            # Basic metrics
            goal = session.get("goal", "No goal specified")
            created = datetime.fromtimestamp(session.get("created", 0))
            duration = session.get(
                "last_updated", session.get("created", 0)
            ) - session.get("created", 0)

            insights.append(f"🎯 Goal: {goal}")
            insights.append(f"📅 Started: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            insights.append(f"⏱️ Duration: {duration / 60:.1f} minutes")

            # Intelligence metrics
            intelligence = session.get("intelligence", {})
            auto_memories = intelligence.get("auto_captured_memories", 0)
            insights.append(f"🧠 Auto-captured memories: {auto_memories}")

            # Event analysis
            events = session.get("episodic", {}).get("events", [])
            breakthroughs = session.get("episodic", {}).get("breakthroughs", [])
            obstacles = session.get("episodic", {}).get("obstacles", [])
            achievements = session.get("episodic", {}).get("achievements", [])

            insights.append(f"\n📊 Event Summary:")
            insights.append(f"  • Total events: {len(events)}")
            insights.append(f"  • Breakthroughs: {len(breakthroughs)}")
            insights.append(f"  • Obstacles: {len(obstacles)}")
            insights.append(f"  • Achievements: {len(achievements)}")

            # Concept network
            concepts = session.get("semantic", {}).get("concepts", {})
            key_insights = session.get("semantic", {}).get("key_insights", [])

            if concepts:
                insights.append(f"\n🧭 Concept Network ({len(concepts)} concepts):")
                # Sort concepts by importance
                sorted_concepts = sorted(
                    concepts.items(),
                    key=lambda x: x[1].get("importance_score", 0.5),
                    reverse=True,
                )
                for concept, data in sorted_concepts[:5]:
                    importance = data.get("importance_score", 0.5)
                    insight_count = len(data.get("insights", []))
                    insights.append(
                        f"  • {concept}: {insight_count} insights (importance: {importance:.2f})"
                    )

            # Workflow patterns
            workflows = session.get("procedural", {}).get("workflows", [])
            if workflows:
                insights.append(f"\n⚙️ Learned Workflows ({len(workflows)}):")
                for workflow in workflows[:3]:
                    name = workflow.get("name", "Unnamed")
                    steps = len(workflow.get("steps", []))
                    frequency = workflow.get("frequency", 1)
                    insights.append(f"  • {name}: {steps} steps (used {frequency}x)")

            # Success indicators
            if duration > 1800 and len(key_insights) > 2:  # 30 min with insights
                insights.append(f"\n✨ Success Indicators:")
                insights.append(f"  • Sustained focus ({duration / 60:.1f} minutes)")
                insights.append(
                    f"  • High insight generation ({len(key_insights)} insights)"
                )
                if auto_memories > 3:
                    insights.append(
                        f"  • Rich auto-memory formation ({auto_memories} entries)"
                    )

            return "\n".join(insights)

        except Exception as e:
            self.logger.error(f"Error generating session insights: {e}")
            return f"Error generating session insights: {str(e)}"

    def bb7_cross_session_analysis(self, days_back: int = 30) -> str:
        """Analyze patterns across multiple sessions"""
        try:
            cutoff_time = time.time() - (days_back * 24 * 60 * 60)
            index = self._load_index()

            recent_sessions = []
            for session_id, session_info in index.get("sessions", {}).items():
                if session_info.get("created", 0) > cutoff_time:
                    session_file = self.sessions_dir / f"{session_id}.json"
                    if session_file.exists():
                        session_data = self._read_json_file(
                            session_file,
                            None,
                            f"session {session_id}",
                        )
                        if isinstance(session_data, dict):
                            recent_sessions.append(session_data)

            if not recent_sessions:
                return f"No sessions found in the last {days_back} days"

            analysis = []
            analysis.append(f"🔍 Cross-Session Analysis ({days_back} days)")
            analysis.append("=" * 50)
            analysis.append(f"📊 Analyzed {len(recent_sessions)} sessions\n")

            # Goal pattern analysis
            goals = [s.get("goal", "") for s in recent_sessions]
            goal_words = []
            for goal in goals:
                goal_words.extend(goal.lower().split())

            common_goal_words = Counter(goal_words).most_common(5)
            analysis.append("🎯 Common Goal Themes:")
            for word, count in common_goal_words:
                if len(word) > 3:  # Skip short words
                    analysis.append(f"  • {word}: {count} sessions")

            # Success pattern analysis
            successful_sessions = []
            for session in recent_sessions:
                duration = session.get("last_updated", 0) - session.get("created", 0)
                insights = len(session.get("semantic", {}).get("key_insights", []))
                auto_memories = session.get("intelligence", {}).get(
                    "auto_captured_memories", 0
                )

                # Define success criteria
                success_score = 0
                if duration > 1800:  # > 30 minutes
                    success_score += 1
                if insights > 2:  # Multiple insights
                    success_score += 2
                if auto_memories > 3:  # Rich auto-capture
                    success_score += 1

                if success_score >= 3:
                    successful_sessions.append(
                        {
                            "session": session,
                            "score": success_score,
                            "duration": duration,
                            "insights": insights,
                        }
                    )

            analysis.append(f"\n✨ Success Analysis:")
            analysis.append(
                f"  • Successful sessions: {len(successful_sessions)}/{len(recent_sessions)}"
            )

            if successful_sessions:
                avg_duration = sum(s["duration"] for s in successful_sessions) / len(
                    successful_sessions
                )
                avg_insights = sum(s["insights"] for s in successful_sessions) / len(
                    successful_sessions
                )

                analysis.append(
                    f"  • Average successful duration: {avg_duration / 60:.1f} minutes"
                )
                analysis.append(f"  • Average insights per success: {avg_insights:.1f}")

                # Extract success factors
                success_factors = []
                for s in successful_sessions:
                    focus_areas = (
                        s["session"].get("metadata", {}).get("attention_focus", [])
                    )
                    success_factors.extend(focus_areas)

                if success_factors:
                    common_factors = Counter(success_factors).most_common(3)
                    analysis.append(f"  • Top success factors:")
                    for factor, count in common_factors:
                        analysis.append(f"    - {factor} ({count} sessions)")

            # Concept evolution analysis
            all_concepts = {}
            for session in recent_sessions:
                concepts = session.get("semantic", {}).get("concepts", {})
                for concept, data in concepts.items():
                    if concept not in all_concepts:
                        all_concepts[concept] = []
                    all_concepts[concept].append(
                        {
                            "session_id": session.get("id"),
                            "importance": data.get("importance_score", 0.5),
                            "insights": len(data.get("insights", [])),
                        }
                    )

            # Find evolving concepts (appearing in multiple sessions)
            evolving_concepts = {k: v for k, v in all_concepts.items() if len(v) > 1}

            if evolving_concepts:
                analysis.append(f"\n🧭 Evolving Concepts ({len(evolving_concepts)}):")
                for concept, occurrences in list(evolving_concepts.items())[:5]:
                    total_importance = sum(o["importance"] for o in occurrences)
                    analysis.append(
                        f"  • {concept}: {len(occurrences)} sessions (importance: {total_importance:.2f})"
                    )

            return "\n".join(analysis)

        except Exception as e:
            self.logger.error(f"Error in cross-session analysis: {e}")
            return f"Error in cross-session analysis: {str(e)}"

    def get_tools(self) -> Dict[str, Callable]:
        """Return all available enhanced session tools"""
        return {
            # Core enhanced session management
            "bb7_start_session": {
                "function": self.bb7_start_session,
                "description": "Start a new enhanced cognitive session with intelligence.",
                "parameters": [
                    {
                        "name": "goal",
                        "description": "The goal of the session.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "context",
                        "description": "Additional context for the session.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "tags",
                        "description": "A list of tags for the session.",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                    },
                ],
            },
            "bb7_log_event": {
                "function": self.bb7_log_event,
                "description": "Enhanced event logging with auto-memory formation.",
                "parameters": [
                    {
                        "name": "event_type",
                        "description": "The type of event to log.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "description",
                        "description": "A description of the event.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "details",
                        "description": "A dictionary of additional details about the event.",
                        "type": "object",
                        "required": False,
                    },
                ],
            },
            "bb7_capture_insight": {
                "function": self.bb7_capture_insight,
                "description": "Enhanced insight capture with auto-memory and relationship tracking.",
                "parameters": [
                    {
                        "name": "insight",
                        "description": "The insight to capture.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "concept",
                        "description": "The concept the insight is related to.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "relationships",
                        "description": "A list of related concepts.",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                    },
                ],
            },
            "bb7_record_workflow": {
                "function": self.bb7_record_workflow,
                "description": "Record a procedural workflow or pattern.",
                "parameters": [
                    {
                        "name": "workflow_name",
                        "description": "The name of the workflow.",
                        "type": "string",
                        "required": True,
                    },
                    {
                        "name": "steps",
                        "description": "A list of steps in the workflow.",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": True,
                    },
                    {
                        "name": "context",
                        "description": "Additional context for the workflow.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_update_focus": {
                "function": self.bb7_update_focus,
                "description": "Update current attention focus and energy state.",
                "parameters": [
                    {
                        "name": "focus_areas",
                        "description": "A list of areas to focus on.",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": True,
                    },
                    {
                        "name": "energy_level",
                        "description": "The current energy level.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "momentum",
                        "description": "The current momentum.",
                        "type": "string",
                        "required": False,
                    },
                ],
            },
            "bb7_pause_session": {
                "function": self.bb7_pause_session,
                "description": "Pause the current session.",
                "parameters": [
                    {
                        "name": "reason",
                        "description": "The reason for pausing the session.",
                        "type": "string",
                        "required": False,
                    }
                ],
            },
            "bb7_resume_session": {
                "function": self.bb7_resume_session,
                "description": "Resume a paused session.",
                "parameters": [
                    {
                        "name": "session_id",
                        "description": "The ID of the session to resume.",
                        "type": "string",
                        "required": True,
                    }
                ],
            },
            "bb7_list_sessions": {
                "function": self.bb7_list_sessions,
                "description": "List all sessions with optional status filter.",
                "parameters": [
                    {
                        "name": "status",
                        "description": "The status to filter sessions by.",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "limit",
                        "description": "The maximum number of sessions to return.",
                        "type": "number",
                        "required": False,
                    },
                ],
            },
            "bb7_get_session_summary": {
                "function": self.bb7_get_session_summary,
                "description": "Get a detailed summary of a specific session.",
                "parameters": [
                    {
                        "name": "session_id",
                        "description": "The ID of the session to get the summary for.",
                        "type": "string",
                        "required": True,
                    }
                ],
            },
            # Enhanced intelligence features
            "bb7_get_session_insights": {
                "function": self.bb7_get_session_insights,
                "description": "Get comprehensive insights about a session.",
                "parameters": [
                    {
                        "name": "session_id",
                        "description": "The ID of the session to get insights for.",
                        "type": "string",
                        "required": False,
                    }
                ],
            },
            "bb7_cross_session_analysis": {
                "function": lambda days_back=30: self.bb7_cross_session_analysis(
                    days_back
                ),
                "description": "Analyze patterns across multiple sessions.",
                "parameters": [
                    {
                        "name": "days_back",
                        "description": "The number of days back to analyze.",
                        "type": "number",
                        "required": False,
                    }
                ],
            },
            "bb7_session_recommendations": {
                "function": lambda goal: json.dumps(
                    self._generate_session_recommendations(goal), indent=2
                ),
                "description": "Generate intelligent recommendations based on past sessions.",
                "parameters": [
                    {
                        "name": "goal",
                        "description": "The goal of the new session.",
                        "type": "string",
                        "required": True,
                    }
                ],
            },
            "bb7_learned_patterns": {
                "function": lambda: json.dumps(self.learned_patterns, indent=2),
                "description": "Get the learned patterns from sessions.",
                "parameters": [],
            },
            "bb7_session_intelligence": {
                "function": lambda: json.dumps(self.session_intelligence, indent=2),
                "description": "Get the session intelligence data.",
                "parameters": [],
            },
            # Memory integration
            "bb7_link_memory_to_session": {
                "function": self.bb7_link_memory_to_session,
                "description": "Link a memory key to the current session.",
                "parameters": [
                    {
                        "name": "memory_key",
                        "description": "The key of the memory to link.",
                        "type": "string",
                        "required": True,
                    }
                ],
            },
            "bb7_auto_memory_stats": {
                "function": lambda: (
                    f"Auto-captured memories this session: {self.current_session.get('intelligence', {}).get('auto_captured_memories', 0) if self.current_session else 0}"
                ),
                "description": "Get the statistics of auto-captured memories for the current session.",
                "parameters": [],
            },
        }

    def _load_index(self) -> Dict[str, Any]:
        """Load the session index"""
        return self._read_json_file(
            self.index_file,
            {"sessions": {}, "active_threads": {}, "patterns": {}},
            "session index",
        )

    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save the session index"""
        try:
            self._with_file_lock(
                self.index_file,
                "session index",
                lambda: self._write_json_atomic(
                    self.index_file,
                    self._merge_session_index(
                        self._read_json_file(
                            self.index_file,
                            {"sessions": {}, "active_threads": {}, "patterns": {}},
                            "session index",
                        ),
                        index,
                    ),
                    "session index",
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to save session index: {e}")

    def _capture_environment_state(self) -> Dict[str, Any]:
        """Capture current development environment state"""
        import os, subprocess

        state = {
            "timestamp": time.time(),
            "working_directory": os.getcwd(),
        }
        # Git state with proper error handling to prevent hanging
        try:
            git_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2,
                shell=False,
                check=False,
            )
            if git_branch.returncode == 0 and git_branch.stdout.strip():
                state["git"] = {"branch": git_branch.stdout.strip()}
            else:
                state["git"] = {"status": "not_in_git_repo"}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            state["git"] = {"status": "git_unavailable", "reason": str(e)}
        except Exception as e:
            state["git"] = {"status": "error", "reason": str(e)}
        return state

    def _load_current_session(self) -> None:
        """Load the current session from disk"""
        if not self.current_session_id:
            return

        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        self.current_session = self._read_json_file(
            session_file,
            None,
            f"current session {self.current_session_id}",
        )

    def _save_current_session(self) -> None:
        """Save the current session to disk"""
        if not self.current_session_id or not self.current_session:
            return

        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        try:
            self._with_file_lock(
                session_file,
                f"current session {self.current_session_id}",
                lambda: self._write_json_atomic(
                    session_file,
                    self.current_session,
                    f"current session {self.current_session_id}",
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to save current session: {e}")

    def _load_memory_index(self) -> Dict[str, Any]:
        """Load the memory-session mapping"""
        memory_index_file = self.sessions_dir / "memory_index.json"
        return self._read_json_file(
            memory_index_file,
            {"memory_to_sessions": {}, "session_memories": {}},
            "memory index",
        )

    def _save_memory_index(self, memory_index: Dict[str, Any]) -> None:
        """Save the memory-session mapping"""
        memory_index_file = self.sessions_dir / "memory_index.json"
        try:
            self._with_file_lock(
                memory_index_file,
                "memory index",
                lambda: self._write_json_atomic(
                    memory_index_file,
                    self._merge_memory_index(
                        self._read_json_file(
                            memory_index_file,
                            {"memory_to_sessions": {}, "session_memories": {}},
                            "memory index",
                        ),
                        memory_index,
                    ),
                    "memory index",
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to save memory index: {e}")

    def bb7_record_workflow(
        self, workflow_name: str, steps: List[str], context: Optional[str] = None
    ) -> str:
        """Record a procedural workflow or pattern"""

        def mutate(session: Dict[str, Any], timestamp: float) -> str:
            timestamp = time.time()
            workflow = {
                "timestamp": timestamp,
                "name": workflow_name,
                "steps": steps,
                "context": context or "",
                "frequency": 1,
            }

            # Check if similar workflow exists
            existing = None
            for i, existing_workflow in enumerate(session["procedural"]["workflows"]):
                if existing_workflow["name"] == workflow_name:
                    existing = i
                    break

            if existing is not None:
                # Update existing workflow
                session["procedural"]["workflows"][existing]["frequency"] += 1
                session["procedural"]["workflows"][existing]["last_used"] = timestamp
                session["procedural"]["workflows"][existing]["steps"] = steps
            else:
                # Add new workflow
                session["procedural"]["workflows"].append(workflow)

            session["last_updated"] = timestamp

            self.logger.info(f"Recorded workflow: {workflow_name}")
            return f"⚙️ Workflow recorded: {workflow_name} ({len(steps)} steps)"

        return self._mutate_active_session(
            f"current session {self.current_session_id}",
            mutate,
        )

    def bb7_update_focus(
        self,
        focus_areas: List[str],
        energy_level: str = "medium",
        momentum: str = "steady",
    ) -> str:
        """Update current attention focus and energy state"""

        def mutate(session: Dict[str, Any], timestamp: float) -> str:
            timestamp = time.time()
            session["metadata"]["attention_focus"] = focus_areas
            session["metadata"]["energy_level"] = energy_level
            session["metadata"]["momentum"] = momentum
            session["metadata"]["focus_updated"] = timestamp
            session["last_updated"] = timestamp

            # Log as event
            session["episodic"]["events"].append(
                {
                    "timestamp": timestamp,
                    "type": "focus_shift",
                    "description": f"Focus shifted to: {', '.join(focus_areas)}",
                    "details": {"energy": energy_level, "momentum": momentum},
                }
            )

            return f"🎯 Focus updated: {', '.join(focus_areas)} (Energy: {energy_level}, Momentum: {momentum})"

        return self._mutate_active_session(
            f"current session {self.current_session_id}",
            mutate,
        )

    def bb7_pause_session(self, reason: Optional[str] = None) -> str:
        """Pause the current session"""
        session_id = self.current_session_id
        if not session_id:
            return "No active session to pause."

        def mutate(session: Dict[str, Any], timestamp: float) -> str:
            timestamp = time.time()
            session["status"] = "paused"
            session["paused_at"] = timestamp
            session["pause_reason"] = reason or "Manual pause"
            session["last_updated"] = timestamp

            # Capture final environment state
            session["metadata"]["pause_environment"] = self._capture_environment_state()

            # Log pause event
            session["episodic"]["events"].append(
                {
                    "timestamp": timestamp,
                    "type": "session_paused",
                    "description": f"Session paused: {reason or 'Manual pause'}",
                    "details": {"environment_captured": True},
                }
            )

            return f"⏸️ Session paused: {reason or 'Manual pause'}"

        response = self._mutate_active_session(
            f"current session {session_id}",
            mutate,
        )
        if not response.startswith("⏸️ Session paused:"):
            return response

        with self._lock:
            index = self._load_index()
            if session_id in index["sessions"]:
                index["sessions"][session_id]["status"] = "paused"
            self._save_index(index)

            self.current_session_id = None
            self.current_session = None

        self.logger.info(f"Paused session: {session_id}")
        return response

    def bb7_resume_session(self, session_id: str) -> str:
        """Resume a paused session"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return f"Session {session_id} not found."

        try:
            with self._lock:

                def action() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
                    session = self._read_json_file(
                        session_file,
                        None,
                        f"session {session_id}",
                    )
                    if not isinstance(session, dict):
                        return None, f"Failed to load session {session_id}."

                    if session.get("status") != "paused":
                        return (
                            session,
                            f"Session {session_id} is not paused (status: {session.get('status', 'unknown')}).",
                        )

                    timestamp = time.time()
                    session["status"] = "active"
                    session["resumed_at"] = timestamp
                    session["last_updated"] = timestamp
                    self._write_json_atomic(
                        session_file, session, f"session {session_id}"
                    )
                    return session, None

                session, error = self._with_file_lock(
                    session_file,
                    f"session {session_id}",
                    action,
                )
                if error:
                    return error
                if not isinstance(session, dict):
                    return f"Failed to load session {session_id}."

                self.current_session_id = session_id
                self.current_session = session

                index = self._load_index()
                if session_id in index["sessions"]:
                    index["sessions"][session_id]["status"] = "active"
                self._save_index(index)

            self.logger.info(f"Resumed session: {session_id}")
            return f"▶️ Session resumed: {session['goal']}"
        except Exception as e:
            self.logger.error(f"Failed to resume session {session_id}: {e}")
            return f"Error resuming session {session_id}: {str(e)}"

    def bb7_list_sessions(self, status: Optional[str] = None, limit: int = 20) -> str:
        """List all sessions with optional status filter"""
        index = self._load_index()
        sessions = index.get("sessions", {})

        if not sessions:
            return "No sessions found."

        # Filter by status if specified
        if status:
            filtered_sessions = {
                k: v for k, v in sessions.items() if v.get("status") == status
            }
        else:
            filtered_sessions = sessions

        if not filtered_sessions:
            return f"No sessions found with status '{status}'."

        # Sort by creation time (newest first)
        sorted_sessions = sorted(
            filtered_sessions.items(),
            key=lambda x: x[1].get("created", 0),
            reverse=True,
        )

        result = []
        result.append(f"📊 Sessions ({len(sorted_sessions)} total):\n")

        for session_id, session_info in sorted_sessions[:limit]:
            created = datetime.fromtimestamp(session_info.get("created", 0))
            status_emoji = {"active": "🟢", "paused": "⏸️", "completed": "✅"}.get(
                session_info.get("status", "unknown"), "❓"
            )

            result.append(
                f"{status_emoji} {session_id[:8]}... - {session_info.get('goal', 'No goal')}"
            )
            result.append(f"    Created: {created.strftime('%Y-%m-%d %H:%M')}")

            tags = session_info.get("tags", [])
            if tags:
                result.append(f"    Tags: {', '.join(tags)}")

        if len(sorted_sessions) > limit:
            result.append(f"\n... and {len(sorted_sessions) - limit} more sessions")

        return "\n".join(result)

    def bb7_get_session_summary(self, session_id: str) -> str:
        """Get a detailed summary of a specific session"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return f"Session {session_id} not found."

        session = self._read_json_file(
            session_file,
            None,
            f"session summary {session_id}",
        )
        if not isinstance(session, dict):
            return f"Failed to load session {session_id}."

        # Build comprehensive summary
        summary = []

        # Header
        created = datetime.fromtimestamp(session.get("created", 0))
        updated = datetime.fromtimestamp(session.get("last_updated", 0))

        summary.append(f"📋 Session Summary: {session_id}")
        summary.append(f"🎯 Goal: {session.get('goal', 'Not specified')}")
        summary.append(f"📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"🔄 Last Updated: {updated.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"📊 Status: {session.get('status', 'Unknown')}")

        tags = session.get("tags", [])
        if tags:
            summary.append(f"🏷️ Tags: {', '.join(tags)}")

        # Episodic Memory
        episodic = session.get("episodic", {})
        events = episodic.get("events", [])
        if events:
            summary.append(f"\n📝 Events ({len(events)} total):")
            for event in events[-10:]:  # Last 10 events
                event_time = datetime.fromtimestamp(event["timestamp"]).strftime(
                    "%H:%M"
                )
                summary.append(f"  • {event_time}: {event['description']}")

        # Semantic Memory
        semantic = session.get("semantic", {})
        concepts = semantic.get("concepts", {})
        insights = semantic.get("key_insights", [])

        if concepts:
            summary.append(f"\n🧠 Concepts ({len(concepts)}):")
            for concept, data in list(concepts.items())[:5]:
                summary.append(
                    f"  • {concept}: {len(data.get('insights', []))} insights"
                )

        if insights:
            summary.append(f"\n💡 Key Insights ({len(insights)}):")
            for insight in insights[-5:]:
                summary.append(f"  • {insight['insight']}")

        # Procedural Memory
        procedural = session.get("procedural", {})
        workflows = procedural.get("workflows", [])

        if workflows:
            summary.append(f"\n⚙️ Workflows ({len(workflows)}):")
            for workflow in workflows:
                freq = workflow.get("frequency", 1)
                summary.append(
                    f"  • {workflow['name']}: {len(workflow['steps'])} steps (used {freq}x)"
                )

        # Current Focus
        metadata = session.get("metadata", {})
        focus = metadata.get("attention_focus", [])
        if focus:
            energy = metadata.get("energy_level", "unknown")
            momentum = metadata.get("momentum", "unknown")
            summary.append(f"\n🎯 Current Focus: {', '.join(focus)}")
            summary.append(f"⚡ Energy: {energy}, Momentum: {momentum}")

        return "\n".join(summary)

    def bb7_link_memory_to_session(self, memory_key: str) -> str:
        """Link a memory key to the current session"""
        if not self.current_session_id:
            return "No active session to link memory to."

        # Update memory index
        memory_index = self._load_memory_index()

        if memory_key not in memory_index["memory_to_sessions"]:
            memory_index["memory_to_sessions"][memory_key] = []

        if (
            self.current_session_id
            not in memory_index["memory_to_sessions"][memory_key]
        ):
            memory_index["memory_to_sessions"][memory_key].append(
                self.current_session_id
            )

        if self.current_session_id not in memory_index["session_memories"]:
            memory_index["session_memories"][self.current_session_id] = []

        if memory_key not in memory_index["session_memories"][self.current_session_id]:
            memory_index["session_memories"][self.current_session_id].append(memory_key)

        self._save_memory_index(memory_index)

        return f"🔗 Linked memory key '{memory_key}' to current session {self.current_session_id[:8]}"
