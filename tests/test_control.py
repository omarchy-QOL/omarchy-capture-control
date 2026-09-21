import configparser
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("control", Path(__file__).parents[1] / "control.py")
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class SettingsTest(unittest.TestCase):
    def test_style_validation_rejects_css_and_nonfinite_opacity(self):
        config = configparser.ConfigParser(interpolation=None)
        config["capture-control"] = {"text-color": "#abcdef"}
        self.assertEqual(control.text_color(config), "#abcdef")
        for value in ("red", "#fff", "#123456; opacity: 0", "#12345678"):
            config["capture-control"]["text-color"] = value
            with self.assertRaises(ValueError):
                control.text_color(config)
        for value in ("nan", "inf", "-0.1", "1.1"):
            config["capture-control"]["background-opacity"] = value
            with self.assertRaises(ValueError):
                control.opacity(config)

    def test_style_edit_preserves_capture_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "keyfile"
            path.write_text("[one/alynx/showmethekey]\nwidth=725.0\npaused=true\n")
            with patch.object(control, "SETTINGS", path), patch.object(control, "running", return_value=False):
                with patch.object(control.sys, "argv", ["control.py", "color", "#94e2d5"]):
                    control.main()
                config = control.settings()
                self.assertEqual(config["one/alynx/showmethekey"]["width"], "725.0")
                self.assertEqual(config["one/alynx/showmethekey"]["paused"], "true")
                self.assertEqual(control.text_color(config), "#94e2d5")

    def test_invalid_style_does_not_overwrite_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "keyfile"
            original = "[one/alynx/showmethekey]\nwidth=725.0\n"
            path.write_text(original)
            with patch.object(control, "SETTINGS", path):
                with patch.object(control.sys, "argv", ["control.py", "opacity", "nan"]):
                    with self.assertRaises(ValueError):
                        control.main()
            self.assertEqual(path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
