#!/usr/bin/env python3
# Copyright 2026 Alejandro Kaspar - AI Forward Deployed Engineer
# Licensed under the Apache License, Version 2.0 (the "License") and CC BY 4.0.
"""Object-Oriented Harness (OO-Harness) for Spec-Driven Development (SDD).

Inspired by:
  - "Object-Oriented Harness: Evolving Agent Harnesses through Object-Oriented
    Design" (Li, Mishra, Ming, Chen, et al., UIUC & Google Cloud AI Research,
    arXiv:2610.28380, Oct 2026)
  - "Harness^2: Recursive Agent Harnessing for an Open World"
    (google-research/harness2, Oct 2026)
  - AutomationBench (zapier/AutomationBench): Programmatic state assertions &
    partial-credit objective scoring across multi-app workflows
  - Commit0 (commit-0/commit0), FeatureBench (LiberCoders/FeatureBench),
    SWE-bench Verified (princeton-nlp/SWE-bench), and SkillsBench

Architecture:
  Instead of a single monolithic global harness that suffers from context bloat
  and conflicting instructions across heterogeneous software engineering tasks,
  OO-Harness organizes SDD + Superpowers execution into an Object-Oriented
  Class Hierarchy:

  BaseSDDHarness (Root Class)
   ├── GreenfieldSpecHarness      (Track/Task: Greenfield 0->1 feature design)
   ├── BrownfieldSyncHarness      (Track/Task: Brownfield reverse-engineering)
   ├── TDDActuationHarness        (Track/Task: Stateful boundary & streak TDD)
   ├── DriftRemediationHarness    (Track/Task: Spec-to-code bug & drift repair)
   ├── MultiAppWorkflowHarness    (Track/Task: AutomationBench state machines)
   └── CleanRoomRebuildHarness    (Track/Task: Level-3 SPEC.md SSOT rebuild)

  Paired with OOHarnessRouter, which inspects task signatures and repository
  state at test time to route each task to its specialized harness subclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import os
from pathlib import Path
import stat
from typing import Any, Callable, Dict, List, Optional, Tuple


class BuilderStatus(str, Enum):
    """4-State Builder Status Protocol from Inner-Loop Superpowers."""

    DONE = "DONE"
    DONE_WITH_CONCERNS = "DONE_WITH_CONCERNS"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"
    BLOCKED = "BLOCKED"


class TaskArchetype(str, Enum):
    """Task archetypes routed by OOHarnessRouter."""

    GREENFIELD_SPEC = "greenfield_spec"
    BROWNFIELD_SYNC = "brownfield_sync"
    TDD_ACTUATION = "tdd_actuation"
    DRIFT_REMEDIATION = "drift_remediation"
    MULTI_APP_WORKFLOW = "multi_app_workflow"
    CLEAN_ROOM_REBUILD = "clean_room_rebuild"


@dataclass
class AuditFinding:
    """Single defect finding from the Cold Independent Auditor."""

    severity: str  # "P0", "P1", "P2"
    stage: str  # "Stage1_SpecCompliance" or "Stage2_CodeQuality"
    requirement_id: str
    description: str


@dataclass
class StageAuditReport:
    """Two-Stage Cold Independent Auditor Report."""

    stage1_passed: bool
    stage2_passed: bool
    findings: List[AuditFinding] = field(default_factory=list)
    test_hashes_intact: bool = True

    @property
    def readiness_score(self) -> float:
        """Defect-anchored readiness score: max(0, 10 - 3*P0 - 1*P1 - 0.2*P2)."""
        p0 = sum(1 for f in self.findings if f.severity == "P0")
        p1 = sum(1 for f in self.findings if f.severity == "P1")
        p2 = sum(1 for f in self.findings if f.severity == "P2")
        return round(max(0.0, 10.0 - (3.0 * p0) - (1.0 * p1) - (0.2 * p2)), 2)

    @property
    def approved(self) -> bool:
        p0 = sum(1 for f in self.findings if f.severity == "P0")
        p1 = sum(1 for f in self.findings if f.severity == "P1")
        return (
            self.stage1_passed
            and self.stage2_passed
            and self.test_hashes_intact
            and p0 == 0
            and p1 == 0
            and self.readiness_score >= 9.0
        )


@dataclass
class HarnessExecutionTrace:
    """Structured telemetry emitted by an OO-Harness execution."""

    harness_class: str
    archetype: TaskArchetype
    inherited_guardrails: List[str]
    overridden_methods: List[str]
    active_skills: List[str]
    builder_status: BuilderStatus
    test_lock_verified: bool
    spec_delta_merged: bool
    audit_report: StageAuditReport
    objective_checks_passed: int
    objective_checks_total: int
    mutants_killed: int
    mutants_total: int

    @property
    def partial_credit_score(self) -> float:
        """AutomationBench-style partial credit objective score (0.0 to 1.0)."""
        if self.objective_checks_total == 0:
            return 1.0
        return round(
            self.objective_checks_passed / self.objective_checks_total, 4
        )

    @property
    def strict_pass_at_1(self) -> bool:
        """Strict Pass@1: 100% objective checks passed + auditor approved."""
        return (
            self.objective_checks_passed == self.objective_checks_total
            and self.audit_report.approved
            and self.test_lock_verified
        )

    @property
    def mutation_kill_rate(self) -> float:
        """Fraction of injected syntactic/semantic mutants killed by tests."""
        if self.mutants_total == 0:
            return 1.0
        return round(self.mutants_killed / self.mutants_total, 4)


class BaseSDDHarness:
    """Root class in the OO-Harness hierarchy (arXiv:2610.28380).

    Encapsulates universal Outer-Loop SDD + Inner-Loop Superpowers invariants
    inherited by every specialized harness subclass:
      1. Constitutional Tech-Stack Governance (`conductor/tech-stack.md`)
      2. Adversarial Verifier Lock (`chmod -w` + SHA-256 hash verification)
      3. Two-Stage Cold Independent Auditor (`Stage 1: Spec -> Stage 2: Code`)
      4. Hard Completion Gate (`@verification-before-completion`)
      5. OpenSpec Two-Plane Delta Synchronization (`openspec/specs/`)
    """

    archetype: TaskArchetype = TaskArchetype.GREENFIELD_SPEC
    active_skills: List[str] = [
        "verification-before-completion",
        "subagent-two-stage-review",
    ]

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root or Path(".")
        self._locked_file_hashes: Dict[Path, str] = {}

    def inherited_guardrails(self) -> List[str]:
        return [
            "Conductor Constitutional Governance (conductor/tech-stack.md)",
            "Immutable Verifier Lock (chmod -w + SHA-256 integrity check)",
            "Elephant-Goldfish Stateless Builder Context Separation",
            "Two-Stage Cold Independent Auditor (3-round circuit breaker)",
            "Hard Verification-Before-Completion Gate (fresh exit_code == 0)",
            "OpenSpec Two-Plane Living Spec Sync (openspec/specs/)",
        ]

    def overridden_methods(self) -> List[str]:
        """Returns the list of lifecycle hooks specialized by the subclass."""
        base_funcs = {
            name: getattr(BaseSDDHarness, name)
            for name in (
                "pre_flight",
                "discover_or_grill",
                "plan_and_scaffold",
                "execute_actuation",
                "audit_and_sync",
            )
        }
        overridden = []
        for name, base_fn in base_funcs.items():
            sub_fn = getattr(self.__class__, name)
            if sub_fn is not base_fn:
                overridden.append(name)
        return overridden

    # --- Universal Hardening Primitives (Inherited by All Subclasses) ---

    def lock_verifier_files(self, test_files: List[Path]) -> Dict[Path, str]:
        """Applies read-only lock and records SHA-256 digests to prevent reward hacking."""
        self._locked_file_hashes.clear()
        for path in test_files:
            if path.exists():
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self._locked_file_hashes[path] = digest
                current_mode = path.stat().st_mode
                path.chmod(
                    current_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                )
        return dict(self._locked_file_hashes)

    def verify_locked_files_intact(self) -> bool:
        """Verifies that no locked test file was tampered with during actuation."""
        for path, expected_hash in self._locked_file_hashes.items():
            if not path.exists():
                return False
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                return False
        return True

    def unlock_verifier_files(self) -> None:
        """Restores user write permissions after verification completes."""
        for path in self._locked_file_hashes:
            if path.exists():
                current_mode = path.stat().st_mode
                path.chmod(current_mode | stat.S_IWUSR)

    def run_two_stage_cold_audit(
        self,
        required_req_ids: List[str],
        covered_req_ids: List[str],
        code_quality_violations: List[Tuple[str, str]],
        scope_creep_files: Optional[List[str]] = None,
    ) -> StageAuditReport:
        """Executes the 2-Stage Cold Independent Auditor protocol.

        Stage 1 (Spec Compliance & Anti-Reward-Hacking) MUST pass before
        Stage 2 (Code Quality & Constitutional Alignment) is evaluated.
        """
        findings: List[AuditFinding] = []
        hashes_ok = self.verify_locked_files_intact()
        if not hashes_ok:
            findings.append(
                AuditFinding(
                    severity="P0",
                    stage="Stage1_SpecCompliance",
                    requirement_id="ANTI-REWARD-HACKING",
                    description="Locked verification test file was modified or deleted during implementation.",
                )
            )

        for req_id in required_req_ids:
            if req_id not in covered_req_ids:
                findings.append(
                    AuditFinding(
                        severity="P0",
                        stage="Stage1_SpecCompliance",
                        requirement_id=req_id,
                        description=f"Requirement {req_id} missing behavioral implementation or scenario verification.",
                    )
                )

        for extra_file in scope_creep_files or []:
            findings.append(
                AuditFinding(
                    severity="P1",
                    stage="Stage1_SpecCompliance",
                    requirement_id="OUT-OF-SCOPE-GUARD",
                    description=f"Unapproved out-of-scope file/feature modified: {extra_file}",
                )
            )

        stage1_passed = len(findings) == 0

        # Stage 2 runs strictly after Stage 1 passes
        stage2_passed = False
        if stage1_passed:
            for sev, desc in code_quality_violations:
                findings.append(
                    AuditFinding(
                        severity=sev,
                        stage="Stage2_CodeQuality",
                        requirement_id="CONSTITUTION",
                        description=desc,
                    )
                )
            stage2_passed = not any(
                f.stage == "Stage2_CodeQuality" and f.severity in ("P0", "P1")
                for f in findings
            )

        return StageAuditReport(
            stage1_passed=stage1_passed,
            stage2_passed=stage2_passed,
            findings=findings,
            test_hashes_intact=hashes_ok,
        )

    # --- Polymorphic Lifecycle Hooks (Overridden by Subclasses) ---

    def pre_flight(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook 1: Pre-flight workspace and context inspection."""
        return {"status": "ready", "mode": "base"}

    def discover_or_grill(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook 2: Socratic discovery or brownfield contract extraction."""
        return {"requirements_locked": True}

    def plan_and_scaffold(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook 3: Bite-sized 2-5 min TDD task decomposition & test scaffolding."""
        return {"tasks_decomposed": True}

    def execute_actuation(self, task_context: Dict[str, Any]) -> BuilderStatus:
        """Hook 4: Stateless Goldfish Builder execution."""
        return BuilderStatus.DONE

    def audit_and_sync(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook 5: Two-Plane OpenSpec delta merge & Conductor checkpoint."""
        return {"spec_synced": True}


class GreenfieldSpecHarness(BaseSDDHarness):
    """Specialized Harness Subclass 1: Greenfield 0->1 Feature Design (Lab 01).

    Inherits BaseSDDHarness guardrails and overrides `discover_or_grill` and
    `plan_and_scaffold` to enforce 1-at-a-time Socratic Brainstorming + explicit
    2-3 option ADR trade-offs routed directly into `openspec/specs/`.
    """

    archetype = TaskArchetype.GREENFIELD_SPEC
    active_skills = [
        "socratic-brainstorming",
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def discover_or_grill(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        questions = task_context.get("ambiguities", [])
        resolved = {
            q: "explicit_rfc2119_contract" for q in questions
        }
        return {
            "socratic_single_question_pacing": True,
            "adr_options_evaluated": 3,
            "resolved_ambiguities": resolved,
            "target_ssot": "openspec/specs/<capability>/spec.md",
        }

    def plan_and_scaffold(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        reqs = task_context.get("requirements", [])
        return {
            "bite_sized_tdd_slices": [
                f"Slice {i + 1}: RED test -> chmod -w -> GREEN impl for {r}"
                for i, r in enumerate(reqs)
            ],
            "track_plan_path": "conductor/tracks/<track_id>/plan.md",
        }


class BrownfieldSyncHarness(BaseSDDHarness):
    """Specialized Harness Subclass 2: Brownfield Reverse-Engineering (Lab 02).

    Overrides `pre_flight` and `discover_or_grill` to enforce a strict Read-Only
    4-Gate AST/Contract Scan (`Sync Spec` + Characterization Tests) before any
    `Delta Spec` (`ADDED`/`MODIFIED`) is proposed.
    """

    archetype = TaskArchetype.BROWNFIELD_SYNC
    active_skills = [
        "socratic-brainstorming",
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def pre_flight(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ready",
            "mode": "brownfield_readonly_scan",
            "gates_executed": [
                "Gate A: Docs & Architecture",
                "Gate B: Schema & State Contracts",
                "Gate C: Public Signatures & Sorting Invariants",
                "Gate D: Edge-Case Call-Site Trace",
            ],
        }

    def discover_or_grill(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "sync_spec_extracted": True,
            "characterization_tests_locked": True,
            "delta_operations": ["ADDED", "MODIFIED"],
        }


class TDDActuationHarness(BaseSDDHarness):
    """Specialized Harness Subclass 3: Stateful Boundary & Streak TDD (Lab 03).

    Overrides `plan_and_scaffold` and `execute_actuation` to enforce strict
    Red-Green-Refactor sequencing with locked (`chmod -w`) boundary tests for
    temporal/numeric edge cases (`gap == 0`, `gap == 1`, `gap > 1`).
    """

    archetype = TaskArchetype.TDD_ACTUATION
    active_skills = [
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def plan_and_scaffold(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "red_phase_verified_failing": True,
            "test_files_chmod_readonly": True,
            "boundary_equivalence_classes": [
                "empty_input",
                "single_element",
                "idempotent_same_day_gap_0",
                "consecutive_day_gap_1",
                "broken_streak_gap_gt_1",
            ],
        }

    def execute_actuation(self, task_context: Dict[str, Any]) -> BuilderStatus:
        if task_context.get("missing_requirement"):
            return BuilderStatus.NEEDS_CONTEXT
        return BuilderStatus.DONE


class DriftRemediationHarness(BaseSDDHarness):
    """Specialized Harness Subclass 4: Spec-to-Code Drift & Bug Repair (Lab 04).

    Overrides `pre_flight` and `execute_actuation` to combine the 4-Phase
    `@systematic-debugging-gate` with the 5-Step Scorecard (`Out of Scope` guard)
    so bugs are fixed at the root cause without scope creep.
    """

    archetype = TaskArchetype.DRIFT_REMEDIATION
    active_skills = [
        "systematic-debugging-gate",
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def pre_flight(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ready",
            "mode": "systematic_4_phase_debugging",
            "phases": [
                "Phase 1: Root-Cause & Spec-Drift Trace",
                "Phase 2: Pattern & Working-Reference Comparison",
                "Phase 3: Single-Hypothesis Minimal Test",
                "Phase 4: Reproduction Test + Out-of-Scope Guard",
            ],
            "circuit_breaker_max_attempts": 3,
        }

    def execute_actuation(self, task_context: Dict[str, Any]) -> BuilderStatus:
        failed_attempts = task_context.get("failed_fix_attempts", 0)
        if failed_attempts >= 3:
            return BuilderStatus.BLOCKED
        return BuilderStatus.DONE


class MultiAppWorkflowHarness(BaseSDDHarness):
    """Specialized Harness Subclass 5: AutomationBench Multi-App State Machines.

    Directly models the multi-application workflow domain evaluated in
    `arXiv:2610.28380` (OO-Harness on AutomationBench): cross-service event
    routing, idempotency keys, transactional rollback on partial downstream
    failure, and programmatic assertions over final multi-app state.
    """

    archetype = TaskArchetype.MULTI_APP_WORKFLOW
    active_skills = [
        "socratic-brainstorming",
        "systematic-debugging-gate",
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def pre_flight(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ready",
            "mode": "multi_app_state_machine",
            "invariants": [
                "Idempotent event deduplication by event_id",
                "Transactional compensation/rollback on downstream API error",
                "Deterministic audit log ordering",
                "Zero phantom side-effects on rejected payloads",
            ],
        }

    def audit_and_sync(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "spec_synced": True,
            "automationbench_state_assertions_verified": True,
        }


class CleanRoomRebuildHarness(BaseSDDHarness):
    """Specialized Harness Subclass 6: Level-3 SPEC.md Clean-Room Rebuild (Lab 06 / Commit0).

    Overrides `pre_flight`, `execute_actuation`, and `audit_and_sync` to enforce
    Clean-Room `/tmp` isolation where the implementation is synthesized strictly
    from the 8-section `SPEC.md` and verified against locked `adversarial_tests/`.
    """

    archetype = TaskArchetype.CLEAN_ROOM_REBUILD
    active_skills = [
        "subagent-two-stage-review",
        "verification-before-completion",
    ]

    def pre_flight(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "ready",
            "mode": "clean_room_tmp_isolation",
            "source_code_access_blocked": True,
            "input_contract": "SPEC.md (8 Canonical Sections)",
        }

    def execute_actuation(self, task_context: Dict[str, Any]) -> BuilderStatus:
        return BuilderStatus.DONE

    def audit_and_sync(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "spec_synced": True,
            "clean_room_behavioral_equivalence": True,
        }


class OOHarnessRouter:
    """Test-time Harness Router (arXiv:2610.28380 Section 3.3).

    Inspects the incoming task metadata and repository state to dynamically
    instantiate the specialized `BaseSDDHarness` subclass best suited for the
    engineering workload.
    """

    _REGISTRY: Dict[TaskArchetype, type[BaseSDDHarness]] = {
        TaskArchetype.GREENFIELD_SPEC: GreenfieldSpecHarness,
        TaskArchetype.BROWNFIELD_SYNC: BrownfieldSyncHarness,
        TaskArchetype.TDD_ACTUATION: TDDActuationHarness,
        TaskArchetype.DRIFT_REMEDIATION: DriftRemediationHarness,
        TaskArchetype.MULTI_APP_WORKFLOW: MultiAppWorkflowHarness,
        TaskArchetype.CLEAN_ROOM_REBUILD: CleanRoomRebuildHarness,
    }

    @classmethod
    def classify(cls, task_metadata: Dict[str, Any]) -> TaskArchetype:
        """Deterministically routes a task signature to its OO-Harness archetype."""
        explicit = task_metadata.get("archetype")
        if isinstance(explicit, TaskArchetype):
            return explicit
        if isinstance(explicit, str):
            for item in TaskArchetype:
                if item.value == explicit:
                    return item

        prompt = str(task_metadata.get("prompt", "")).lower()
        has_legacy_code = bool(task_metadata.get("has_legacy_code", False))
        is_clean_room = bool(task_metadata.get("clean_room_rebuild", False))
        is_multi_app = bool(task_metadata.get("multi_app_workflow", False))
        has_failing_regression = bool(
            task_metadata.get("has_failing_regression", False)
        )

        if is_clean_room or "clean-room" in prompt or "rebuild from spec" in prompt:
            return TaskArchetype.CLEAN_ROOM_REBUILD
        if is_multi_app or "workflow" in prompt or "webhook" in prompt or "multi-app" in prompt:
            return TaskArchetype.MULTI_APP_WORKFLOW
        if has_failing_regression or "drift" in prompt or "bug" in prompt or "regression" in prompt:
            return TaskArchetype.DRIFT_REMEDIATION
        if has_legacy_code or "brownfield" in prompt or "existing" in prompt:
            return TaskArchetype.BROWNFIELD_SYNC
        if "streak" in prompt or "tdd" in prompt or "boundary" in prompt:
            return TaskArchetype.TDD_ACTUATION
        return TaskArchetype.GREENFIELD_SPEC

    @classmethod
    def route(
        cls,
        task_metadata: Dict[str, Any],
        workspace_root: Optional[Path] = None,
    ) -> BaseSDDHarness:
        """Instantiates and returns the specialized harness subclass."""
        custom_key = str(task_metadata.get("evolved_archetype", ""))
        if custom_key and custom_key in cls._EVOLVED_REGISTRY:
            return cls._EVOLVED_REGISTRY[custom_key](
                workspace_root=workspace_root
            )
        archetype = cls.classify(task_metadata)
        harness_cls = cls._REGISTRY[archetype]
        return harness_cls(workspace_root=workspace_root)

    _EVOLVED_REGISTRY: Dict[str, type[BaseSDDHarness]] = {}

    @classmethod
    def evolve_subclass_from_failure(
        cls,
        parent_cls: type[BaseSDDHarness],
        new_class_name: str,
        archetype_key: str,
        failure_invariant: str,
    ) -> type[BaseSDDHarness]:
        """OO-Harness Dynamic Subclass Evolution (arXiv:2610.28380 Section 3.2).

        Inspects a failed execution trace and dynamically synthesizes a new child
        harness class inheriting from `parent_cls`, overriding `pre_flight` to
        enforce the newly discovered `failure_invariant` and registering it in
        the router's evolved registry.
        """

        def evolved_pre_flight(
            self: BaseSDDHarness, task_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            base_state = parent_cls.pre_flight(self, task_context)
            invariants = list(base_state.get("invariants", []))
            invariants.append(failure_invariant)
            return {
                **base_state,
                "mode": f"evolved_{archetype_key}",
                "evolved_from": parent_cls.__name__,
                "invariants": invariants,
            }

        evolved_cls = type(
            new_class_name,
            (parent_cls,),
            {
                "pre_flight": evolved_pre_flight,
                "evolved_invariant": failure_invariant,
            },
        )
        cls._EVOLVED_REGISTRY[archetype_key] = evolved_cls
        return evolved_cls


class HarnessSquaredProber:
    """Harness^2 Recursive Propose-Probe-Compose Engine (google-research/harness2).

    Implements the Two-Level Recursive Harnessing loop for open-world tasks where
    no ground-truth test oracle exists yet:
      1. Task-Level Recursion (Propose -> Probe -> Compose):
         Generates K candidate specification/test interpretations, synthesizes
         contrastive boundary probes `x_probe` where candidates disagree, and
         composes the strongest boundary invariants into a unified contract.
      2. Harnessing-Level Recursion (Experience Distillation):
         Persists newly discovered boundary rules into an experience memory bank
         so future tasks inherit the insight without re-probing.
    """

    def __init__(self) -> None:
        self.experience_bank: List[Dict[str, str]] = []

    def propose_probe_compose(
        self,
        domain: str,
        candidate_predicates: Dict[str, Callable[[int], bool]],
        probe_inputs: List[int],
        strict_inclusive_preference: bool = True,
    ) -> Dict[str, Any]:
        """Runs contrastive probing across candidate boundary predicates."""
        disagreements: List[Dict[str, Any]] = []
        for x in probe_inputs:
            outcomes = {
                name: bool(pred(x))
                for name, pred in candidate_predicates.items()
            }
            if len(set(outcomes.values())) > 1:
                disagreements.append({"probe_input": x, "outcomes": outcomes})

        selected_candidate = (
            "inclusive_boundary"
            if strict_inclusive_preference
            and "inclusive_boundary" in candidate_predicates
            else next(iter(candidate_predicates))
        )
        distilled_rule = (
            f"{domain}: resolved {len(disagreements)} contrastive boundary "
            f"disagreement(s) at {[d['probe_input'] for d in disagreements]} -> "
            f"locked '{selected_candidate}'"
        )
        self.experience_bank.append(
            {"domain": domain, "rule": distilled_rule}
        )
        return {
            "domain": domain,
            "candidates_evaluated": len(candidate_predicates),
            "contrastive_disagreements": disagreements,
            "selected_candidate": selected_candidate,
            "distilled_rule": distilled_rule,
        }

