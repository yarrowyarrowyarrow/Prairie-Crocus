"""
src/branding.py — the app's display identity.

Single source of truth for the user-facing product name. The app has had three
names: "PermaDesign" until V1.69, "Site & Pattern" (drawn from the
design-philosophy document) from V1.69 to V3.67, and **Prairie Crocus** from
V3.68, after the native flower its icon has shown since V3.17.

A rebrand renames what people see, not what is already on their machines. What
deliberately keeps an older name, so existing installs keep their data, their
settings, their shortcuts and their updates:

  * the per-user data *folder*, still ``Site & Pattern`` (``DATA_DIR_NAME``):
    every design lives in its ``saves`` folder, and a move that failed half way
    (a file held open, a synced folder) would show a person an empty start
    screen. V1.69 did move it once, from ``PermaDesign`` (``src/user_paths.py``);
  * the Windows program file ``SiteAndPattern.exe``, its registry keys and the
    folder an existing copy is installed in (``scripts/packaging/installer.nsi``):
    a pinned taskbar icon points at the file, and the program's code is inside it;
  * the GitHub repo + the releases URL (``src/github_releases.py``), which
    GitHub redirects if the repo is renamed;
  * the QSettings org/app name (``main.py``) that keys window geometry and the
    one-time legacy-recipe migration flag;
  * the on-disk database *filenames* (``permadesign.db`` …), the autosave file
    and the frozen scripting / MCP API symbols (``src/permadesign_api.py``,
    ``src/mcp_server.py``) snapshotted by ``tests/test_architecture_guard.py``.

Kept dependency-free (no Qt) so any layer can import the name.
"""

from __future__ import annotations

# What the user sees.
APP_NAME = "Prairie Crocus"
def _home() -> str:
    """The default region pack's short name, for the tagline (V3.24: the
    region names itself; ``src/region.py``)."""
    try:
        from src import region
        return region.default().short
    except Exception:                                      # noqa: BLE001
        return ""


# S6, V3.23: "Native plant yards for Edmonton", the default pack's place.
APP_TAGLINE = (f"Native plant yards for {_home()}" if _home()
               else "Native plant yards")
APP_TITLE = f"{APP_NAME} — {APP_TAGLINE}"

#: The licence the program is under (V3.18, FN-1; the owner's decision D1).
#: It was the PolyForm Noncommercial License, which the GPL v3 that PyQt6 is
#: licensed under does not allow a program built on it to be distributed
#: under. ``LICENSE`` holds the text; Help › About and the README name it, and
#: ``tests/test_licence.py`` keeps the three saying the same thing.
LICENCE_NAME = "GNU General Public License, version 3"
LICENCE_SPDX = "GPL-3.0-only"


def window_title(document: str | None = None, *, version: str | None) -> str:
    """The main window's title (F231, V3.16): the name, the release it is
    running, and the open design, or the tagline before one is named.
    ``window_title(version=None)`` is ``APP_TITLE``.

    The version is there so a screenshot says which copy it came from, and so
    an update can be checked at a glance: the words come from the program, the
    number from the ``version.txt`` installed beside it. It is a required
    keyword so a new caller cannot leave it out by accident; pass
    ``app_version.running_version()``."""
    name = f"{APP_NAME} {version}" if version else APP_NAME
    return f"{name} — {document or APP_TAGLINE}"


# Per-user data-folder names (see ``src/user_paths.py``). The folder was migrated
# from the legacy name on first launch after the V1.69 rebrand. It keeps the
# Site & Pattern name through the V3.68 one on purpose (see the module docstring):
# it holds every design, and nobody opens it by hand.
DATA_DIR_NAME = "Site & Pattern"
LEGACY_DATA_DIR_NAME = "PermaDesign"
