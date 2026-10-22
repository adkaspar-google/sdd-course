"""Dependency DAG Release Planner & Rollback Simulator."""

from __future__ import annotations
from typing import Any, Iterable


class DependencyReleasePlanner:
    def __init__(self) -> None:
        self.services: dict[str, dict[str, Any]] = {}

    def register_service(
        self,
        name: str,
        version: str,
        depends_on: list[str] | None = None,
        critical: bool = False,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("Empty service name")
        if not isinstance(version, str):
            raise ValueError("Invalid version")
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isascii() and p.isdigit() for p in parts):
            raise ValueError("Invalid version")
        deps = list(dict.fromkeys(depends_on or []))
        if name.strip() in deps:
            raise ValueError("Self dependency")
        self.services[name.strip()] = {
            "name": name.strip(),
            "version": version,
            "depends_on": deps,
            "critical": bool(critical),
        }

    def compute_release_waves(self) -> list[list[str]]:
        if not self.services:
            return []
        for svc, meta in self.services.items():
            for d in meta["depends_on"]:
                if d not in self.services:
                    raise ValueError(f"Unknown dependency {d}")
        placed: dict[str, int] = {}
        waves: list[list[str]] = []
        remaining = set(self.services.keys())
        while remaining:
            ready = [
                s for s in remaining
                if all(d in placed for d in self.services[s]["depends_on"])
            ]
            if not ready:
                raise ValueError("Cycle detected")
            ready.sort()
            w_idx = len(waves)
            waves.append(ready)
            for s in ready:
                placed[s] = w_idx
                remaining.remove(s)
        return waves

    def simulate_rollout(self, failed_services: Iterable[str]) -> dict[str, Any]:
        waves = self.compute_release_waves()
        failed_set = set(failed_services)
        deployed: list[str] = []
        failed: list[str] = []
        blocked: list[str] = []
        halt_triggered = False

        for wave in waves:
            halted_before_wave = halt_triggered
            for svc in wave:
                deps = self.services[svc]["depends_on"]
                if halted_before_wave or any(d in failed or d in blocked for d in deps):
                    blocked.append(svc)
                elif svc in failed_set:
                    failed.append(svc)
                    if self.services[svc]["critical"]:
                        halt_triggered = True
                else:
                    deployed.append(svc)

        return {
            "waves": waves,
            "deployed": sorted(deployed),
            "failed": sorted(failed),
            "blocked": sorted(blocked),
            "halt_triggered": halt_triggered,
        }

    def impact_radius(self, service_name: str) -> list[str]:
        if service_name not in self.services:
            raise ValueError("Unknown service")
        waves = self.compute_release_waves()
        impacted: set[str] = set()
        ordered_impacted: list[str] = []
        for wave in waves:
            for svc in wave:
                deps = self.services[svc]["depends_on"]
                if any(d == service_name or d in impacted for d in deps):
                    impacted.add(svc)
                    ordered_impacted.append(svc)
        return ordered_impacted

    # TODO: implement generate_helm_chart_yaml(self) -> str helper
    # TODO: implement notify_pagerduty_oncall(self, service_name: str) -> bool helper
