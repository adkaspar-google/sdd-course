# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of IL-T3: DependencyReleasePlanner."""

from typing import Any, Dict, Iterable, List, Optional, Set


class DependencyReleasePlanner:
    """Computes topological deployment waves and simulates failure blast radius."""

    def __init__(self) -> None:
        self.services: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _validate_semver(version: str) -> None:
        if not isinstance(version, str) or not version.isascii():
            raise ValueError(f"Invalid SemVer version: {version!r}")
        parts = version.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Invalid SemVer version: {version!r}")

    def register_service(
        self,
        name: str,
        version: str,
        depends_on: Optional[List[str]] = None,
        critical: bool = False,
    ) -> None:
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError(
                f"Service name must be a trimmed non-empty string: {name!r}"
            )

        self._validate_semver(version)

        deduped_deps: List[str] = []
        seen_deps: Set[str] = set()
        if depends_on is not None:
            for dep in depends_on:
                if not isinstance(dep, str):
                    continue
                cleaned_dep = dep.strip()
                if not cleaned_dep:
                    continue
                if cleaned_dep == name or dep == name:
                    raise ValueError(f"Service {name!r} cannot depend on itself.")
                if cleaned_dep not in seen_deps:
                    seen_deps.add(cleaned_dep)
                    deduped_deps.append(cleaned_dep)

        self.services[name] = {
            "name": name,
            "version": version,
            "depends_on": deduped_deps,
            "critical": bool(critical),
        }

    def compute_release_waves(self) -> List[List[str]]:
        if not self.services:
            return []

        in_degree: Dict[str, int] = {}
        dependents: Dict[str, List[str]] = {name: [] for name in self.services}

        for name, info in self.services.items():
            deps = info["depends_on"]
            for dep in deps:
                if dep not in self.services:
                    raise ValueError(
                        f"Service {name!r} depends on unregistered service {dep!r}."
                    )
                dependents[dep].append(name)
            in_degree[name] = len(deps)

        current_wave = sorted(name for name, deg in in_degree.items() if deg == 0)
        waves: List[List[str]] = []
        processed_count = 0

        while current_wave:
            waves.append(current_wave)
            processed_count += len(current_wave)
            next_wave: List[str] = []
            for u in current_wave:
                for v in dependents[u]:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        next_wave.append(v)
            current_wave = sorted(next_wave)

        if processed_count != len(self.services):
            raise ValueError("Cycle detected in service dependency graph.")

        return waves

    def simulate_rollout(self, failed_services: Iterable[str]) -> Dict[str, Any]:
        waves = self.compute_release_waves()
        failed_input: Set[str] = set(failed_services)

        status: Dict[str, str] = {}
        deployed: List[str] = []
        failed: List[str] = []
        blocked: List[str] = []
        halt_triggered = False

        for wave in waves:
            wave_critical_failed = False
            for service in wave:
                deps = self.services[service]["depends_on"]
                dep_failed_or_blocked = any(
                    status.get(dep) in ("FAILED", "BLOCKED") for dep in deps
                )
                if halt_triggered or dep_failed_or_blocked:
                    status[service] = "BLOCKED"
                    blocked.append(service)
                elif service in failed_input:
                    status[service] = "FAILED"
                    failed.append(service)
                    if self.services[service]["critical"]:
                        wave_critical_failed = True
                else:
                    status[service] = "DEPLOYED"
                    deployed.append(service)

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
        waves = self.compute_release_waves()
        if service_name not in self.services:
            raise ValueError(f"Service {service_name!r} is not registered.")

        dependents: Dict[str, List[str]] = {name: [] for name in self.services}
        for name, info in self.services.items():
            for dep in info["depends_on"]:
                dependents[dep].append(name)

        downstream: Set[str] = set()
        stack = list(dependents[service_name])
        while stack:
            curr = stack.pop()
            if curr not in downstream and curr != service_name:
                downstream.add(curr)
                stack.extend(dependents[curr])

        return [
            svc
            for wave in waves
            for svc in wave
            if svc in downstream
        ]
