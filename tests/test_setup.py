import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("capture_setup", Path(__file__).parents[1] / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        for patcher in (
            patch.object(setup, "RENDERER", self.home / "renderer"),
            patch.dict(setup.os.environ, {"XDG_CACHE_HOME": str(self.home)}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_first_run_requests_only_missing_packages(self):
        result = subprocess.CompletedProcess([], 127, "showmethekey\nmeson\nglib2-devel\n", "")
        with patch.object(setup.subprocess, "run", return_value=result) as run:
            self.assertEqual(setup.missing_packages(), ["showmethekey", "meson", "glib2-devel"])
        requested = run.call_args.args[0]
        self.assertIn("gcc", requested)
        self.assertNotIn("ninja", requested)

    def test_completed_build_needs_only_runtime_package(self):
        setup.RENDERER.touch()
        with patch.object(setup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            self.assertEqual(setup.missing_packages(), [])
        self.assertEqual(run.call_args.args[0], ["pacman", "-T", "showmethekey"])

    def test_package_query_failure_is_not_treated_as_ready(self):
        with patch.object(setup.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "database error")):
            with self.assertRaisesRegex(RuntimeError, "database error"):
                setup.missing_packages()

    def test_existing_renderer_is_not_rebuilt(self):
        setup.RENDERER.touch()
        with patch.object(setup.subprocess, "run") as run:
            setup.build()
        run.assert_not_called()

    def test_install_builds_only_after_package_success(self):
        with patch.object(setup.sys, "argv", ["setup.py", "install"]), \
                patch.object(setup, "missing_packages", return_value=["showmethekey"]), \
                patch.object(setup.subprocess, "run") as run, patch.object(setup, "build") as build:
            setup.main()
            run.assert_called_once_with(["omarchy", "pkg", "add", "showmethekey"], check=True)
            build.assert_called_once_with()
            build.reset_mock()
            run.side_effect = subprocess.CalledProcessError(1, "omarchy")
            with patch("builtins.input", return_value=""), patch("builtins.print"), self.assertRaises(SystemExit):
                setup.main()
            build.assert_not_called()

    def test_failed_build_can_retry_without_publishing_renderer(self):
        with patch.object(setup.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "meson")):
            with self.assertRaises(subprocess.CalledProcessError):
                setup.build()
        self.assertFalse(setup.RENDERER.exists())
        with patch.object(setup.subprocess, "run") as run:
            setup.build()
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
