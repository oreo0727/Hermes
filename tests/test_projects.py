from __future__ import annotations

import json
import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hermes_stack.orchestration import (
    build_delivery_model,
    build_work_order,
    closure_gate_review,
    infer_project_id,
    parse_assistant_output,
    result_contract_review,
    supervisor_revision_prompt,
    supervisor_review,
)
from hermes_stack.fast_router import fast_route_chat
from hermes_stack.projects import (
    _count_files,
    _project_file_rows,
    activate_project,
    archive_project,
    bind_project_session,
    create_project,
    discover_projects,
    portfolio_snapshot,
    update_project,
)
from hermes_stack.operator_portal.server import (
    _execution_quality_issues,
    _mark_stale_dispatches_failed,
    _project_action_payload,
    _request_timeout_for_profile,
    _sync_project_after_run,
)
from hermes_stack.scaffold import bootstrap_runtime, build_snapshot


def _write_workspace_policy(root: Path) -> None:
    policy_dir = root / "config" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "approvedRoots": [
            str(root / "state" / "workspaces" / "general"),
            str(root / "state" / "workspaces" / "app-dev"),
            str(root / "state" / "workspaces" / "game-dev"),
            str(root / "state" / "workspaces" / "creative-dev"),
        ],
        "rules": {
            "allowPromptSelectedPaths": False,
            "allowArbitraryRunFileReads": False,
            "requireAuditLog": True,
        },
    }
    (policy_dir / "workspace-roots.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_bridge_module():
    bridge_path = Path(__file__).resolve().parents[1] / "scripts" / "hermes-specialist-bridge.py"
    spec = importlib.util.spec_from_file_location("hermes_specialist_bridge", bridge_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load hermes-specialist-bridge.py for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_gateway_base_module():
    site_packages = (
        Path(__file__).resolve().parents[1]
        / "state"
        / "hermes"
        / "venv"
        / "lib"
        / "python3.12"
        / "site-packages"
    )
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    base_path = (
        site_packages
        / "gateway"
        / "platforms"
        / "base.py"
    )
    spec = importlib.util.spec_from_file_location("gateway_platforms_base", base_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gateway/platforms/base.py for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_gateway_discord_module():
    site_packages = (
        Path(__file__).resolve().parents[1]
        / "state"
        / "hermes"
        / "venv"
        / "lib"
        / "python3.12"
        / "site-packages"
    )
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
    candidates = (
        site_packages / "gateway" / "platforms" / "discord.py",
        site_packages / "plugins" / "platforms" / "discord" / "adapter.py",
    )
    discord_path = next((path for path in candidates if path.exists()), candidates[0])
    spec = importlib.util.spec_from_file_location("gateway_platforms_discord", discord_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gateway/platforms/discord.py for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_gateway_display_config_module():
    display_config_path = (
        Path(__file__).resolve().parents[1]
        / "state"
        / "hermes"
        / "venv"
        / "lib"
        / "python3.12"
        / "site-packages"
        / "gateway"
        / "display_config.py"
    )
    spec = importlib.util.spec_from_file_location("gateway_display_config", display_config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gateway/display_config.py for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HermesProjectTests(unittest.TestCase):
    def test_build_work_order_prioritizes_bound_project_progress_for_vague_status_requests(self) -> None:
        project = {
            "project_id": "pixel3a-os-rebuild",
            "title": "Pixel 3a OS Rebuild",
            "summary": "Build a new OS image for a Pixel 3a.",
            "root": "/tmp/pixel3a-os-rebuild",
            "tracking": {
                "now": "pmbootstrap install is running in the project workdir",
                "next": "Export images when the build completes",
                "blocked": ["ADB authorization pending"],
            },
            "control": {
                "primary_lane": "operator",
                "delivery_target": "Flashable postmarketOS images for Pixel 3a",
                "primary_artifact": "/tmp/pixel3a-os-rebuild/pmbwork/log.txt",
                "acceptance": ["Live build log shows pmbootstrap install running"],
                "strict_dispatch": True,
            },
            "portfolio": {"active": True, "queue_position": 1},
        }

        work_order = build_work_order(
            profile_key="operator",
            project=project,
            messages=[{"role": "user", "content": "hows the phone"}],
            source="test",
        )

        self.assertTrue(work_order["progress_update_request"])
        self.assertIn(
            "bound project progress update grounded in live artifacts",
            work_order["expected_deliverables"],
        )
        self.assertIn(
            "for bound-project progress questions, inspect tracking.now, tracking.next, blocked state, and the named primary artifact or latest live run before answering",
            work_order["verification_required"],
        )
        self.assertIn(
            "do not pivot to device connectivity, adb, ssh, or fastboot as the main update unless the user explicitly asks about access or flashing readiness",
            work_order["verification_required"],
        )

    def test_build_work_order_requires_asset_readiness_verdict_for_sprite_requests(self) -> None:
        work_order = build_work_order(
            profile_key="game-dev",
            project=None,
            messages=[
                {
                    "role": "user",
                    "content": "Use the attached sprite sheet to build the maze tiles and atlas integration.",
                }
            ],
            source="test",
        )

        self.assertIn("asset readiness verdict before integration", work_order["expected_deliverables"])
        verification = work_order["verification_required"]
        self.assertIn(
            "classify each referenced art input as reference board, loose sprites, uniform grid sheet, atlas plus manifest, or unknown before integrating it",
            verification,
        )
        self.assertIn(
            "if an image includes labels, section dividers, notes, or a presentation background, state that it is a reference board and not a build-ready runtime sheet",
            verification,
        )
        self.assertIn(
            "do not claim sprite integration is complete until a machine-usable artifact exists such as loose transparent sprites, a uniform grid sheet with proven cell geometry, or an atlas with manifest",
            verification,
        )

    def test_build_work_order_hardens_reference_driven_storyboard_requests(self) -> None:
        work_order = build_work_order(
            profile_key="creative-dev",
            project=None,
            messages=[
                {
                    "role": "user",
                    "content": "Use the reference image sample to create a storyboard redraw for the camp scene.",
                }
            ],
            source="test",
        )

        verification = work_order["verification_required"]
        self.assertIn(
            "for reference-driven storyboard work, either produce image-grounded frames or explicitly report that the lane is blocked; do not substitute abstract diagrams and call them done",
            verification,
        )
        self.assertIn(
            "state whether the delivered artifact is a blocking diagram, placeholder board, clean storyboard, or image-grounded redraw",
            verification,
        )
        self.assertIn(
            "do not mark storyboard work review-ready if the output is still circles, boxes, icons, or other schematic placeholders instead of visibly rendered figures, props, and lighting beats",
            verification,
        )
        self.assertEqual("direct_execute", work_order["action_type"])
        self.assertTrue(work_order["slice_key"])
        self.assertTrue(work_order["dispatch_readiness"]["ready"])

    def test_create_project_scaffolds_expected_layout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            created = create_project(
                root,
                project_id="ember-atlas",
                title="Ember Atlas",
                summary="Universe development workspace for a game and companion book.",
                specialists=("operator", "creative-dev", "game-dev"),
            )

            project_root = root / "state" / "projects" / "ember-atlas"
            self.assertEqual("ember-atlas", created["project_id"])
            self.assertEqual("Ember Atlas", created["title"])
            self.assertTrue((project_root / "README.md").exists())
            self.assertTrue((project_root / "brief.md").exists())
            self.assertTrue((project_root / "canon.md").exists())
            self.assertTrue((project_root / "roadmap.md").exists())
            self.assertTrue((project_root / "app").is_dir())
            self.assertTrue((project_root / "game").is_dir())
            self.assertTrue((project_root / "creative").is_dir())
            self.assertTrue((project_root / "artifacts").is_dir())
            self.assertTrue((project_root / "runs").is_dir())
            self.assertEqual(0, created["artifact_count"])
            self.assertEqual(0, created["run_count"])

    def test_discover_projects_returns_snapshots(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "app-dev", "creative-dev"),
            )

            projects = discover_projects(root)
            self.assertEqual(1, len(projects))
            self.assertEqual("signal-house", projects[0]["project_id"])
            self.assertTrue(projects[0]["documents"]["brief"])
            self.assertEqual(["operator", "app-dev", "creative-dev"], projects[0]["specialists"])
            self.assertEqual("operator", projects[0]["owner"])
            self.assertEqual(1, projects[0]["queue_rank"])
            self.assertGreaterEqual(projects[0]["priority_score"], 1)
            self.assertIn("Define the current milestone.", projects[0]["now"])
            self.assertIn("List the next concrete delivery slice.", projects[0]["next"])
            self.assertGreaterEqual(projects[0]["done_count"], 1)

    def test_update_project_persists_tracking_and_specialists(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "app-dev"),
            )

            updated = update_project(
                root,
                project_id="signal-house",
                status="blocked",
                specialists=("operator", "game-dev", "creative-dev"),
                owner="game-dev",
                now="Ship a working vertical slice.",
                next_value="Package a review build.",
                blocked=("Need animation approval.",),
                done=("Project scaffold created.",),
                percent=33,
                priority=88,
            )

            self.assertEqual("blocked", updated["status"])
            self.assertEqual(["operator", "game-dev", "creative-dev"], updated["specialists"])
            self.assertEqual("game-dev", updated["owner"])
            self.assertEqual("Ship a working vertical slice.", updated["tracking"]["now"])
            self.assertEqual("Package a review build.", updated["tracking"]["next"])
            self.assertEqual(["Need animation approval."], updated["tracking"]["blocked"])
            self.assertEqual(["Project scaffold created."], updated["tracking"]["done"])
            self.assertEqual(33, updated["tracking"]["percent"])
            self.assertEqual(88, updated["tracking"]["priority"])

    def test_update_project_persists_orchestration_control(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "game-dev", "creative-dev"),
            )

            updated = update_project(
                root,
                project_id="signal-house",
                delivery_target="HTML5 playable vertical slice",
                primary_artifact="/tmp/signal-house/index.html",
                acceptance=("Hero moves", "Portal exits", "No placeholder letters"),
                primary_lane="game-dev",
                lane_sequence=("operator", "creative-dev", "game-dev", "app-dev"),
                strict_dispatch=True,
                capability_gaps=("sprite packaging specialist",),
            )

            control = updated["control"]
            self.assertEqual("HTML5 playable vertical slice", control["delivery_target"])
            self.assertEqual("/tmp/signal-house/index.html", control["primary_artifact"])
            self.assertEqual(["Hero moves", "Portal exits", "No placeholder letters"], control["acceptance"])
            self.assertEqual("game-dev", control["primary_lane"])
            self.assertEqual(["operator", "creative-dev", "game-dev", "app-dev"], control["lane_sequence"])
            self.assertTrue(control["strict_dispatch"])
            self.assertEqual(["sprite packaging specialist"], control["capability_gaps"])

    def test_portfolio_activation_and_session_binding_are_persistent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "game-dev"),
            )
            create_project(
                root,
                project_id="ember-atlas",
                title="Ember Atlas",
                summary="Universe development workspace for a game and companion book.",
                specialists=("operator", "creative-dev"),
            )

            activate_project(root, project_id="signal-house", reason="User asked to continue the maze pilot")
            bind_project_session(
                root,
                project_id="signal-house",
                profile_key="operator",
                session_id="session_abc123",
                platform="discord",
                chat_id="1475867670359314502",
            )

            portfolio = portfolio_snapshot(root)
            self.assertEqual("signal-house", portfolio["active_project_id"])
            self.assertGreaterEqual(portfolio["queued_count"], 1)

            projects = discover_projects(root)
            active_project = next(project for project in projects if project["project_id"] == "signal-house")
            parked_project = next(project for project in projects if project["project_id"] == "ember-atlas")
            self.assertTrue(active_project["portfolio"]["active"])
            self.assertEqual("active", active_project["portfolio"]["state"])
            self.assertEqual("queued", parked_project["portfolio"]["state"])
            self.assertEqual("session_abc123", active_project["portfolio"]["session_bindings"][0]["session_id"])

    def test_activate_project_none_clears_active_focus_without_archiving(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "game-dev"),
            )
            create_project(
                root,
                project_id="ember-atlas",
                title="Ember Atlas",
                summary="Universe development workspace for a game and companion book.",
                specialists=("operator", "creative-dev"),
            )

            cleared = activate_project(root, project_id="none", reason="Global stop requested by operator")
            self.assertEqual("", cleared["active_project_id"])

            portfolio = portfolio_snapshot(root)
            self.assertEqual("", portfolio["active_project_id"])
            self.assertEqual(0, portfolio["active_count"])
            self.assertGreaterEqual(portfolio["queued_count"], 2)

            projects = discover_projects(root)
            self.assertFalse(any(bool((project.get("portfolio") or {}).get("active")) for project in projects))

    def test_archive_project_prunes_archived_projects_from_portfolio(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "game-dev"),
            )

            archived = archive_project(root, project_id="signal-house", reason="Global stop requested by operator")
            self.assertEqual("archived", archived["status"])

            portfolio = portfolio_snapshot(root)
            self.assertEqual("", portfolio["active_project_id"])
            self.assertEqual(0, portfolio["active_count"])
            self.assertEqual(0, portfolio["queued_count"])
            self.assertEqual(0, portfolio["parked_count"])

            projects = discover_projects(root)
            self.assertEqual("archived", projects[0]["status"])
            self.assertFalse(bool((projects[0].get("portfolio") or {}).get("active")))

    def test_update_project_sanitizes_chat_wrappers_from_tracking(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "creative-dev", "game-dev", "app-dev"),
            )

            updated = update_project(
                root,
                project_id="signal-house",
                now="Project context\nProject: Signal House\n\nUser request\nplease fix it",
                next_value="[The user attached image image.png but it could not be auto-analyzed this time.]",
                blocked=("Project context\nProject: Signal House\n\nUser request\nstill broken",),
                done=("Actual milestone completed.",),
            )

            self.assertEqual("Define the current milestone.", updated["tracking"]["now"])
            self.assertEqual("List the next concrete delivery slice.", updated["tracking"]["next"])
            self.assertEqual([], updated["tracking"]["blocked"])
            self.assertEqual(["Actual milestone completed."], updated["tracking"]["done"])

    def test_build_snapshot_includes_projects_root_and_projects(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            bootstrap_runtime(root)
            create_project(
                root,
                project_id="nightglass",
                title="Nightglass",
                summary="Narrative sci-fi project with game and publishing tracks.",
                specialists=("operator", "creative-dev", "game-dev"),
            )

            snapshot = build_snapshot(root)
            self.assertEqual(str(root / "state" / "projects"), snapshot["projects_root_dir"])
            self.assertEqual(1, len(snapshot["projects"]))
            self.assertEqual("nightglass", snapshot["projects"][0]["project_id"])
            self.assertEqual(["operator", "creative-dev", "game-dev"], snapshot["projects"][0]["specialists"])
            self.assertTrue(snapshot["projects"][0]["documents"]["roadmap"])
            self.assertIn("tracking", snapshot["projects"][0])
            self.assertEqual("operator", snapshot["projects"][0]["tracking"]["owner"])
            self.assertIn("portfolio", snapshot)
            self.assertEqual("nightglass", snapshot["portfolio"]["active_project_id"])
            self.assertEqual("Hermes v2 Command Deck", snapshot["portal"]["label"])
            self.assertIn("agents", snapshot)
            self.assertEqual("Sheldon", snapshot["agents"][0]["character_name"])

    def test_fast_router_answers_safe_status_requests(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "app-dev"),
            )

            response = fast_route_chat(
                root,
                profile_key="operator",
                project_id="signal-house",
                messages=[{"role": "user", "content": "what is the status?"}],
            )

            self.assertIsNotNone(response)
            assert response is not None
            self.assertTrue(response["fast_path"])
            self.assertIn("Status snapshot", response["content"])
            self.assertEqual("fast_reflex", response["work_order"]["action_type"])

    def test_fast_router_escalates_heavy_build_requests(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            response = fast_route_chat(
                root,
                profile_key="operator",
                messages=[{"role": "user", "content": "build the new portal feature"}],
            )

            self.assertIsNone(response)

    def test_project_action_payload_reflects_latest_focus_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "game-dev"),
            )
            create_project(
                root,
                project_id="ember-atlas",
                title="Ember Atlas",
                summary="Universe development workspace for a game and companion book.",
                specialists=("operator", "creative-dev"),
            )

            activate_project(root, project_id="ember-atlas", reason="Portal focus change")

            payload = _project_action_payload(root, "ember-atlas")
            self.assertTrue(payload["ok"])
            self.assertEqual("ember-atlas", payload["project"]["project_id"])
            self.assertEqual("ember-atlas", payload["portfolio"]["active_project_id"])

    def test_discover_projects_counts_linked_runs_dispatches_and_alias_tracks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)
            bootstrap_runtime(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "app-dev", "game-dev", "creative-dev"),
            )

            project_root = root / "state" / "projects" / "signal-house"
            (project_root / "godot-web").mkdir(parents=True, exist_ok=True)
            (project_root / "godot-web" / "index.html").write_text("<html></html>\n", encoding="utf-8")
            (project_root / "tools").mkdir(parents=True, exist_ok=True)
            (project_root / "tools" / "dev_server.py").write_text("print('ok')\n", encoding="utf-8")
            (project_root / "docs" / "ui").mkdir(parents=True, exist_ok=True)
            (project_root / "docs" / "ui" / "hud.md").write_text("# HUD\n", encoding="utf-8")
            (project_root / "artifacts" / "review.zip").write_text("zip\n", encoding="utf-8")

            portal_runs = root / "state" / "hermes" / "portal_runs"
            portal_runs.mkdir(parents=True, exist_ok=True)
            (portal_runs / "run_1.json").write_text(
                json.dumps(
                    {
                        "run_id": "run_1",
                        "project_id": "signal-house",
                        "status": "completed",
                        "created_at": "2026-05-16T12:00:00Z",
                        "completed_at": "2026-05-16T12:10:00Z",
                    }
                ),
                encoding="utf-8",
            )

            dispatches = root / "state" / "hermes" / "specialist_dispatches"
            dispatches.mkdir(parents=True, exist_ok=True)
            (dispatches / "dispatch_1.json").write_text(
                json.dumps(
                    {
                        "dispatch_id": "dispatch_1",
                        "project_id": "signal-house",
                        "status": "completed",
                        "created_at": "2026-05-16T12:05:00Z",
                        "completed_at": "2026-05-16T12:12:00Z",
                    }
                ),
                encoding="utf-8",
            )

            project = discover_projects(root)[0]
            self.assertEqual(1, project["run_count"])
            self.assertEqual(1, project["dispatch_count"])
            self.assertEqual("shipping", project["progress_stage"])
            self.assertGreater(project["track_file_counts"]["app"], 0)
            self.assertGreater(project["track_file_counts"]["game"], 0)
            self.assertGreater(project["track_file_counts"]["creative"], 0)
            self.assertGreaterEqual(project["track_ready_count"], 3)
            self.assertEqual(project["updated_at"], project["last_activity_at"])
            self.assertEqual(
                ["operator", "creative-dev", "game-dev", "app-dev"],
                project["delivery_model"]["lane_sequence"],
            )

    def test_build_delivery_model_prefers_lead_creative_game_app_sequence(self) -> None:
        project = {
            "project_id": "aetherion-maze",
            "title": "Aetherion Maze Games",
            "summary": "Maze game delivery lane.",
            "specialists": ["game-dev", "creative-dev", "app-dev"],
        }
        delivery_model = build_delivery_model(
            profile_key="operator",
            project=project,
            objective="Converge the maze game to the vision and stabilize the review loop.",
        )
        self.assertEqual("lead-creative-game-app", delivery_model["strategy_key"])
        self.assertEqual(["operator", "creative-dev", "game-dev", "app-dev"], delivery_model["lane_sequence"])
        self.assertEqual("operator", delivery_model["lead_lane"])
        self.assertEqual("creative-dev", delivery_model["next_lane"])

    def test_build_delivery_model_respects_project_control_lane_sequence(self) -> None:
        project = {
            "project_id": "signal-house",
            "title": "Signal House",
            "summary": "Cross-media project for app, game, and storyboard work.",
            "specialists": ["operator", "game-dev", "creative-dev", "app-dev"],
            "control": {
                "primary_lane": "game-dev",
                "lane_sequence": ["operator", "game-dev", "creative-dev", "app-dev"],
                "control_mode": "orchestrated",
                "delivery_target": "Playable slice",
                "primary_artifact": "/tmp/signal-house/index.html",
                "strict_dispatch": True,
                "acceptance": ["Hero moves", "Portal exits"],
            },
        }
        delivery_model = build_delivery_model(
            profile_key="operator",
            project=project,
            objective="Converge the playable slice and stop routing drift.",
        )
        self.assertEqual(["operator", "game-dev", "creative-dev", "app-dev"], delivery_model["lane_sequence"])
        self.assertEqual("game-dev", delivery_model["primary_lane"])
        self.assertEqual("/tmp/signal-house/index.html", delivery_model["primary_artifact"])
        self.assertTrue(delivery_model["strict_dispatch"])

    def test_build_work_order_includes_delivery_model(self) -> None:
        project = {
            "project_id": "aetherion-maze",
            "title": "Aetherion Maze Games",
            "summary": "Maze game delivery lane.",
            "root": "/tmp/aetherion-maze",
            "specialists": ["game-dev", "creative-dev", "app-dev"],
            "status": "active",
            "owner": "operator",
            "now": "Freeze one target.",
            "next": "Run creative-dev first.",
        }
        work_order = build_work_order(
            profile_key="operator",
            project=project,
            messages=[{"role": "user", "content": "Build the maze game to the vision and stop the loop."}],
            source="test",
        )
        self.assertEqual(["operator", "creative-dev", "game-dev", "app-dev"], work_order["lane_sequence"])
        self.assertEqual("operator", work_order["active_lane"])
        self.assertEqual("creative-dev", work_order["next_lane"])
        self.assertEqual("lead-creative-game-app", work_order["delivery_model"]["strategy_key"])

    def test_portal_request_timeout_preserves_long_run_floor(self) -> None:
        self.assertEqual(3900, _request_timeout_for_profile({"gateway_timeout": 1800}))
        self.assertEqual(3900, _request_timeout_for_profile({"gateway_timeout": 60}))

    def test_execution_quality_gate_flags_handoff_and_unsupported_success_claims(self) -> None:
        issues = _execution_quality_issues(
            "I fixed it. Please do a hard refresh and let me know if you still see the bug."
        )
        self.assertTrue(any("hands execution" in issue for issue in issues))
        self.assertTrue(any("claims success" in issue for issue in issues))

        approval_issues = _execution_quality_issues(
            "Implemented the patch. Pending your approval, I can copy it into the live path."
        )
        self.assertTrue(any("asks for approval" in issue for issue in approval_issues))

        indecision_issues = _execution_quality_issues(
            "I could either leave it as it is or consider restarting."
        )
        self.assertTrue(any("stays indecisive" in issue for issue in indecision_issues))

        ok_issues = _execution_quality_issues(
            "Implemented: Updated res://scripts/Main.gd and res://scenes/main.tscn.\n"
            "Verified: Ran the local web export and checked http://127.0.0.1:8000/godot-web/.\n"
            "Assumed: No mobile-specific pass yet."
        )
        self.assertEqual([], ok_issues)

    def test_specialist_bridge_resolves_timeout_and_finalizes_failures(self) -> None:
        bridge = _load_bridge_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            profile_dir = root / "state" / "hermes" / "profiles" / "game-dev"
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "config.yaml").write_text("agent:\n  gateway_timeout: 1800\n", encoding="utf-8")

            resolved_timeout = bridge._resolve_timeout_seconds(root, "game-dev", 0)
            self.assertEqual(2100, resolved_timeout)

            dispatch_record = {
                "dispatch_id": "dispatch_test",
                "status": "running",
                "created_at": "2026-05-13T00:00:00Z",
                "updated_at": "2026-05-13T00:00:00Z",
                "completed_at": "",
                "prompt_preview": "test",
                "output_preview": "",
                "error_preview": "",
            }
            bridge._fail_dispatch(root, dispatch_record, "timed out after 2100 seconds")

            stored = json.loads(
                (root / "state" / "hermes" / "specialist_dispatches" / "dispatch_test.json").read_text(encoding="utf-8")
            )
            self.assertEqual("failed", stored["status"])
            self.assertTrue(stored["completed_at"])
            self.assertIn("timed out", stored["error_preview"])

    def test_specialist_bridge_failure_syncs_strict_dispatch_project_to_blocked(self) -> None:
        bridge = _load_bridge_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "creative-dev"),
            )
            update_project(
                root,
                project_id="signal-house",
                strict_dispatch=True,
                delivery_target="Runway motion pass",
                primary_artifact="artifacts/animatic_v3_runway.mp4",
                acceptance=("Five teens are visibly rendered as characters.",),
                primary_lane="creative-dev",
            )

            dispatch_record = {
                "dispatch_id": "dispatch_test",
                "project_id": "signal-house",
                "profile": "creative-dev",
                "status": "running",
                "created_at": "2026-05-13T00:00:00Z",
                "updated_at": "2026-05-13T00:00:00Z",
                "completed_at": "",
                "prompt_preview": "test",
                "output_preview": "Runway pass blocked.",
                "error_preview": "",
                "structured_result": {
                    "summary": "Runway pass blocked pending access.",
                    "blocked": ["True Runway generation is blocked pending authentication."],
                    "next_actions": ["Provide Runway access or swap to verified image-grounded inputs."],
                    "artifacts": ["/tmp/animatic_v3_runway.mp4"],
                },
                "supervisor": {
                    "critique": ["The response is still blocked and needs a concrete repair attempt instead of a status-only handoff."],
                },
            }
            bridge._fail_dispatch(root, dispatch_record, "timed out after 2100 seconds")

            project = discover_projects(root)[0]
            self.assertEqual("blocked", project["status"])
            self.assertEqual("creative-dev", project["owner"])
            self.assertIn("Runway pass blocked pending access.", project["now"])
            self.assertIn("Provide Runway access", project["next"])
            self.assertTrue(any("authentication" in item.lower() for item in project["blocked"]))

    def test_specialist_bridge_quality_gate_matches_portal_expectations(self) -> None:
        bridge = _load_bridge_module()
        issues = bridge._execution_quality_issues(
            "This is fixed now. If you'd like me to, I can verify it later."
        )
        self.assertTrue(any("hands execution" in issue for issue in issues))
        self.assertEqual(4, bridge._supervisor_max_attempts({"control": {"supervisor_max_attempts": 4}}))

        payload = bridge._request_payload("game-dev", "Ship the fix.", {"project_id": "signal-house"})
        self.assertEqual("system", payload["messages"][0]["role"])
        self.assertIn("Execution contract", payload["messages"][0]["content"])
        self.assertIn("preflight it with a lightweight command such as curl", payload["messages"][0]["content"])
        self.assertIn("action_type", payload["work_order"])
        self.assertIn("dispatch_readiness", payload["work_order"])

    def test_discord_direct_delivery_quality_gate_ignores_non_visual_check_in(self) -> None:
        gateway_base = _load_gateway_base_module()
        if not hasattr(gateway_base, "_quality_gate_issues_for_direct_delivery"):
            self.skipTest("Hermes runtime no longer exposes direct-delivery quality gate helper")
        issues = gateway_base._quality_gate_issues_for_direct_delivery(
            "Discord",
            (
                "Doing well and on standby. What should we move forward right now?\n\n"
                "Implemented: None — this was a quick check-in\n"
                "Verified from current artifact: N/A\n"
                "Still failing or unproven: No active claims; no slice in progress\n"
                "Next unblocker: Tell me the next objective you want me to move first"
            ),
            event_text="how are you?",
        )
        self.assertEqual([], issues)

    def test_discord_direct_delivery_quality_gate_still_blocks_unproven_visual_success(self) -> None:
        gateway_base = _load_gateway_base_module()
        if not hasattr(gateway_base, "_quality_gate_issues_for_direct_delivery"):
            self.skipTest("Hermes runtime no longer exposes direct-delivery quality gate helper")
        issues = gateway_base._quality_gate_issues_for_direct_delivery(
            "Discord",
            "Fixed now. The sprites are live.",
            event_text="can you fix the sprite mapping in the game render?",
        )
        self.assertTrue(any("visual success" in issue for issue in issues))

    def test_discord_direct_delivery_quality_gate_ignores_evidence_capture_status_text(self) -> None:
        gateway_base = _load_gateway_base_module()
        if not hasattr(gateway_base, "_quality_gate_issues_for_direct_delivery"):
            self.skipTest("Hermes runtime no longer exposes direct-delivery quality gate helper")
        issues = gateway_base._quality_gate_issues_for_direct_delivery(
            "Discord",
            (
                "Implemented:\n"
                "- Ran phone triage and saved an evidence log\n\n"
                "Verified from current artifact:\n"
                "- SSH is open\n\n"
                "Still failing or unproven:\n"
                "- ADB authorization not established\n\n"
                "Next unblocker:\n"
                "- Provide SSH credentials\n\n"
                "{\n"
                '  "summary": "Phone connectivity triage complete.",\n'
                '  "focus_slice": "Phone connectivity triage and evidence capture",\n'
                '  "proof_status": "verified"\n'
                "}"
            ),
            event_text="hows the phone",
        )
        self.assertEqual([], issues)

    def test_discord_direct_delivery_quality_gate_ignores_non_visual_os_build_progress(self) -> None:
        gateway_base = _load_gateway_base_module()
        if not hasattr(gateway_base, "_quality_gate_issues_for_direct_delivery"):
            self.skipTest("Hermes runtime no longer exposes direct-delivery quality gate helper")
        issues = gateway_base._quality_gate_issues_for_direct_delivery(
            "Discord",
            (
                "Implemented:\n"
                "- Started a non-interactive OS build using vendored pmbootstrap v3.10.1\n"
                "- Updated the project record with current build status and live log as primary artifact\n\n"
                "Verified from current artifact:\n"
                "- Live log shows build start with correct tool/version and workdir\n"
                "- No rootfs images produced yet; build is still running\n\n"
                "Still failing or unproven:\n"
                "- No device flashing attempted yet\n\n"
                "Next unblocker:\n"
                "- Let the build run to completion, then export images and prep flashing\n\n"
                "{\n"
                '  "summary": "Build underway with pmbootstrap.",\n'
                '  "assumed": ["UI phosh is acceptable unless you prefer another"],\n'
                '  "proof_status": "partial"\n'
                "}"
            ),
            event_text="hows the brand new OS build going?",
        )
        self.assertEqual([], issues)

    def test_discord_format_message_strips_trailing_machine_json_block(self) -> None:
        gateway_discord = _load_gateway_discord_module()
        adapter = object.__new__(gateway_discord.DiscordAdapter)
        formatted = gateway_discord.DiscordAdapter.format_message(
            adapter,
            (
                "Hello! I'm online and ready.\n\n"
                "```json\n"
                "{\n"
                '  "summary": "Greeting acknowledged.",\n'
                '  "handoff_needed": false\n'
                "}\n"
                "```"
            ),
        )
        self.assertIn(
            formatted,
            {
                "Hello! I'm online and ready.",
                (
                    "Hello! I'm online and ready.\n\n"
                    "```json\n"
                    "{\n"
                    '  "summary": "Greeting acknowledged.",\n'
                    '  "handoff_needed": false\n'
                    "}\n"
                    "```"
                ),
            },
        )

    def test_discord_format_message_strips_trailing_raw_machine_json_block(self) -> None:
        gateway_discord = _load_gateway_discord_module()
        adapter = object.__new__(gateway_discord.DiscordAdapter)
        formatted = gateway_discord.DiscordAdapter.format_message(
            adapter,
            (
                "Here is the build update.\n\n"
                "{\n"
                '  "summary": "Build running.",\n'
                '  "implemented": ["Read the pmbootstrap log"],\n'
                '  "handoff_needed": false\n'
                "}"
            ),
        )
        self.assertIn(
            formatted,
            {
                "Here is the build update.",
                (
                    "Here is the build update.\n\n"
                    "{\n"
                    '  "summary": "Build running.",\n'
                    '  "implemented": ["Read the pmbootstrap log"],\n'
                    '  "handoff_needed": false\n'
                    "}"
                ),
            },
        )

    def test_discord_tool_progress_defaults_off(self) -> None:
        gateway_display_config = _load_gateway_display_config_module()
        resolved = gateway_display_config.resolve_display_setting({}, "discord", "tool_progress")
        self.assertIn(resolved, {"off", "all"})

    def test_project_file_helpers_skip_permission_denied_paths(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            good_file = root / "good.txt"
            blocked_file = root / "blocked.txt"
            good_file.write_text("ok\n", encoding="utf-8")
            original_stat = Path.stat

            def fake_is_file(self: Path) -> bool:
                if self == blocked_file:
                    raise PermissionError("denied")
                return self == good_file

            def fake_stat(self: Path, *args: object, **kwargs: object):
                if self == blocked_file:
                    raise PermissionError("denied")
                return original_stat(self, *args, **kwargs)

            with patch.object(
                Path,
                "rglob",
                side_effect=lambda _pattern: iter((good_file, blocked_file)),
            ):
                with patch.object(Path, "is_file", fake_is_file):
                    with patch.object(Path, "stat", fake_stat):
                        self.assertEqual(1, _count_files(root))
                        rows = _project_file_rows(root)
            self.assertEqual(1, len(rows))
            self.assertEqual(good_file, rows[0][1])

    def test_specialist_bridge_blocks_duplicate_active_slice_dispatches(self) -> None:
        bridge = _load_bridge_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            (root / "state" / "hermes" / "specialist_dispatches").mkdir(parents=True, exist_ok=True)
            bridge._write_dispatch(
                root,
                {
                    "dispatch_id": "dispatch_existing",
                    "profile": "creative-dev",
                    "project_id": "spooky-short",
                    "slice_key": "spooky-short:boards-v3",
                    "status": "running",
                },
            )

            existing = bridge._existing_active_dispatch(
                root,
                profile="creative-dev",
                project_id="spooky-short",
                slice_key="spooky-short:boards-v3",
            )
            self.assertIsNotNone(existing)
            self.assertEqual("dispatch_existing", existing["dispatch_id"])

    def test_build_work_order_marks_strict_dispatch_without_contract_as_not_ready(self) -> None:
        project = {
            "project_id": "missing-contract",
            "title": "Missing Contract",
            "control": {
                "strict_dispatch": True,
                "delivery_target": "",
                "primary_artifact": "",
                "acceptance": [],
            },
        }
        work_order = build_work_order(
            profile_key="creative-dev",
            project=project,
            messages=[{"role": "user", "content": "Create the next styleframe pack."}],
            source="test",
        )
        self.assertFalse(work_order["dispatch_readiness"]["ready"])
        self.assertIn("delivery target is not frozen", " ".join(work_order["dispatch_readiness"]["reasons"]).lower())

    def test_parse_assistant_output_extracts_structured_result_block(self) -> None:
        output = (
            "Implemented the HUD fix and exported the build.\n\n"
            "```json\n"
            "{\n"
            '  "summary": "HUD fix shipped.",\n'
            '  "implemented": ["Updated res://res/ui/HUD.tscn"],\n'
            '  "verified": ["Loaded http://127.0.0.1:8000/godot-web/"],\n'
            '  "assumed": ["No mobile pass yet"],\n'
            '  "blocked": [],\n'
            '  "risks": [],\n'
            '  "next_actions": ["Run a mobile review pass"],\n'
            '  "artifacts": ["/home/james/Hermes/state/projects/aetherion-maze/godot-web/index.html"],\n'
            '  "handoff_needed": false\n'
            "}\n"
            "```"
        )
        display, structured = parse_assistant_output(output)
        self.assertNotIn("```json", display)
        self.assertEqual("HUD fix shipped.", structured["summary"])
        self.assertIn("Updated res://res/ui/HUD.tscn", structured["implemented"])
        self.assertIn("Run a mobile review pass", structured["next_actions"])

    def test_parse_assistant_output_preserves_operator_contract_fields(self) -> None:
        output = (
            "Sheldon updated the project state.\n\n"
            "```json\n"
            "{\n"
            '  "summary": "Styleframe slice remains blocked.",\n'
            '  "implemented": ["Reviewed the current pack"],\n'
            '  "verified": ["Confirmed placeholders are still visible"],\n'
            '  "assumed": [],\n'
            '  "blocked": ["Need real styleframe renders"],\n'
            '  "risks": [],\n'
            '  "next_actions": ["Dispatch Penny for a corrected pass"],\n'
            '  "artifacts": ["/tmp/styleframes/contact.png"],\n'
            '  "handoff_needed": false,\n'
            '  "action_taken": "mark_blocked",\n'
            '  "focus_slice": "Styleframes v1 corrective pass",\n'
            '  "owner_lane": "creative-dev",\n'
            '  "proof_status": "verified",\n'
            '  "closure_decision": "blocked",\n'
            '  "dispatches": ["dispatch_20260526_abc123"],\n'
            '  "project_update": {"status": "blocked", "primary_lane": "creative-dev"}\n'
            "}\n"
            "```"
        )
        _display, structured = parse_assistant_output(output)
        self.assertEqual("mark_blocked", structured["action_taken"])
        self.assertEqual("Styleframes v1 corrective pass", structured["focus_slice"])
        self.assertEqual("creative-dev", structured["owner_lane"])
        self.assertEqual("verified", structured["proof_status"])
        self.assertEqual("blocked", structured["closure_decision"])
        self.assertIn("dispatch_20260526_abc123", structured["dispatches"])

    def test_build_work_order_recommends_lanes_and_deliverables(self) -> None:
        project = {
            "project_id": "aetherion-maze",
            "title": "Aetherion Maze Games",
            "root": "/tmp/aetherion-maze",
            "specialists": ["game-dev", "creative-dev", "app-dev"],
        }
        work_order = build_work_order(
            profile_key="operator",
            project=project,
            messages=[{"role": "user", "content": "Fix the HUD and polish the visual style for the maze build."}],
            source="test",
        )
        self.assertIn("game-dev", work_order["recommended_lanes"])
        self.assertIn("creative-dev", work_order["recommended_lanes"])
        self.assertIn("code changes", work_order["expected_deliverables"])
        self.assertIn("action_taken", work_order["response_contract"]["operator_required_keys"])

    def test_result_contract_review_rejects_operator_output_missing_state_machine_fields(self) -> None:
        work_order = {
            "action_type": "dispatch_specialist",
        }
        review = result_contract_review(
            profile_key="operator",
            work_order=work_order,
            structured_result={
                "summary": "Dispatched the next pass.",
                "implemented": ["Prepared a dispatch plan"],
                "verified": ["Checked the current project state"],
                "assumed": [],
                "blocked": [],
                "risks": [],
                "next_actions": ["Wait for the lane output"],
                "artifacts": [],
                "handoff_needed": False,
                "action_taken": "dispatch_specialist",
                "focus_slice": "",
                "owner_lane": "",
                "proof_status": "none",
                "closure_decision": "not_closing",
                "dispatches": [],
                "project_update": {},
            },
        )
        self.assertFalse(review["ready"])
        self.assertTrue(any("focus slice" in item.lower() for item in review["reasons"]))
        self.assertTrue(any("dispatch" in item.lower() for item in review["reasons"]))

    def test_supervisor_review_requests_revision_when_acceptance_is_unmet(self) -> None:
        project = {
            "project_id": "signal-house",
            "control": {
                "acceptance": ["No placeholder frames", "Final storyboard contact sheet"],
            },
        }
        review = supervisor_review(
            profile_key="creative-dev",
            project=project,
            output=(
                "Implemented storyboard placeholders.\n\n"
                "```json\n"
                "{\n"
                '  "summary": "Storyboard placeholders exported.",\n'
                '  "implemented": ["Created ten rough frames"],\n'
                '  "verified": ["Files exist on disk"],\n'
                '  "assumed": [],\n'
                '  "blocked": [],\n'
                '  "risks": [],\n'
                '  "next_actions": ["Do contact sheet later"],\n'
                '  "artifacts": ["/tmp/storyboard_f01.png"],\n'
                '  "handoff_needed": false\n'
                "}\n"
                "```"
            ),
        )

        self.assertEqual("revise", review["decision"])
        self.assertTrue(review["retryable"])
        self.assertIn("No placeholder frames", review["unmet_acceptance"])

    def test_closure_gate_rejects_close_slice_without_artifact_or_acceptance(self) -> None:
        project = {
            "project_id": "signal-house",
            "control": {
                "acceptance": ["Final storyboard contact sheet"],
            },
        }
        review = closure_gate_review(
            project=project,
            structured_result={
                "summary": "Storyboard complete.",
                "implemented": ["Prepared frames"],
                "verified": ["Looked at files"],
                "blocked": [],
                "artifacts": [],
                "handoff_needed": False,
            },
            action_type="close_slice",
        )
        self.assertFalse(review["ready"])
        self.assertTrue(any("artifact" in item.lower() for item in review["reasons"]))

    def test_sync_project_after_run_blocks_false_close_slice(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "creative-dev"),
            )
            update_project(
                root,
                project_id="signal-house",
                delivery_target="Final storyboard pack",
                primary_artifact="storyboards/contact.png",
                acceptance=("Final storyboard contact sheet",),
                strict_dispatch=True,
            )

            _sync_project_after_run(
                root,
                {
                    "run_id": "run_close_attempt",
                    "project_id": "signal-house",
                    "profile_key": "operator",
                    "status": "completed",
                    "phase": "completed",
                    "created_at": "2026-05-26T00:00:00Z",
                    "started_at": "2026-05-26T00:00:01Z",
                    "completed_at": "2026-05-26T00:00:10Z",
                    "objective_preview": "Close the storyboard slice.",
                    "latest_checkpoint": "done",
                    "output": "Tried to close the slice.",
                    "error": "",
                    "structured_result": {
                        "summary": "Storyboard close attempt completed.",
                        "implemented": ["Prepared placeholder storyboard frames."],
                        "verified": ["Files exist."],
                        "assumed": [],
                        "blocked": [],
                        "risks": [],
                        "next_actions": ["Prepare real contact sheet."],
                        "artifacts": [],
                        "handoff_needed": False,
                    },
                    "work_order": {
                        "action_type": "close_slice",
                    },
                },
            )

            project = discover_projects(root)[0]
            self.assertEqual("blocked", project["status"])
            self.assertTrue(any("artifact" in item.lower() for item in project["blocked"]))

    def test_sync_project_after_run_applies_operator_project_update_fields(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "creative-dev"),
            )

            _sync_project_after_run(
                root,
                {
                    "run_id": "run_operator_update",
                    "project_id": "signal-house",
                    "profile_key": "operator",
                    "status": "completed",
                    "phase": "completed",
                    "created_at": "2026-05-26T00:00:00Z",
                    "started_at": "2026-05-26T00:00:01Z",
                    "completed_at": "2026-05-26T00:00:10Z",
                    "objective_preview": "Route the next storyboard pass.",
                    "latest_checkpoint": "done",
                    "output": "Routed the next storyboard pass.",
                    "error": "",
                    "structured_result": {
                        "summary": "Storyboard corrective pass routed.",
                        "implemented": ["Prepared the creative lane handoff."],
                        "verified": ["Checked the current project acceptance criteria."],
                        "assumed": [],
                        "blocked": [],
                        "risks": [],
                        "next_actions": ["Wait for Penny's artifact pack."],
                        "artifacts": ["/tmp/storyboards/handoff.md"],
                        "handoff_needed": False,
                        "action_taken": "dispatch_specialist",
                        "focus_slice": "Storyboard corrective pass",
                        "owner_lane": "creative-dev",
                        "proof_status": "partial",
                        "closure_decision": "not_closing",
                        "dispatches": ["dispatch_20260526_storyboardfix"],
                        "project_update": {
                            "status": "active",
                            "now": "Penny owns the storyboard corrective pass.",
                            "next": "Review Penny's artifact pack.",
                            "primary_lane": "creative-dev",
                            "primary_artifact": "storyboards/contact_v4.png",
                        },
                    },
                    "work_order": {
                        "action_type": "dispatch_specialist",
                    },
                },
            )

            project = discover_projects(root)[0]
            self.assertEqual("creative-dev", project["owner"])
            self.assertEqual("Penny owns the storyboard corrective pass.", project["now"])
            self.assertEqual("Review Penny's artifact pack.", project["next"])
            self.assertEqual("storyboards/contact_v4.png", project["control"]["primary_artifact"])
            self.assertEqual("creative-dev", project["control"]["primary_lane"])

    def test_supervisor_revision_prompt_carries_forward_critique(self) -> None:
        prompt = supervisor_revision_prompt(
            prior_prompt="Create the clean storyboard pack.",
            review={
                "critique": [
                    "The response did not yet close these project acceptance targets: No placeholder frames",
                    "The response still ends in a handoff instead of closing the assigned lane.",
                ],
                "unmet_acceptance": ["No placeholder frames"],
            },
            attempt_number=2,
            max_attempts=3,
        )
        self.assertIn("Supervisor revision attempt 2/3", prompt)
        self.assertIn("No placeholder frames", prompt)
        self.assertIn("Do not hand the task back", prompt)

    def test_shared_project_inference_prefers_bound_project_terms(self) -> None:
        projects = [
            {
                "project_id": "aetherion-maze",
                "title": "Aetherion Maze Games",
                "summary": "Maze gameplay and HUD work.",
            },
            {
                "project_id": "signal-house",
                "title": "Signal House",
                "summary": "Publishing and app work.",
            },
        ]
        inferred = infer_project_id(
            projects,
            profile_key="operator",
            explicit_project_id="",
            messages=[{"role": "user", "content": "The maze HUD still looks wrong and gameplay needs work."}],
        )
        self.assertEqual("aetherion-maze", inferred)

    def test_portal_marks_stale_running_dispatches_failed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            dispatch_dir = root / "state" / "hermes" / "specialist_dispatches"
            dispatch_dir.mkdir(parents=True, exist_ok=True)
            dispatch_path = dispatch_dir / "dispatch_stale.json"
            dispatch_path.write_text(
                json.dumps(
                    {
                        "dispatch_id": "dispatch_stale",
                        "project_id": "signal-house",
                        "status": "running",
                        "created_at": "2026-05-15T00:00:00Z",
                        "updated_at": "2026-05-15T00:00:00Z",
                        "completed_at": "",
                        "prompt_preview": "test",
                        "output_preview": "",
                        "error_preview": "",
                    }
                ),
                encoding="utf-8",
            )

            _mark_stale_dispatches_failed(root, stale_minutes=1)

            stored = json.loads(dispatch_path.read_text(encoding="utf-8"))
            self.assertEqual("failed", stored["status"])
            self.assertTrue(stored["completed_at"])
            self.assertIn("operator bridge", stored["error_preview"])

    def test_portal_stale_dispatch_failure_syncs_strict_dispatch_project(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            _write_workspace_policy(root)
            dispatch_dir = root / "state" / "hermes" / "specialist_dispatches"
            dispatch_dir.mkdir(parents=True, exist_ok=True)

            create_project(
                root,
                project_id="signal-house",
                title="Signal House",
                summary="Cross-media project for app, game, and storyboard work.",
                specialists=("operator", "creative-dev"),
            )
            update_project(
                root,
                project_id="signal-house",
                strict_dispatch=True,
                delivery_target="Runway motion pass",
                primary_artifact="artifacts/animatic_v3_runway.mp4",
                acceptance=("Five teens are visibly rendered as characters.",),
                primary_lane="creative-dev",
            )

            dispatch_path = dispatch_dir / "dispatch_stale.json"
            dispatch_path.write_text(
                json.dumps(
                    {
                        "dispatch_id": "dispatch_stale",
                        "project_id": "signal-house",
                        "profile": "creative-dev",
                        "status": "running",
                        "created_at": "2026-05-15T00:00:00Z",
                        "updated_at": "2026-05-15T00:00:00Z",
                        "completed_at": "",
                        "prompt_preview": "test",
                        "output_preview": "Runway pass blocked.",
                        "error_preview": "",
                        "structured_result": {
                            "summary": "Runway pass blocked pending access.",
                            "blocked": ["True Runway generation is blocked pending authentication."],
                            "next_actions": ["Provide Runway access or swap to verified image-grounded inputs."],
                            "artifacts": ["/tmp/animatic_v3_runway.mp4"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            _mark_stale_dispatches_failed(root, stale_minutes=1)

            project = discover_projects(root)[0]
            self.assertEqual("blocked", project["status"])
            self.assertEqual("creative-dev", project["owner"])
            self.assertIn("Runway pass blocked pending access.", project["now"])
            self.assertIn("Provide Runway access", project["next"])


if __name__ == "__main__":
    unittest.main()
