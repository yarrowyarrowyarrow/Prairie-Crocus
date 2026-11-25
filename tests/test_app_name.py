"""
tests/test_app_name.py — the V3.68 rename to Prairie Crocus, held.

Site & Pattern became Prairie Crocus in V3.68 (docs/plans/V3.68-prairie-crocus.md).
A rebrand renames what people see and keeps what an installed copy is found by,
and both halves can drift: a new message typed with the old name, or an
identity "tidied" to the new one, which strands a person's designs, their
shortcuts or their updates. These tests hold the line both ways.
"""

import ast
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_OLD = re.compile(r"Site\s*(?:&|&amp;|and)\s*Pattern|SiteAndPattern|Site-and-Pattern"
                  r"|site[-_]and[-_]pattern", re.I)

#: Old-name strings in ``src/`` that are identities, each with its reason.
_KEPT = (
    # The repository is still named Site-and-Pattern; GitHub redirects it if
    # it is renamed, and the updater reads its releases.
    re.compile(r"yarrowyarrowyarrow/Site-and-Pattern", re.I),
    # Unsaved work from before the update is recovered from this file.
    re.compile(r"\.site-and-pattern_autosave"),
    # The updater finds the stash it made by this label.
    re.compile(r"site-and-pattern auto-update"),
    # The diagnostic log people have been asked to send.
    re.compile(r"site-and-pattern-debug\.log"),
    # The Mac update message names the old copy, so it can be put in the Bin.
    re.compile(r"named SiteAndPattern"),
)


def _docstrings(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)):
                out.add(id(first.value))
    return out


class TestNoOldNameInWhatPeopleRead(unittest.TestCase):
    def test_src_strings_say_prairie_crocus(self):
        """A string in ``src/`` with the old name is an identity on the list
        above, or the data folder's name in ``branding``; anything else is
        a message somebody will read, and should use ``branding.APP_NAME``."""
        offenders = []
        for path in sorted((ROOT / "src").rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docs = _docstrings(tree)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Constant)
                        and isinstance(node.value, str)) or id(node) in docs:
                    continue
                text = node.value
                for kept in _KEPT:
                    text = kept.sub("", text)
                if rel == "src/branding.py" and text == "Site & Pattern":
                    continue           # DATA_DIR_NAME, kept on purpose
                if _OLD.search(text):
                    offenders.append(f"{rel}:{node.lineno}: {node.value[:80]!r}")
        self.assertFalse(offenders, "the old name in a string people read; "
                         "write branding.APP_NAME:\n" + "\n".join(offenders))

    def test_the_name_and_the_folder(self):
        from src import branding
        self.assertEqual(branding.APP_NAME, "Prairie Crocus")
        # The folder holds every design: renaming it is its own decision,
        # with a migration, never a side effect of a rebrand.
        self.assertEqual(branding.DATA_DIR_NAME, "Site & Pattern")

    def test_web_pages_say_prairie_crocus(self):
        offenders = []
        for path in sorted((ROOT / "html").rglob("*.html")):
            if "vendor" in path.parts:
                continue
            for n, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1):
                if _OLD.search(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{n}")
        self.assertFalse(offenders, "\n".join(offenders))


class TestInstalledCopiesAreStillFound(unittest.TestCase):
    """The installer renames what is shown and keeps what finds a copy."""

    @classmethod
    def setUpClass(cls):
        cls.nsi = (ROOT / "scripts" / "packaging" / "installer.nsi").read_text(
            encoding="utf-8")

    def define(self, name):
        m = re.search(rf'^!define {name} "([^"]*)"', self.nsi, re.M)
        self.assertIsNotNone(m, name)
        return m.group(1)

    def test_identities_keep_their_names(self):
        # A pinned taskbar icon points at the program file, and its code is
        # inside it: a new name would leave the old program running.
        self.assertEqual(self.define("APP_EXE"), "SiteAndPattern.exe")
        # A later install finds this one, and Settings > Apps lists one entry.
        self.assertEqual(self.define("REG_KEY"), r"Software\Site & Pattern")
        self.assertTrue(self.define("UNINSTALL_KEY").endswith(r"\Site & Pattern"))
        self.assertIn('InstallDirRegKey HKLM "${REG_KEY}" "InstallDir"', self.nsi)

    def test_what_is_shown_is_renamed(self):
        self.assertIn('Name "Prairie Crocus"', self.nsi)
        self.assertIn('"DisplayName" "Prairie Crocus"', self.nsi)
        self.assertIn(r'CreateShortCut "$SMPROGRAMS\Prairie Crocus\Prairie Crocus.lnk"',
                      self.nsi)

    def test_old_shortcuts_are_replaced_not_doubled(self):
        self.assertEqual(self.define("OLD_NAME"), "Site & Pattern")
        install = self.nsi.split('Section "Prairie Crocus"', 1)[1].split(
            "SectionEnd", 1)[0]
        uninstall = self.nsi.split('Section "Uninstall"', 1)[1]
        for section in (install, uninstall):
            self.assertIn(r'RMDir /r "$SMPROGRAMS\${OLD_NAME}"', section)
            self.assertIn(r'Delete "$DESKTOP\${OLD_NAME}.lnk"', section)
        # A desktop shortcut under the old name comes back under the new one.
        self.assertIn(r'${OrIf} ${FileExists} "$DESKTOP\${OLD_NAME}.lnk"', install)


class TestTheDownloadsStillReachTheUpdater(unittest.TestCase):
    """Renaming the release files is safe only because the updater picks an
    asset by its extension. If that changes, a copy already installed looks
    for a name these releases no longer carry."""

    def test_updater_matches_by_extension(self):
        from src import github_releases as ghr
        self.assertEqual(ghr.platform_asset_extensions("darwin"), (".dmg",))
        self.assertEqual(ghr.platform_asset_extensions("win32")[0], ".exe")

    def test_the_build_and_the_workflows_agree(self):
        pack = ROOT / "scripts" / "packaging"
        flows = ROOT / ".github" / "workflows"
        sh = (pack / "build_installer.sh").read_text(encoding="utf-8")
        spec = (pack / "permadesign.spec").read_text(encoding="utf-8")
        mac = (flows / "release-macos.yml").read_text(encoding="utf-8")
        win = (flows / "release-windows.yml").read_text(encoding="utf-8")
        nsi = (pack / "installer.nsi").read_text(encoding="utf-8")
        self.assertIn("name='Prairie Crocus.app'", spec)
        self.assertIn('APP="dist/Prairie Crocus.app"', sh)
        self.assertIn("dist/PrairieCrocus.dmg", sh)
        self.assertIn('mv "dist/PrairieCrocus.dmg" '
                      '"dist/PrairieCrocus-${{ github.ref_name }}.dmg"', mac)
        self.assertIn("files: dist/PrairieCrocus-${{ github.ref_name }}.dmg", mac)
        self.assertIn(r'OutFile "..\..\PrairieCrocus-Installer.exe"', nsi)
        self.assertIn('Move-Item -Force "PrairieCrocus-Installer.exe" '
                      '"dist/PrairieCrocus-${{ github.ref_name }}-Setup.exe"', win)
        self.assertIn("files: dist/PrairieCrocus-${{ github.ref_name }}-Setup.exe",
                      win)


if __name__ == "__main__":
    unittest.main()
