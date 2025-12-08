"""
Coordination Skill for TAID.

Manages cross-repo coordination and multi-agent orchestration.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json
import yaml

from ..base import BaseSkill


class CoordinationSkill(BaseSkill):
    """
    Cross-repo and multi-agent coordination skill.

    Manages dependencies, shared state, and coordination
    across multiple repositories or agent workflows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._coordination_dir: Optional[Path] = None
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "coordination"

    @property
    def description(self) -> str:
        return "Cross-repo coordination and multi-agent orchestration"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> bool:
        """Initialize coordination directory."""
        try:
            self._coordination_dir = Path(
                self.config.get('coordination_dir', '.claude/coordination')
            )
            self._coordination_dir.mkdir(parents=True, exist_ok=True)

            # Load active sessions
            sessions_file = self._coordination_dir / 'sessions.yaml'
            if sessions_file.exists():
                with open(sessions_file) as f:
                    self._active_sessions = yaml.safe_load(f) or {}

            self._initialized = True
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check prerequisites."""
        return {
            "satisfied": True,
            "missing": [],
            "warnings": []
        }

    # Session Management

    def start_session(
        self,
        session_name: str,
        participants: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a coordination session.

        Args:
            session_name: Name for the session
            participants: List of participant identifiers (repos, agents, etc.)
            context: Initial session context

        Returns:
            Session ID
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session_id = f"{session_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        session = {
            "id": session_id,
            "name": session_name,
            "participants": participants,
            "context": context or {},
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "events": []
        }

        self._active_sessions[session_id] = session
        self._save_sessions()

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        if not self._initialized:
            raise RuntimeError("Skill not initialized")
        return self._active_sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update session context.

        Args:
            session_id: Session ID
            context_updates: Context updates to merge

        Returns:
            Updated session
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session["context"].update(context_updates)
        session["updated_at"] = datetime.now().isoformat()

        self._save_sessions()
        return session

    def end_session(
        self,
        session_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        End a coordination session.

        Args:
            session_id: Session ID
            result: Final result/summary

        Returns:
            Completed session
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session["status"] = "completed"
        session["result"] = result
        session["completed_at"] = datetime.now().isoformat()

        # Archive the session
        archive_path = self._coordination_dir / 'archive' / f"{session_id}.yaml"
        archive_path.parent.mkdir(exist_ok=True)
        with open(archive_path, 'w', encoding='utf-8') as f:
            yaml.dump(session, f, default_flow_style=False)

        # Remove from active
        del self._active_sessions[session_id]
        self._save_sessions()

        return session

    # Event Tracking

    def record_event(
        self,
        session_id: str,
        event_type: str,
        participant: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record an event in a session.

        Args:
            session_id: Session ID
            event_type: Type of event (e.g., "work_item_created", "dependency_resolved")
            participant: Who triggered the event
            data: Event data

        Returns:
            Created event
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        event = {
            "type": event_type,
            "participant": participant,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        session["events"].append(event)
        session["updated_at"] = datetime.now().isoformat()

        self._save_sessions()
        return event

    def get_events(
        self,
        session_id: str,
        event_type: Optional[str] = None,
        participant: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events from a session with optional filtering.

        Args:
            session_id: Session ID
            event_type: Filter by event type
            participant: Filter by participant

        Returns:
            List of matching events
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        events = session.get("events", [])

        if event_type:
            events = [e for e in events if e.get("type") == event_type]

        if participant:
            events = [e for e in events if e.get("participant") == participant]

        return events

    # Dependency Management

    def register_dependency(
        self,
        session_id: str,
        source: str,
        target: str,
        dependency_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a dependency between participants.

        Args:
            session_id: Session ID
            source: Source participant (depends on target)
            target: Target participant (depended upon)
            dependency_type: Type of dependency
            metadata: Additional dependency metadata

        Returns:
            Created dependency record
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        dependency = {
            "source": source,
            "target": target,
            "type": dependency_type,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        session.setdefault("dependencies", []).append(dependency)
        session["updated_at"] = datetime.now().isoformat()

        self._save_sessions()
        return dependency

    def resolve_dependency(
        self,
        session_id: str,
        source: str,
        target: str,
        resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark a dependency as resolved.

        Args:
            session_id: Session ID
            source: Source participant
            target: Target participant
            resolution: Resolution details

        Returns:
            Updated dependency
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        for dep in session.get("dependencies", []):
            if dep["source"] == source and dep["target"] == target:
                dep["status"] = "resolved"
                dep["resolution"] = resolution
                dep["resolved_at"] = datetime.now().isoformat()

                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions()
                return dep

        raise ValueError(f"Dependency not found: {source} -> {target}")

    def get_pending_dependencies(
        self,
        session_id: str,
        participant: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending dependencies.

        Args:
            session_id: Session ID
            participant: Filter for dependencies where this is source or target

        Returns:
            List of pending dependencies
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        deps = [d for d in session.get("dependencies", []) if d["status"] == "pending"]

        if participant:
            deps = [d for d in deps if d["source"] == participant or d["target"] == participant]

        return deps

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        return [
            {"id": s["id"], "name": s["name"], "status": s["status"], "participants": s["participants"]}
            for s in self._active_sessions.values()
        ]

    def _save_sessions(self) -> None:
        """Save active sessions to disk."""
        sessions_file = self._coordination_dir / 'sessions.yaml'
        with open(sessions_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._active_sessions, f, default_flow_style=False)


# Factory function
def get_skill(config: Optional[Dict[str, Any]] = None) -> CoordinationSkill:
    """Get an instance of the coordination skill."""
    return CoordinationSkill(config)


Skill = CoordinationSkill
