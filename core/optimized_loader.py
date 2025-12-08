"""
Optimized Context Loader for Claude Code Agents
Implements smart context selection based on task analysis and templates
"""

import yaml
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from functools import lru_cache
import json

# Import the context pruner
try:
    from context_pruner import ContextPruner
    PRUNER_AVAILABLE = True
except ImportError:
    PRUNER_AVAILABLE = False

# Import usage analytics
try:
    from usage_analytics import UsageAnalytics
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

class OptimizedContextLoader:
    """
    Optimized context loader that uses an index file and templates
    for intelligent context selection.
    """

    def __init__(self, project_root: Optional[Path] = None, enable_analytics: bool = True):
        """Initialize the context loader."""
        self.project_root = project_root or Path.cwd()
        self.index_path = self.project_root / ".claude" / "context-index.yaml"
        self.index = self._load_index()
        self.cache = {}
        self.cache_timestamps = {}
        self.usage_log = []
        self.pruner = ContextPruner() if PRUNER_AVAILABLE else None
        self.analytics = UsageAnalytics() if (ANALYTICS_AVAILABLE and enable_analytics) else None

    def _load_index(self) -> Dict[str, Any]:
        """Load the context index file."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Context index not found: {self.index_path}")

        with open(self.index_path, 'r') as f:
            return yaml.safe_load(f)

    def get_context_for_task(self, task: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Get optimized context for a specific task.

        Returns:
            Dict containing:
                - content: The actual context content
                - contexts_used: List of context names that were loaded
                - tokens_used: Estimated token count
                - template_used: Template name if one was matched
        """
        import time
        start_time = time.time()

        # Check cache first
        task_hash = hashlib.md5(task.encode()).hexdigest()
        cache_key = f"{task_hash}_{max_tokens}"
        cache_hit = False

        if self._is_cache_valid(cache_key):
            result = self.cache[cache_key]
            cache_hit = True
            self._log_usage(task, "cache_hit", result["contexts_used"])
        else:
            # Try to match a template first
            template_name = self._match_template(task)

            if template_name:
                result = self._load_template_context(template_name, task, max_tokens)
                result["template_used"] = template_name
            else:
                # Use keyword-based selection
                keywords = self._extract_keywords(task)
                relevant_contexts = self._find_relevant_contexts(keywords)
                result = self._load_contexts_within_budget(relevant_contexts, max_tokens)
                result["template_used"] = None

            # Cache the result
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = datetime.now()

            # Log usage
            self._log_usage(task, "loaded", result["contexts_used"], template_name)

        # Track analytics if enabled
        if self.analytics:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.analytics.log_usage(
                task=task,
                task_hash=task_hash,
                contexts_loaded=result.get("contexts_used", []),
                template_used=result.get("template_used"),
                tokens_used=result.get("tokens_used"),
                cache_hit=cache_hit,
                execution_time_ms=execution_time_ms,
                success=True
            )

        return result

    def _match_template(self, task: str) -> Optional[str]:
        """Match task to a pre-defined template."""
        task_lower = task.lower()

        # Check for explicit template matches
        template_patterns = {
            "implement_feature": r"(implement|create|add|build).*feature",
            "write_tests": r"(write|create|add).*test",
            "debug_issue": r"(debug|fix|investigate|troubleshoot)",
            "sprint_planning": r"sprint.*planning|plan.*sprint",
            "sprint_execution": r"sprint.*execution|execute.*sprint",
            "mcp_development": r"mcp|model.context|tool.*(handler|registration)",
            "infrastructure": r"terraform|infrastructure|provision",
            "security_review": r"security.*(review|audit|scan)",
            "deployment": r"deploy|release|rollout",
            "azure_operations": r"azure|devops|work.item"
        }

        for template_name, pattern in template_patterns.items():
            if re.search(pattern, task_lower):
                return template_name

        return None

    def _load_template_context(self, template_name: str, task: str, max_tokens: int) -> Dict[str, Any]:
        """Load context based on a template."""
        if template_name not in self.index.get("templates", {}):
            raise ValueError(f"Template not found: {template_name}")

        template = self.index["templates"][template_name]
        contexts_to_load = template["contexts"].copy()

        # Check for additional contexts based on keywords
        task_lower = task.lower()
        for keyword, additional_contexts in template.get("additional_by_keyword", {}).items():
            if keyword in task_lower:
                contexts_to_load.extend(additional_contexts)

        # Remove duplicates while preserving order
        seen = set()
        unique_contexts = []
        for ctx in contexts_to_load:
            if ctx not in seen:
                seen.add(ctx)
                unique_contexts.append(ctx)

        return self._load_contexts_within_budget(unique_contexts, max_tokens)

    def _extract_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task description."""
        # Convert to lowercase and split
        words = re.findall(r'\b[a-z]+\b', task.lower())

        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                     'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
                     'was', 'were', 'be', 'been', 'being', 'have', 'has',
                     'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'need', 'help'}

        keywords = [w for w in words if w not in stop_words]

        # Also check for multi-word keywords
        multi_word_patterns = {
            "model context": r"model\s+context",
            "work item": r"work\s+item",
            "sprint planning": r"sprint\s+planning",
            "azure devops": r"azure\s+devops"
        }

        for keyword, pattern in multi_word_patterns.items():
            if re.search(pattern, task.lower()):
                keywords.append(keyword)

        return keywords

    def _find_relevant_contexts(self, keywords: List[str]) -> List[str]:
        """Find relevant contexts based on keywords."""
        context_scores = {}

        # Score contexts based on keyword matches
        keyword_mappings = self.index.get("keyword_mappings", {})

        for keyword in keywords:
            if keyword in keyword_mappings:
                for context_name in keyword_mappings[keyword]:
                    if context_name not in context_scores:
                        context_scores[context_name] = 0
                    context_scores[context_name] += 1

        # Also check context tags
        for context_name, context_info in self.index.get("contexts", {}).items():
            tags = context_info.get("tags", [])
            for keyword in keywords:
                if keyword in tags:
                    if context_name not in context_scores:
                        context_scores[context_name] = 0
                    context_scores[context_name] += 1

        # Sort by score
        sorted_contexts = sorted(context_scores.items(), key=lambda x: x[1], reverse=True)

        # Return context names in order of relevance
        return [ctx[0] for ctx in sorted_contexts]

    def _load_contexts_within_budget(self, context_names: List[str], max_tokens: int) -> Dict[str, Any]:
        """Load contexts within token budget."""
        loaded_content = []
        loaded_contexts = []
        total_tokens = 0

        # Handle dependencies first
        contexts_to_load = self._resolve_dependencies(context_names)

        # If pruner is available, use it for intelligent loading
        if self.pruner and PRUNER_AVAILABLE:
            context_configs = []
            for context_name in contexts_to_load:
                if context_name not in self.index.get("contexts", {}):
                    continue

                context_info = self.index["contexts"][context_name]
                context_path = self.project_root / context_info["path"]

                if context_path.exists():
                    # Determine if we should load essential only
                    priority = context_info.get("priority", "medium")
                    essential_only = priority == "low" and len(contexts_to_load) > 3

                    context_configs.append({
                        'path': context_path,
                        'essential_only': essential_only,
                        'max_tokens': max_tokens // len(contexts_to_load)
                    })

            # Use pruner to load contexts
            if context_configs:
                pruned_content = self.pruner.prune_multiple_contexts(context_configs, max_tokens)
                return {
                    "content": pruned_content,
                    "contexts_used": contexts_to_load,
                    "tokens_used": self.pruner._estimate_tokens(pruned_content) if self.pruner else len(pruned_content) // 4
                }

        # Fallback to original loading method if pruner not available
        for context_name in contexts_to_load:
            if context_name not in self.index.get("contexts", {}):
                continue

            context_info = self.index["contexts"][context_name]
            token_estimate = context_info.get("token_estimate", 1000)

            # Check if we have budget
            if total_tokens + token_estimate > max_tokens:
                continue

            # Load the context
            context_path = self.project_root / context_info["path"]
            if context_path.exists():
                content = self._load_context_file(context_path)
                loaded_content.append(f"# Context: {context_name}\n{content}")
                loaded_contexts.append(context_name)
                total_tokens += token_estimate

        return {
            "content": "\n\n---\n\n".join(loaded_content),
            "contexts_used": loaded_contexts,
            "tokens_used": total_tokens
        }

    def _resolve_dependencies(self, context_names: List[str]) -> List[str]:
        """Resolve context dependencies."""
        resolved = []
        seen = set()

        def add_with_deps(ctx_name):
            if ctx_name in seen:
                return
            seen.add(ctx_name)

            if ctx_name in self.index.get("contexts", {}):
                # Add dependencies first
                deps = self.index["contexts"][ctx_name].get("dependencies", [])
                for dep in deps:
                    add_with_deps(dep)

                # Then add the context itself
                resolved.append(ctx_name)

        for ctx_name in context_names:
            add_with_deps(ctx_name)

        return resolved

    def _load_context_file(self, path: Path) -> str:
        """Load a context file."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached context is still valid."""
        if cache_key not in self.cache:
            return False

        # Check TTL
        ttl_minutes = self.index.get("loading_rules", {}).get("cache_ttl_minutes", 30)
        timestamp = self.cache_timestamps.get(cache_key)

        if not timestamp:
            return False

        age = datetime.now() - timestamp
        return age < timedelta(minutes=ttl_minutes)

    def _log_usage(self, task: str, action: str, contexts: List[str], template: Optional[str] = None):
        """Log context usage for analytics."""
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "task": task[:100],  # Truncate long tasks
            "action": action,
            "contexts": contexts,
            "template": template
        })

    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get usage analytics."""
        if not self.usage_log:
            return {"message": "No usage data available"}

        # Analyze usage patterns
        context_usage_count = {}
        template_usage_count = {}
        cache_hits = 0
        total_requests = len(self.usage_log)

        for entry in self.usage_log:
            if entry["action"] == "cache_hit":
                cache_hits += 1

            for ctx in entry.get("contexts", []):
                context_usage_count[ctx] = context_usage_count.get(ctx, 0) + 1

            template = entry.get("template")
            if template:
                template_usage_count[template] = template_usage_count.get(template, 0) + 1

        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hits / total_requests if total_requests > 0 else 0,
            "most_used_contexts": sorted(context_usage_count.items(), key=lambda x: x[1], reverse=True)[:5],
            "most_used_templates": sorted(template_usage_count.items(), key=lambda x: x[1], reverse=True)[:5],
            "unique_contexts_used": len(context_usage_count),
            "unique_templates_used": len(template_usage_count)
        }

    def clear_cache(self):
        """Clear the context cache."""
        self.cache.clear()
        self.cache_timestamps.clear()

    def save_usage_log(self, path: Optional[Path] = None):
        """Save usage log to file."""
        if not path:
            path = self.project_root / ".claude" / "context-usage.json"

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.usage_log, f, indent=2)

    def load_usage_log(self, path: Optional[Path] = None):
        """Load usage log from file."""
        if not path:
            path = self.project_root / ".claude" / "context-usage.json"

        if path.exists():
            with open(path, 'r') as f:
                self.usage_log = json.load(f)

    def get_analytics_report(self) -> str:
        """Get analytics report if analytics is enabled."""
        if self.analytics:
            return self.analytics.generate_report()
        else:
            return "Analytics not enabled or not available"

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions from analytics."""
        if self.analytics:
            return self.analytics.get_optimization_suggestions()
        else:
            return []

    def analyze_context_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a specific context file for optimization."""
        if self.pruner:
            return self.pruner.analyze_context_usage(file_path)
        else:
            return {"error": "Context pruner not available"}


# Convenience functions
def get_context_for_task(task: str, max_tokens: int = 4000) -> str:
    """Get context for a task (convenience function)."""
    loader = OptimizedContextLoader()
    result = loader.get_context_for_task(task, max_tokens)
    return result["content"]


def get_context_with_metadata(task: str, max_tokens: int = 4000) -> Dict[str, Any]:
    """Get context with metadata about what was loaded."""
    loader = OptimizedContextLoader()
    return loader.get_context_for_task(task, max_tokens)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        loader = OptimizedContextLoader()
        result = loader.get_context_for_task(task)

        print(f"Task: {task}")
        print(f"Template Used: {result.get('template_used', 'None')}")
        print(f"Contexts Loaded: {', '.join(result['contexts_used'])}")
        print(f"Estimated Tokens: {result['tokens_used']}")
        print("\n--- CONTEXT ---\n")
        print(result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content'])