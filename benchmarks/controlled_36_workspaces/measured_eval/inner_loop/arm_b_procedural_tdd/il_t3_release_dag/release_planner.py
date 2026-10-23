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
"""DependencyReleasePlanner implementation for topological deployment waves and rollout simulation."""

import re
from typing import Any, Dict, Iterable, List, Optional, Set

_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class DependencyReleasePlanner:
    """Computes topological deployment waves and simulates failure blast radius."""

    def __init__(self) -> None:
        self.services: Dict[str, Dict[str, Any]] = {}

    def register_service(
        self,
        name: str,
        version: str,
        depends_on: Optional[List[str]] = None,
        critical: bool = False,
    ) -> None:
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError("Service name must be a trimmed non-empty string.")

        if not isinstance(version, str) or not _SEMVER_RE.match(version):
            raise ValueError(
                f"Invalid version '{version}': must be a 3-part non-negative integer SemVer 'X.Y.Z'."
            )

        raw_deps = list(depends_on) if depends_on is not None else []
        deduped_deps: List[str] = []
        seen: Set[str] = set()
        for dep in raw_deps:
            if not isinstance(dep, str) or not dep.strip() or dep != dep.strip():
                raise ValueError("Dependency name must be a trimmed non-empty string.")
            if dep == name:
                raise ValueError(f"Service '{name}' cannot depend on itself.")
            if dep not in seen:
                seen.add(dep)
                deduped_deps.append(dep)

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

        remaining: Set[str] = set(self.services.keys())
        placed: Set[str] = set()
        waves: List[List[str]] = []

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
        failed_input: Set[str] = set(failed_services)

        deployed: List[str] = []
        failed: List[str] = []
        blocked: List[str] = []
        unhealthy: Set[str] = set()
        halt_triggered = False

        for wave in waves:
            wave_critical_failed = False
            for svc in wave:
                deps = self.services[svc]["depends_on"]
                if halt_triggered or any(dep in unhealthy for dep in deps):
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
        waves = self.compute_release_waves()
        if service_name not in self.services:
            raise ValueError(f"Service '{service_name}' is not registered.")

        impacted: Set[str] = set()
        for wave in waves:
            for svc in wave:
                if svc == service_name:
                    continue
                deps = self.services[svc]["depends_on"]
                if service_name in deps or any(dep in impacted for dep in deps):
                    impacted.add(svc)

        return [svc for wave in waves for svc in wave if svc in impacted]
