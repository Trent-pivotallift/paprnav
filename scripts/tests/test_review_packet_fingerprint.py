from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest


SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
TASK = "T-FINGERPRINT"


class ReviewPacketFingerprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.temp_dir.name)
        self._run("git", "init", "--quiet")
        self._run("git", "config", "user.email", "review-test@example.invalid")
        self._run("git", "config", "user.name", "Review Test")
        (self.repo / "seed.txt").write_text("seed\n")
        self._run("git", "add", "seed.txt")
        self._run("git", "commit", "--quiet", "-m", "seed")

        self.run_dir = self.repo / ".ai" / "review-runs" / TASK
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "decision.md").write_text(
            "# Decision\n\n"
            "## Objective\nTest fingerprint agreement.\n\n"
            "## Safety and correctness invariants\nBind every input.\n\n"
            "## Proposed design\nUse one canonical implementation.\n\n"
            "## Test strategy\nMutate an explicit input.\n"
        )
        (self.run_dir / "findings.json").write_text("[]\n")
        (self.run_dir / "proposal.md").write_text("proposal-v1\n")
        (self.run_dir / "closure.md").write_text(
            "# Closure\n\n"
            "## Outcome\nReady.\n\n"
            "## Invariants verified\nInputs are bound.\n\n"
            "## Verification performed\nTools agree.\n\n"
            "## Final scope reviewed\nInfrastructure only.\n\n"
            "## Not verified\nNothing else.\n"
        )
        self._build_packet()
        manifest = json.loads((self.run_dir / "manifest.json").read_text())
        fingerprint = manifest["scopeFingerprint"]
        head = manifest["head"]
        reviews = []
        for stage in ("design", "implementation", "closure"):
            artifact = self.run_dir / f"{stage}-review.md"
            artifact.write_text(f"{stage} pass\n")
            reviews.append(
                {
                    "stage": stage,
                    "reviewer": "reviewer",
                    "builder": "builder",
                    "outcome": "pass",
                    "reviewedAt": "2026-08-30T00:00:00+00:00",
                    "baseRef": "HEAD",
                    "head": head,
                    "scopeFingerprint": fingerprint,
                    "artifact": str(artifact.relative_to(self.repo)),
                    "artifactSha256": hashlib.sha256(
                        artifact.read_bytes()
                    ).hexdigest(),
                }
            )
        (self.run_dir / "reviews.json").write_text(
            json.dumps(reviews, indent=2) + "\n"
        )
        (self.run_dir / "state.json").write_text(
            json.dumps({"phase": "closed", "bootstrapException": None}) + "\n"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=check,
        )

    def _build_packet(self) -> None:
        self._run(
            "python3",
            str(SCRIPTS / "build-review-packet.py"),
            "--task",
            TASK,
            "--base",
            "HEAD",
            "--stage",
            "closure",
            "--review-input",
            str((self.run_dir / "proposal.md").relative_to(self.repo)),
        )

    def _verify(self, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self._run(
            "python3",
            str(SCRIPTS / "verify-review-packet.py"),
            "--task",
            TASK,
            "--stage",
            "closure",
            "--base",
            "HEAD",
            "--packet",
            str((self.run_dir / "review-packet.md").relative_to(self.repo)),
            check=check,
        )

    def _validate(self, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self._run(
            "python3",
            str(SCRIPTS / "validate-review-run.py"),
            "--task",
            TASK,
            check=check,
        )

    def _record_reattest(
        self,
        artifact_name: str,
        *,
        stage: str = "closure",
        outcome: str = "pass",
        reviewer: str = "new-reviewer",
        builder: str = "builder",
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        artifact = self.run_dir / artifact_name
        if not artifact.exists():
            artifact.write_text("fresh independent review\n")
        return self._run(
            "python3",
            str(SCRIPTS / "record-review.py"),
            "--task",
            TASK,
            "--stage",
            stage,
            "--reviewer",
            reviewer,
            "--builder",
            builder,
            "--outcome",
            outcome,
            "--artifact",
            str(artifact.relative_to(self.repo)),
            "--reattest",
            check=check,
        )

    def test_build_verify_and_validate_agree_with_explicit_review_input(self) -> None:
        self.assertIn("review packet is current", self._verify().stdout)
        self.assertIn("review run is closable", self._validate().stdout)

    def test_verify_and_validate_reject_changed_explicit_review_input(self) -> None:
        (self.run_dir / "proposal.md").write_text("proposal-v2\n")

        verify = self._verify(check=False)
        validate = self._validate(check=False)

        self.assertNotEqual(verify.returncode, 0)
        self.assertIn("working tree changed after packet generation", verify.stderr)
        self.assertNotEqual(validate.returncode, 0)
        self.assertIn(
            "working tree changed after packet generation", validate.stdout
        )

    def test_closed_run_accepts_fresh_closure_pass_reattestation(self) -> None:
        state_before = (self.run_dir / "state.json").read_text()

        self._record_reattest("closure-reattest.md")

        reviews = json.loads((self.run_dir / "reviews.json").read_text())
        self.assertEqual(len(reviews), 4)
        self.assertEqual(reviews[-1]["stage"], "closure")
        self.assertEqual(reviews[-1]["outcome"], "pass")
        self.assertIs(reviews[-1]["reattest"], True)
        self.assertEqual((self.run_dir / "state.json").read_text(), state_before)
        self.assertIn("review run is closable", self._validate().stdout)

    def test_reattestation_rejects_stale_packet(self) -> None:
        (self.run_dir / "proposal.md").write_text("proposal-v2\n")

        result = self._record_reattest(
            "stale-closure-reattest.md", outcome="fail", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a current packet fingerprint", result.stderr)
        self.assertEqual(len(json.loads((self.run_dir / "reviews.json").read_text())), 3)
        self.assertEqual(
            json.loads((self.run_dir / "state.json").read_text())["phase"],
            "closed",
        )

    def test_reattestation_requires_prior_closure_pass(self) -> None:
        reviews = json.loads((self.run_dir / "reviews.json").read_text())
        (self.run_dir / "reviews.json").write_text(
            json.dumps(
                [review for review in reviews if review["stage"] != "closure"],
                indent=2,
            )
            + "\n"
        )

        result = self._record_reattest(
            "missing-prior-closure-reattest.md", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a prior closure PASS", result.stderr)

    def test_reattestation_requires_closed_phase(self) -> None:
        (self.run_dir / "state.json").write_text(
            json.dumps(
                {"phase": "implementation_reviewed", "bootstrapException": None}
            )
            + "\n"
        )

        result = self._record_reattest(
            "wrong-phase-reattest.md", outcome="fail", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires an already closed run", result.stderr)

    def test_reattestation_requires_distinct_reviewer_and_builder(self) -> None:
        result = self._record_reattest(
            "self-review-reattest.md",
            reviewer="same-identity",
            builder="same-identity",
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewer and builder identities must be distinct", result.stderr)

    def test_reattestation_rejects_wrong_stage(self) -> None:
        result = self._record_reattest(
            "implementation-reattest.md", stage="implementation", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allowed only for the closure stage", result.stderr)

    def test_closure_fail_reattestation_reopens_implementation_review(self) -> None:
        self._record_reattest("closure-fail-reattest.md", outcome="fail")

        reviews = json.loads((self.run_dir / "reviews.json").read_text())
        state = json.loads((self.run_dir / "state.json").read_text())
        self.assertEqual(len(reviews), 4)
        self.assertEqual(reviews[-1]["stage"], "closure")
        self.assertEqual(reviews[-1]["outcome"], "fail")
        self.assertIs(reviews[-1]["reattest"], True)
        self.assertEqual(state["phase"], "implementation_reviewed")

    def test_reattestation_rejects_reused_artifact(self) -> None:
        result = self._record_reattest(
            "closure-review.md", outcome="fail", check=False
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review artifacts are immutable", result.stderr)
        self.assertEqual(
            json.loads((self.run_dir / "state.json").read_text())["phase"],
            "closed",
        )
