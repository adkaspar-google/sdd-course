"""DependencyReleasePlanner implementation for topological deployment waves and rollout simulation."""

from typing import Any, Dict, Iterable, List, Optional, Set


def _is_valid_semver(version: str) -> bool:
    """Validates that version is a 3-part non-negative integer SemVer string 'X.Y.Z'."""
    if not isinstance(version, str) or version != version.strip():
        return False
    parts = version.split(".")
    if len(parts) != 3:
        return False
    for part in parts:
        if not part or not part.isdigit() or not part.isascii():
            return False
    return True


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
            raise ValueError(f"Invalid service name: {name!r}")
        if not _is_valid_semver(version):
            raise ValueError(f"Invalid SemVer version: {version!r}")

        raw_deps = list(depends_on) if depends_on is not None else []
        deduped_deps: List[str] = []
        seen: Set[str] = set()
        for dep in raw_deps:
            if not isinstance(dep, str):
                raise ValueError(f"Invalid dependency name: {dep!r}")
            dep_clean = dep.strip()
            if not dep_clean:
                continue
            if dep_clean == name or dep == name:
                raise ValueError(f"Service {name!r} cannot depend on itself")
            if dep_clean not in seen:
                seen.add(dep_clean)
                deduped_deps.append(dep_clean)

        self.services[name] = {
            "name": name,
            "version": version,
            "depends_on": deduped_deps,
            "critical": bool(critical),
        }

    def compute_release_waves(self) -> List[List[str]]:
        if not self.services:
            return []

        for svc_name, meta in self.services.items():
            for dep in meta["depends_on"]:
                if dep not in self.services:
                    raise ValueError(
                        f"Service {svc_name!r} depends on unregistered service {dep!r}"
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
                raise ValueError("Cycle detected in service dependency graph")

            waves.append(current_wave)
            placed.update(current_wave)
            remaining.difference_update(current_wave)

        return waves

    def simulate_rollout(self, failed_services: Iterable[str]) -> Dict[str, Any]:
        waves = self.compute_release_waves()
        failed_set: Set[str] = set(failed_services or [])

        status: Dict[str, str] = {}
        halt_triggered = False

        for wave in waves:
            halted_before_wave = halt_triggered
            for svc in wave:
                deps = self.services[svc]["depends_on"]
                dep_failed_or_blocked = any(
                    status.get(dep) in ("FAILED", "BLOCKED") for dep in deps
                )
                if halted_before_wave or dep_failed_or_blocked:
                    status[svc] = "BLOCKED"
                elif svc in failed_set:
                    status[svc] = "FAILED"
                    if self.services[svc]["critical"]:
                        halt_triggered = True
                else:
                    status[svc] = "DEPLOYED"

        deployed = sorted(svc for svc, st in status.items() if st == "DEPLOYED")
        failed = sorted(svc for svc, st in status.items() if st == "FAILED")
        blocked = sorted(svc for svc, st in status.items() if st == "BLOCKED")

        return {
            "waves": waves,
            "deployed": deployed,
            "failed": failed,
            "blocked": blocked,
            "halt_triggered": halt_triggered,
        }

    def impact_radius(self, service_name: str) -> List[str]:
        if not isinstance(service_name, str) or service_name not in self.services:
            raise ValueError(f"Unregistered service: {service_name!r}")

        waves = self.compute_release_waves()

        impacted: Set[str] = {service_name}
        ordered_downstream: List[str] = []

        for wave in waves:
            for svc in wave:
                if svc == service_name:
                    continue
                if any(dep in impacted for dep in self.services[svc]["depends_on"]):
                    impacted.add(svc)
                    ordered_downstream.append(svc)

        return ordered_downstream
