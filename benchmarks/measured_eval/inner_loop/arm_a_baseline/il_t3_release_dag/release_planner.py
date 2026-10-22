"""Starter module for IL-T3: DependencyReleasePlanner."""

import re
from typing import Any, Dict, Iterable, List, Optional, Set

_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class DependencyReleasePlanner:
    """Computes topological deployment waves and simulates failure blast radius."""

    def __init__(self) -> None:
        self.services: Dict[str, Dict[str, Any]] = {}
        # TODO(legacy): add generate_helm_chart() and notify_pagerduty()

    def register_service(
        self,
        name: str,
        version: str,
        depends_on: Optional[List[str]] = None,
        critical: bool = False,
    ) -> None:
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError("Service name must be a non-empty trimmed string.")
        if not isinstance(version, str) or not _SEMVER_RE.fullmatch(version):
            raise ValueError(
                f"Invalid version '{version}': must be a 3-part non-negative integer SemVer string 'X.Y.Z'."
            )

        raw_deps = list(depends_on or [])
        if name in raw_deps:
            raise ValueError(f"Service '{name}' cannot depend on itself.")
        deduped_deps = list(dict.fromkeys(raw_deps))

        self.services[name] = {
            "name": name,
            "version": version,
            "depends_on": deduped_deps,
            "critical": bool(critical),
        }

    def compute_release_waves(self) -> List[List[str]]:
        if not self.services:
            return []

        for svc_name, info in self.services.items():
            for dep in info["depends_on"]:
                if dep not in self.services:
                    raise ValueError(
                        f"Service '{svc_name}' depends on unregistered service '{dep}'."
                    )

        waves: List[List[str]] = []
        placed: Set[str] = set()
        remaining: Set[str] = set(self.services.keys())

        while remaining:
            current_wave = sorted(
                svc
                for svc in remaining
                if all(dep in placed for dep in self.services[svc]["depends_on"])
            )
            if not current_wave:
                raise ValueError("Cycle detected in service dependency graph.")
            waves.append(current_wave)
            placed.update(current_wave)
            remaining.difference_update(current_wave)

        return waves

    def simulate_rollout(self, failed_services: Iterable[str]) -> Dict[str, Any]:
        waves = self.compute_release_waves()
        failed_input: Set[str] = set(failed_services or [])

        deployed: List[str] = []
        failed: List[str] = []
        blocked: List[str] = []
        unhealthy: Set[str] = set()
        halt_triggered = False

        for wave in waves:
            halt_before_wave = halt_triggered
            wave_critical_failed = False

            for svc in wave:
                deps = self.services[svc]["depends_on"]
                if halt_before_wave or any(dep in unhealthy for dep in deps):
                    blocked.append(svc)
                    unhealthy.add(svc)
                elif svc in failed_input:
                    failed.append(svc)
                    unhealthy.add(svc)
                    if self.services[svc]["critical"]:
                        wave_critical_failed = True
                else:
                    deployed.append(svc)

            if wave_critical_failed:
                halt_triggered = True

        return {
            "waves": waves,
            "deployed": sorted(deployed),
            "failed": sorted(failed),
            "blocked": sorted(blocked),
            "halt_triggered": halt_triggered,
        }

    def impact_radius(self, service_name: str) -> List[str]:
        if not isinstance(service_name, str) or service_name not in self.services:
            raise ValueError(f"Service '{service_name}' is not registered.")

        waves = self.compute_release_waves()
        impacted: Set[str] = {service_name}
        downstream: List[str] = []

        for wave in waves:
            for svc in wave:
                if svc == service_name:
                    continue
                if any(dep in impacted for dep in self.services[svc]["depends_on"]):
                    impacted.add(svc)
                    downstream.append(svc)

        return downstream
