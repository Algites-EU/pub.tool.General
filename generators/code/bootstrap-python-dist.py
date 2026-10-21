#!/usr/bin/env python3
"""Build all native Python Codegen distributions outside Modustro conventions.

The six product descriptors are authoritative for package dependencies; staging
collects only the corresponding artifact's Python sources and package resources.
No generated sources are edited and no source-tree pyproject is created.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import email
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

import yaml

PARTS = ("intf", "impl", "cli")
GENERATORS = ("defscodegen", "sdocodegen")
SOURCE_DIRS = ("src/product/python", "src/product/python.gen", "src/product/config", "src/product/resources")
BOOTSTRAP_NAME = "pub.tool.General_generators.code"
EXPECTED_CLI_OPTIONS = {
    "defscodegen": ("--repository-root", "--schema-input-dir", "--technology-dointf-output-dir", "--naming-conventions-file"),
    "sdocodegen": ("--repository-root", "--technology-dointf-input-dir", "--technology-sdointf-output-dir", "--naming-conventions-file"),
}


def normalized_distribution(artifact: str) -> str:
    """Derive the standard Modustro Python distribution name from the artifact ID."""
    return "eu-algites-" + re.sub(r"[^a-z0-9]+", "-", artifact.lower()).strip("-")


def python_version(version: str, override: str | None) -> str:
    """Convert a Maven release/snapshot to one unique PEP 440 deployment version."""
    if override:
        result = override
    elif re.fullmatch(r"[0-9]+(?:\.[0-9]+)*-SNAPSHOT", version):
        result = version.removesuffix("-SNAPSHOT") + ".dev" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:17]
    elif re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
        result = version
    else:
        raise ValueError(f"Unsupported Java version {version!r}; set MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_VERSION")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*(?:\.dev[0-9]+)?", result):
        raise ValueError(f"Invalid bootstrap Python version {result!r}")
    return result


def version_spec(requirement: dict | None, default_version: str) -> str:
    """Render descriptor-native release bounds without importing the Modustro Builder."""
    value = requirement or {}
    if "Exact" in value:
        exact = str(value["Exact"])
        if exact.endswith("-SNAPSHOT"):
            minor = exact.removesuffix("-SNAPSHOT")
            return f">={minor}.dev0,<{minor}a0"
        return f"=={exact}"
    bounds = []
    for key, sign in (("Minimum", ">="), ("Maximum", "<=")):
        if key not in value:
            continue
        raw = str(value[key])
        if raw.startswith((">=", "<=", "==", ">", "<")):
            bounds.append(raw)
        else:
            bounds.append(("<" if key == "Maximum" and value.get("MaximumStrict") else sign) + raw)
    if not bounds:
        return version_spec({"Exact": default_version}, default_version)
    return ",".join(bounds)


def descriptor_dependencies(data: dict, version: str, python_release: str) -> list[str]:
    """Use only production-level declared Modustro and Python dependencies."""
    dependencies = []
    for group in data.get("Dependencies", []):
        kind = group.get("DependencyKind")
        if kind not in ("modustro", "python"):
            continue
        for item in group.get("Items", []):
            usages = item.get("Usages", [])
            if not any(name in ("product_api", "product_implementation") for name in usages):
                continue
            artifact_id = item["ArtifactId"]
            name = normalized_distribution(artifact_id) if kind == "modustro" else artifact_id.lower().replace("_", "-")
            if kind == "modustro" and artifact_id.startswith(BOOTSTRAP_NAME + "."):
                # The six Codegen wheels form one bootstrap snapshot; never mix
                # current intf/impl/cli with an older compatible-range snapshot.
                spec = "==" + python_release
            else:
                spec = version_spec(item.get("VersionRequirement"), version) if kind == "modustro" or item.get("VersionRequirement") else ""
            dependencies.append(name + spec)
    return list(dict.fromkeys(dependencies))


def stage_artifact(repository: Path, work: Path, generator: str, part: str, version: str, python_release: str) -> tuple[str, Path]:
    """Construct an isolated PEP 420 setuptools project from one source artifact."""
    artifact = repository / "generators" / "code" / generator / part
    document = yaml.safe_load((artifact / "modustro-artifact.yml").read_text(encoding="utf-8"))
    technologies = document["Artifact"]["TechnologyKinds"]
    if "python" not in technologies:
        raise ValueError(f"{artifact} does not declare a Python product")
    name = normalized_distribution(f"{BOOTSTRAP_NAME}.{generator}.{part}")
    project = work / f"{generator}-{part}"
    root = project / "src"
    root.mkdir(parents=True)
    count = 0
    for location in SOURCE_DIRS:
        source_root = artifact / location
        if not source_root.is_dir():
            continue
        for source in sorted(source_root.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo"):
                continue
            relative = source.relative_to(source_root)
            destination = root / relative
            if destination.is_file():
                if destination.read_bytes() != source.read_bytes():
                    raise ValueError(f"Conflicting staged files in {name}: {relative}")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            count += 1
    if not count or not any(root.rglob("*.py")):
        raise ValueError(f"No Python product sources for {name}")
    license_file = repository / "LICENSE"
    if license_file.is_file():
        shutil.copy2(license_file, project / "LICENSE")
    requirements = descriptor_dependencies(document, version, python_release)
    description = document["Artifact"].get("Description", f"Algites {generator} {part}")
    # TOML strings and lists use JSON quoting, which is also TOML-compatible.
    manifest = (f'[build-system]\nrequires = ["setuptools>=69", "wheel"]\n'
                f'build-backend = "setuptools.build_meta"\n\n'
                f'[project]\nname = {json.dumps(name)}\nversion = {json.dumps(python_release)}\n'
                f'description = {json.dumps(description)}\nrequires-python = ">=3.11"\n'
                f'dependencies = {json.dumps(requirements)}\n\n'
                f'[tool.setuptools.packages.find]\nwhere = ["src"]\nnamespaces = true\n\n'
                f'[tool.setuptools.package-data]\n"*" = ["*.settings", "*.yaml", "*.yml", "*.json", "*.py"]\n')
    (project / "pyproject.toml").write_text(manifest, encoding="utf-8")
    (project / "MANIFEST.in").write_text("recursive-include src *.py *.settings *.yaml *.yml *.json\n", encoding="utf-8")
    return name, project


def verify_wheel(wheel: Path, name: str, generator: str, part: str, release: str) -> None:
    """Validate metadata, product files, default settings, and new CLI contract."""
    with zipfile.ZipFile(wheel) as archive:
        entries = archive.namelist()
        metas = [path for path in entries if path.endswith(".dist-info/METADATA")]
        if len(metas) != 1:
            raise ValueError(f"Missing/ambiguous wheel metadata: {wheel}")
        metadata = email.message_from_bytes(archive.read(metas[0]))
        if re.sub(r"[-_.]+", "-", metadata["Name"].lower()) != name or metadata["Version"] != release:
            raise ValueError(f"Incorrect wheel identity/version: {wheel}")
        if not any(path.endswith(".py") and path.startswith("eu/algites/tool/codegen/") for path in entries):
            raise ValueError(f"Wheel has no Codegen Python sources: {wheel}")
        if part == "intf":
            settings = f"eu/algites/tool/codegen/{'defs' if generator == 'defscodegen' else 'sdo'}/algites-{generator}-python-default.settings"
            if settings not in entries:
                raise ValueError(f"Missing packaged default settings: {settings}")
        if part == "cli":
            prefix = "defs" if generator == "defscodegen" else "sdo"
            cli = f"eu/algites/tool/codegen/{prefix}/impl/cli/aic_{prefix}_codegen_cli.py"
            if cli not in entries:
                raise ValueError(f"Missing Python CLI: {cli}")
            body = archive.read(cli).decode("utf-8")
            for option in EXPECTED_CLI_OPTIONS[generator]:
                if option not in body:
                    raise ValueError(f"Outdated Python CLI {cli}: missing {option}")


def verify_sdist(sdist: Path) -> None:
    """Require standard PKG-INFO and real Python product sources in the sdist."""
    with tarfile.open(sdist, "r:gz") as archive:
        paths = archive.getnames()
        if not any(path.endswith("/PKG-INFO") for path in paths):
            raise ValueError(f"Missing PKG-INFO: {sdist}")
        if not any(path.endswith(".py") and "/eu/algites/tool/codegen/" in path for path in paths):
            raise ValueError(f"Missing Python product code in sdist: {sdist}")


def main() -> None:
    """Build and verify all six distributions before exposing an upload manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--maven-version", required=True)
    parser.add_argument("--python-version")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    options = parser.parse_args()
    repository = options.repository.resolve(strict=True)
    output = options.output.absolute()
    manifest = options.manifest.absolute()
    release = python_version(options.maven_version, options.python_version)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="python-packages.", dir=output.parent) as temp:
        stage = Path(temp)
        distribution_dir = stage / "dist"
        distribution_dir.mkdir()
        rows = []
        for generator in GENERATORS:
            for part in PARTS:
                name, project = stage_artifact(repository, stage, generator, part, options.maven_version, release)
                before = set(distribution_dir.iterdir())
                subprocess.run([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(distribution_dir)],
                               cwd=project, check=True)
                created = set(distribution_dir.iterdir()) - before
                wheels = [path for path in created if path.name.endswith(".whl")]
                sdists = [path for path in created if path.name.endswith(".tar.gz")]
                if len(wheels) != 1 or len(sdists) != 1:
                    raise RuntimeError(f"Expected wheel+sdist for {name}; got {sorted(created)}")
                verify_wheel(wheels[0], name, generator, part, release)
                verify_sdist(sdists[0])
                rows.append((wheels[0].name, sdists[0].name))
                print(f"Verified Python bootstrap distribution: {name} {release}", flush=True)
        # Commit only after every package has been built and verified. On a failed
        # build, an earlier prepared collection remains untouched.
        backup = output.parent / (output.name + ".previous")
        if backup.exists():
            shutil.rmtree(backup)
        if output.exists():
            output.rename(backup)
        try:
            distribution_dir.rename(output)
        except Exception:
            if backup.exists():
                backup.rename(output)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    manifest.write_text("".join(f"{output / wheel}\t{output / sdist}\n" for wheel, sdist in rows), encoding="utf-8")
    print(f"SUCCESS: prepared {len(rows)} Python wheels and {len(rows)} sdists: {manifest}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAILED: Python Codegen bootstrap: {error}", file=sys.stderr)
        sys.exit(1)
