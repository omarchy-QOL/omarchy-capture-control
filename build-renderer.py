#!/usr/bin/python3
"""Build GTK colour support and graceful service shutdown into the renderer."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

COMMIT = "3e70a7deb178dd7d8a8b5bbf663807c490997273"
SHA256 = "412e1021b39a738ff67a6567baa0c3e72b4d451ecf7b53365db2546e8ce64421"
cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "capture-control"
cache.mkdir(parents=True, exist_ok=True)
archive = cache / "showmethekey.tar.gz"
if not archive.exists():
    urllib.request.urlretrieve(
        "https://codeload.github.com/AlynxZhou/showmethekey/tar.gz/" + COMMIT, archive,
    )
if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
    raise SystemExit("Show Me The Key source checksum mismatch")
source = cache / ("showmethekey-" + COMMIT)
if not source.exists():
    with tarfile.open(archive) as package:
        package.extractall(cache, filter="data")
renderer = source / "showmethekey-gtk/smtk-keys-area.c"
original = "\tcairo_set_source_rgba(cr, 1.0, 1.0, 1.0, 1.0);"
patched = ("\tGdkRGBA color;\n\tgtk_widget_get_color(GTK_WIDGET(this), &color);\n"
           "\tgdk_cairo_set_source_rgba(cr, &color);")
text = renderer.read_text()
if original not in text and patched not in text:
    raise SystemExit("Unexpected renderer source")
renderer.write_text(text.replace(original, patched))
entry = source / "showmethekey-gtk/main.c"
text = entry.read_text()
if "g_unix_signal_add" not in text:
    text = text.replace("#include <locale.h>", "#include <locale.h>\n#include <glib-unix.h>")
    text = text.replace("int main(", "static gboolean terminate_app(gpointer app)\n{\n"
                        "\tsmtk_app_quit(SMTK_APP(app));\n\treturn G_SOURCE_CONTINUE;\n}\n\nint main(")
    text = text.replace("return g_application_run(G_APPLICATION(app), argc, argv);",
                        "guint signal = g_unix_signal_add(SIGTERM, terminate_app, app);\n"
                        "\tint result = g_application_run(G_APPLICATION(app), argc, argv);\n"
                        "\tg_source_remove(signal);\n\treturn result;")
    entry.write_text(text)
build = source / "build"
if not (build / "build.ninja").exists():
    subprocess.run(["meson", "setup", str(build), str(source),
                    "--prefix=/usr", "--buildtype=release"], check=True)
subprocess.run(["meson", "compile", "-C", str(build), "showmethekey-gtk"], check=True)
target = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "capture-control"
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(build / "showmethekey-gtk/showmethekey-gtk", target / "showmethekey-gtk")
print(target / "showmethekey-gtk")
