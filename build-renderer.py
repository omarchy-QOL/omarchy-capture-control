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


def patch_source(path, replacements):
    text = path.read_text()
    for original, replacement in replacements.items():
        if text.count(original) != 1:
            raise ValueError(f"Unexpected source in {path}: {original!r}")
        text = text.replace(original, replacement)
    path.write_text(text)


def main():
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "capture-control"
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "showmethekey.tar.gz"
    if not archive.exists():
        download = archive.with_suffix(".download")
        urllib.request.urlretrieve(
            "https://codeload.github.com/AlynxZhou/showmethekey/tar.gz/" + COMMIT, download,
        )
        if hashlib.sha256(download.read_bytes()).hexdigest() != SHA256:
            raise SystemExit("Show Me The Key source checksum mismatch")
        download.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise SystemExit("Show Me The Key source checksum mismatch")
    with tarfile.open(archive) as package:
        package.extractall(cache, filter="data")
    source = cache / ("showmethekey-" + COMMIT)
    patch_source(source / "showmethekey-gtk/smtk-keys-area.c", {
        "\tcairo_set_source_rgba(cr, 1.0, 1.0, 1.0, 1.0);":
            "\tGdkRGBA color;\n\tgtk_widget_get_color(GTK_WIDGET(this), &color);\n"
            "\tgdk_cairo_set_source_rgba(cr, &color);",
    })
    patch_source(source / "showmethekey-gtk/main.c", {
        "#include <locale.h>": "#include <locale.h>\n#include <glib-unix.h>",
        "int main(": "static gboolean terminate_app(gpointer app)\n{\n"
            "\tsmtk_app_quit(SMTK_APP(app));\n\treturn G_SOURCE_CONTINUE;\n}\n\nint main(",
        "return g_application_run(G_APPLICATION(app), argc, argv);":
            "guint signal = g_unix_signal_add(SIGTERM, terminate_app, app);\n"
            "\tint result = g_application_run(G_APPLICATION(app), argc, argv);\n"
            "\tg_source_remove(signal);\n\treturn result;",
    })
    build = source / "build"
    if not (build / "build.ninja").exists():
        subprocess.run(["meson", "setup", str(build), str(source),
                        "--prefix=/usr", "--buildtype=release"], check=True)
    subprocess.run(["meson", "compile", "-C", str(build), "showmethekey-gtk"], check=True)
    target = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "capture-control"
    target.mkdir(parents=True, exist_ok=True)
    temporary = target / "showmethekey-gtk.tmp"
    shutil.copy2(build / "showmethekey-gtk/showmethekey-gtk", temporary)
    temporary.replace(target / "showmethekey-gtk")
    print(target / "showmethekey-gtk")


if __name__ == "__main__":
    main()
