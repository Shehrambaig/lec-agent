import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from backend.state import NodeLog


class ExecutionLogger:
    """Logger for tracking node executions and creating audit trails."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_id = None
        self.current_session_logs = []

    def start_session(self, topic: str, user_id: str = "default_user") -> str:
        """Start a new logging session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = f"{user_id}_{timestamp}"
        self.current_session_logs = []

        # Create session metadata
        metadata = {
            "session_id": self.current_session_id,
            "topic": topic,
            "user_id": user_id,
            "started_at": datetime.now().isoformat(),
            "logs": []
        }

        return self.current_session_id

    def log_node_execution(
            self,
            node_name: str,
            inputs: Dict[str, Any],
            output: Any,
            prompt: Optional[str] = None,
            model_settings: Optional[Dict[str, Any]] = None,
            human_decision: Optional[str] = None,
            execution_time_ms: Optional[float] = None
    ) -> NodeLog:
        """Log a single node execution."""

        log_entry = NodeLog(
            node_name=node_name,
            timestamp=datetime.now(),
            inputs=self._sanitize_for_json(inputs),
            prompt=prompt,
            output=self._sanitize_for_json(output),
            model_settings=model_settings or {},
            human_decision=human_decision,
            execution_time_ms=execution_time_ms
        )

        self.current_session_logs.append(log_entry.dict())

        # Write to file immediately for safety
        self._write_session_log()

        return log_entry

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Sanitize objects for JSON serialization."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        else:
            return str(obj)

    def _write_session_log(self):
        """Write current session logs to file."""
        if not self.current_session_id:
            return

        log_file = self.log_dir / f"{self.current_session_id}.json"

        log_data = {
            "session_id": self.current_session_id,
            "total_nodes": len(self.current_session_logs),
            "last_updated": datetime.now().isoformat(),
            "logs": self.current_session_logs
        }

        # Custom JSON encoder for datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, cls=DateTimeEncoder)

    def end_session(self, final_output: Optional[str] = None):
        """End the current logging session."""
        if not self.current_session_id:
            return

        log_file = self.log_dir / f"{self.current_session_id}.json"

        with open(log_file, 'r') as f:
            log_data = json.load(f)

        log_data["completed_at"] = datetime.now().isoformat()
        log_data["final_output"] = final_output
        log_data["status"] = "completed"

        # Custom JSON encoder for datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, cls=DateTimeEncoder)

        print(f"✓ Session log saved: {log_file}")

        self.current_session_id = None
        self.current_session_logs = []

    def get_session_logs(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve logs for a specific session."""
        log_file = self.log_dir / f"{session_id}.json"

        if not log_file.exists():
            return None

        with open(log_file, 'r') as f:
            return json.load(f)


# Global logger instance
execution_logger = ExecutionLogger()