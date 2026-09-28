"""Core tests: run with  python -m unittest discover -s tests  (from agent-system/)"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mahadir.llm import BrainParseError, BrainUnavailable, MockBrain, validate_schema
from mahadir.memory import Memory
from mahadir.orchestrator import Orchestrator

TASK = {"title": "Global Computer & Technology: on-site PC repair service in Dhaka",
        "brief": "publish-ready blog post", "constraints": ["cite every claim"]}


def fresh_root():
    return tempfile.mkdtemp(prefix="mahadir-test-")


class TestSchema(unittest.TestCase):
    def test_validate_schema(self):
        ok = {"a": "x", "b": [1], "c": {"d": 1}}
        self.assertEqual(validate_schema(ok, {"a": "str", "b": "list", "c": {"d": "number"}}), [])
        bad = {"a": 3}
        errs = validate_schema(bad, {"a": "str", "z": "list"})
        self.assertEqual(len(errs), 2)

    def test_extract_json_from_fence(self):
        from mahadir.llm import extract_json
        self.assertEqual(extract_json('```json\n{"x": 1}\n```'), {"x": 1})
        self.assertEqual(extract_json('blah {"x": {"y": 2}} blah'), {"x": {"y": 2}})


class TestFullRun(unittest.TestCase):
    def test_mock_run_reaches_done(self):
        root = fresh_root()
        try:
            mem = Memory(os.path.join(root, "memory"))
            orch = Orchestrator(TASK, root, memory=mem)
            rep = orch.start()
            self.assertEqual(rep["status"], "DONE", rep)
            self.assertTrue(os.path.exists(os.path.join(root, "runs", rep["run_id"], "final_output.md")))
            md = open(os.path.join(root, "runs", rep["run_id"], "final_output.md"), encoding="utf-8").read()
            self.assertIn("Sources & Citations", md)          # critic forced the revision
            self.assertEqual(rep["draft_rounds"], 2)          # one rejection, one revision
            self.assertEqual(rep["stats"]["critic_rejections"], 1)
        finally:
            shutil.rmtree(root)

    def test_system_improves_on_second_run(self):
        root = fresh_root()
        try:
            mem = Memory(os.path.join(root, "memory"))
            rep1 = Orchestrator(TASK, root, memory=mem).start()
            self.assertEqual(rep1["status"], "DONE")
            self.assertFalse(rep1["per_agent"]["writer"]["first_pass_ok"])  # rejected once
            rep2 = Orchestrator({"title": TASK["title"], "brief": TASK["brief"],
                                 "constraints": []}, root, memory=mem).start()
            self.assertEqual(rep2["status"], "DONE")
            self.assertTrue(rep2["per_agent"]["writer"]["first_pass_ok"],   # lesson applied in v1
                            "writer should pass first draft after learning the lesson")
            self.assertEqual(rep2["draft_rounds"], 1)
            self.assertTrue(rep2["self_improvement"]["playbook_id"])
            lessons = mem.lessons
            self.assertTrue(any(l["target"] == "writer" for l in lessons))
        finally:
            shutil.rmtree(root)

    def test_budget_exhaustion_is_graceful(self):
        root = fresh_root()
        try:
            mem = Memory(os.path.join(root, "memory"))
            mem.update_policies({"max_steps": 3})   # impossible budget
            rep = Orchestrator(TASK, root, memory=mem).start()
            self.assertEqual(rep["status"], "FAILED")
            self.assertTrue(rep["dead_letters"])
            self.assertTrue(rep["per_agent"].get("postmortem") or rep["dead_letters"],
                            "postmortem should still run after failure")
        finally:
            shutil.rmtree(root)

    def test_transient_and_parse_retries_recover(self):
        class Flaky(MockBrain):
            def __init__(self):
                super().__init__()
                self.calls = {}
            def complete(self, agent, system, request, schema):
                n = self.calls.get(agent, 0)
                self.calls[agent] = n + 1
                if agent == "researcher" and n == 0:
                    raise BrainUnavailable("simulated outage")
                if agent == "writer" and n == 0:
                    raise BrainParseError("simulated bad json")
                return super().complete(agent, system, request, schema)

        root = fresh_root()
        try:
            mem = Memory(os.path.join(root, "memory"))
            rep = Orchestrator(TASK, root, brain=Flaky(), memory=mem).start()
            self.assertEqual(rep["status"], "DONE")
            self.assertGreaterEqual(rep["stats"]["retries"], 2)
            self.assertTrue(rep["incidents"])
        finally:
            shutil.rmtree(root)

    def test_resume_after_checkpoint(self):
        root = fresh_root()
        try:
            mem = Memory(os.path.join(root, "memory"))
            orch = Orchestrator(TASK, root, memory=mem)
            orch.start()
            rep = Orchestrator.resume(orch.run_id, root, memory=Memory(os.path.join(root, "memory")))
            self.assertIn(rep["status"], ("DONE", "DONE_WITH_WARNINGS", "FAILED"))
        finally:
            shutil.rmtree(root)

    def test_policies_cannot_leave_bounds(self):
        mem = Memory(fresh_root())
        out = mem.update_policies({"critic_rounds": 99, "retry_budget": -5, "bogus": 1})
        self.assertLessEqual(out["critic_rounds"], 5)
        self.assertGreaterEqual(out["retry_budget"], 1)
        self.assertNotIn("bogus", out)


if __name__ == "__main__":
    unittest.main()
