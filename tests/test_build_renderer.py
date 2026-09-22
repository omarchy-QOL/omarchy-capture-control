import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("build_renderer", Path(__file__).parents[1] / "build-renderer.py")
build_renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_renderer)


class RendererPatchTest(unittest.TestCase):
    def test_applies_each_patch_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main.c"
            path.write_text("first\nsecond\n")
            build_renderer.patch_source(path, {"first": "one", "second": "two"})
            self.assertEqual(path.read_text(), "one\ntwo\n")

    def test_unexpected_source_is_rejected_without_partial_write(self):
        for original in ("first\nmissing\n", "first\nsecond\nsecond\n"):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "main.c"
                path.write_text(original)
                with self.assertRaisesRegex(ValueError, "Unexpected source"):
                    build_renderer.patch_source(path, {"first": "one", "second": "two"})
                self.assertEqual(path.read_text(), original)


if __name__ == "__main__":
    unittest.main()
