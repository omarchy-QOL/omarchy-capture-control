import configparser
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("control", Path(__file__).parents[1] / "control.py")
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class SettingsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        for name, value in {
            "APP_HOME": self.home,
            "SETTINGS": self.home / "glib-2.0/settings/keyfile",
            "RENDERER": self.home / "renderer",
        }.items():
            patcher = patch.object(control, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_clean_defaults_and_initialization_preserves_existing_settings(self):
        control.initialize()
        config = control.settings()
        self.assertEqual(control.text_color(config), "#ffffff")
        self.assertEqual(control.opacity(config), 0.3)
        self.assertFalse(control.only_omarchy_bindings(config))
        config["one/alynx/showmethekey"]["width"] = "725.0"
        control.save(config)
        original = control.SETTINGS.read_bytes()
        control.initialize()
        self.assertEqual(control.SETTINGS.read_bytes(), original)

    def test_incomplete_settings_fail_without_repair(self):
        control.SETTINGS.parent.mkdir(parents=True)
        original = "[one/alynx/showmethekey]\nwidth=725.0\n"
        control.SETTINGS.write_text(original)
        with self.assertRaisesRegex(ValueError, "Missing \\[capture-control\\]"):
            control.set_appearance("color", "#ffffff")
        self.assertEqual(control.SETTINGS.read_text(), original)

    def test_style_validation_rejects_css_and_nonfinite_opacity(self):
        config = configparser.ConfigParser(interpolation=None)
        config["capture-control"] = {"text-color": "#ABCDEF"}
        self.assertEqual(control.text_color(config), "#abcdef")
        for value in ("red", "#fff", "#123456; opacity: 0", "#12345678"):
            config["capture-control"]["text-color"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                control.text_color(config)
        for value in ("nan", "inf", "-0.1", "1.1"):
            config["capture-control"]["background-opacity"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                control.opacity(config)

    def test_style_edit_preserves_native_settings_and_restarts_active_capture(self):
        control.initialize()
        config = control.settings()
        config["one/alynx/showmethekey"].update({"width": "725.0", "paused": "true"})
        control.save(config)
        with patch.object(control, "running", return_value=True), \
                patch.object(control, "stop") as stop, patch.object(control, "start") as start:
            control.main(["color", "#94e2d5"])
        self.assertEqual(control.settings()["one/alynx/showmethekey"], config["one/alynx/showmethekey"])
        self.assertEqual(control.text_color(control.settings()), "#94e2d5")
        stop.assert_called_once_with()
        start.assert_called_once_with()

    def test_invalid_style_does_not_overwrite_settings(self):
        control.initialize()
        original = control.SETTINGS.read_bytes()
        with self.assertRaises(ValueError):
            control.main(["opacity", "nan"])
        self.assertEqual(control.SETTINGS.read_bytes(), original)

    def test_native_filter_persists_and_preserves_other_settings(self):
        control.initialize()
        for mode in ("raw", "compact", "composed"):
            with self.subTest(mode=mode):
                config = control.settings()
                config["one/alynx/showmethekey"].update({"mode": repr(mode), "show-mouse": "false"})
                config["capture-control"]["background-opacity"] = "0.63"
                control.save(config)
                control.main(["bindings-only", "true"])
                updated = control.settings()
                self.assertTrue(control.only_omarchy_bindings(updated))
                self.assertEqual(updated["one/alynx/showmethekey"]["mode"],
                                 repr("composed" if mode == "raw" else mode))
                self.assertEqual(updated["one/alynx/showmethekey"]["show-mouse"], "false")
                self.assertEqual(control.opacity(updated), 0.63)
                control.main(["bindings-only", "false"])
                self.assertFalse(control.only_omarchy_bindings(control.settings()))
        original = control.SETTINGS.read_bytes()
        with self.assertRaises(ValueError):
            control.main(["bindings-only", "yes"])
        self.assertEqual(control.SETTINGS.read_bytes(), original)

    def test_native_filter_failure_is_reported(self):
        with patch.object(control.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "gsettings")):
            with self.assertRaises(subprocess.CalledProcessError):
                control.set_bindings_only("true")

    def test_start_requires_renderer_and_writes_isolated_style(self):
        with patch.object(control, "running", return_value=False):
            with self.assertRaisesRegex(ValueError, "build-renderer.py"):
                control.start()
            control.RENDERER.touch()
            with patch.object(control.subprocess, "run") as run:
                control.start()
        css = (self.home / "gtk-4.0/gtk.css").read_text()
        self.assertIn("rgba(0, 0, 0, 0.3)", css)
        self.assertIn("#ffffff", css)
        self.assertIn("--setenv=XDG_CONFIG_HOME=" + str(self.home), run.call_args.args[0])
        self.assertEqual(run.call_args.args[0][-3:], [str(control.RENDERER), "-A", "-C"])

    def test_status_before_first_start_is_read_only(self):
        with patch.object(control.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                control.main(["status"])
        self.assertEqual(json.loads(output.getvalue()), {
            "recording": False, "running": False, "opacity": 0.3,
            "textColor": "#ffffff", "onlyOmarchyBindings": False,
        })
        self.assertFalse(control.SETTINGS.exists())

    def test_cli_rejects_missing_and_extra_arguments(self):
        for args in ([], ["unknown"], ["color"], ["status", "extra"], ["stop", "a", "b"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    control.main(args)
                self.assertEqual(error.exception.code, 2)
        self.assertFalse(control.SETTINGS.exists())


if __name__ == "__main__":
    unittest.main()
