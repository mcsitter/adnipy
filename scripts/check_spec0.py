"""SPEC0 compliance check (pre-commit friendly, stdlib only)."""

import json
import logging
import sys
import tomllib
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal
from urllib.request import urlopen

from packaging.requirements import Requirement
from packaging.version import Version

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger(__name__)

project_file_path: Path = Path(__file__).parent.parent / "pyproject.toml"

core_packages: set[str] = {
    "numpy",
    "scipy",
    "matplotlib",
    "pandas",
    "scikit-image",
    "networkx",
    "scikit-learn",
    "xarray",
    "ipython",
    "zarr",
}

python_support_window: timedelta = timedelta(days=365 * 3)
package_support_window: timedelta = timedelta(days=365 * 2)

current_time: datetime = datetime.now(UTC)
current_quarter_start: datetime = datetime(
    current_time.year,
    3 * ((current_time.month - 1) // 3) + 1,
    1,
    tzinfo=UTC,
)

project_data: dict
with project_file_path.open("rb") as file:
    project_data = tomllib.load(file)

package_cache: dict[str, dict[Version, datetime]] = {}
PYTHON_CACHE: dict[Version, datetime] | None = None


def fetch_python_releases() -> dict[Version, datetime]:
    """Fetch Python minor release dates from python.org API."""
    global PYTHON_CACHE  # noqa: PLW0603
    if PYTHON_CACHE is not None:
        return PYTHON_CACHE

    with urlopen(
        "https://www.python.org/api/v2/downloads/release/",
        timeout=10,
    ) as response:
        raw_data = json.loads(response.read().decode())

    releases: dict[Version, datetime] = {}

    for entry in raw_data:
        if "install" in entry["name"].lower():
            continue
        parsed_version: Version = Version(entry["name"].split()[1])
        if parsed_version.major == 2 or parsed_version.micro != 0:  # noqa: PLR2004
            continue
        minor_version: Version = Version(
            f"{parsed_version.major}.{parsed_version.minor}",
        )
        release_date: datetime = datetime.fromisoformat(entry["release_date"])
        releases[minor_version] = release_date

    PYTHON_CACHE = dict(sorted(releases.items()))
    return PYTHON_CACHE


def get_minimum_python_version() -> Version:
    """Extract minimum Python version from pyproject.toml."""
    python_requirement: str = project_data["project"]["requires-python"]
    return Version(python_requirement.replace(">=", "").strip())


def fetch_package_releases(package_name: str) -> dict[Version, datetime]:
    """Fetch package release data from PyPI and collapse to minor versions."""
    if package_name in package_cache:
        return package_cache[package_name]

    with urlopen(f"https://pypi.org/pypi/{package_name}/json", timeout=10) as response:
        raw_data = json.loads(response.read().decode())
    grouped_releases: dict[Version, list[datetime]] = defaultdict(list)

    for version_string, release_files in raw_data["releases"].items():
        timestamps: list[datetime] = [
            datetime.fromisoformat(file["upload_time_iso_8601"])
            for file in release_files
            if "upload_time_iso_8601" in file
        ]

        if not timestamps:
            continue

        parsed_version: Version = Version(version_string)
        minor_version: Version = Version(
            f"{parsed_version.major}.{parsed_version.minor}",
        )

        grouped_releases[minor_version].append(min(timestamps))

    collapsed_releases: dict[Version, datetime] = {
        version: min(times) for version, times in grouped_releases.items()
    }

    package_cache[package_name] = collapsed_releases
    return collapsed_releases


def output_broken_policy_message(
    spec0_minimum: Version,
    dependency: str,
    actual_minimum: Version,
) -> None:
    """Output a standardized message for broken SPEC0 policy."""
    logger.info(
        "❌ SPEC0 policy recommends "
        "minimum version %s for %s, but requirement allows %s",
        spec0_minimum,
        dependency,
        actual_minimum,
    )


def check_python_version() -> Literal[0, 1]:
    """Check Python version compliance with SPEC0 rules."""
    minimum_required_python: Version = get_minimum_python_version()
    python_releases: dict[Version, datetime] = fetch_python_releases()
    python_releases = {
        version: release_date
        for version, release_date in python_releases.items()
        if release_date >= current_quarter_start - python_support_window
    }
    spec0_minimum = min(python_releases.keys())  # Ensure releases are sorted
    if minimum_required_python < spec0_minimum:
        output_broken_policy_message(spec0_minimum, "python", minimum_required_python)
        return 1
    return 0


def check_dependencies() -> Literal[0, 1]:
    """Check dependency versions against SPEC0 rules."""
    dependencies: list[str] = project_data["project"].get("dependencies", [])
    failure_detected: bool = False

    for dependency_string in dependencies:
        requirement = Requirement(dependency_string)
        package_name = requirement.name

        if package_name not in core_packages:
            continue

        # Fetch all known releases
        releases: dict[Version, datetime] = fetch_package_releases(package_name)

        # Keep only supported SPEC0 window releases
        supported_releases = {
            version: release_date
            for version, release_date in releases.items()
            if release_date >= current_quarter_start - package_support_window
        }

        if not supported_releases:
            logger.warning(
                "❌ No supported releases found for package %s "
                "within the last %d years",
                package_name,
                package_support_window.days // 365,
            )
            failure_detected = True
            continue
        spec0_minimum = min(supported_releases.keys())
        matching_versions = sorted(
            requirement.specifier.filter(
                releases.keys(),
                prereleases=True,
            ),
        )
        if not matching_versions:
            logger.warning(
                "❌ Requirement for package %s matches no known versions",
                package_name,
            )
            failure_detected = True
            continue
        dependency_minimum = matching_versions[0]
        if dependency_minimum < spec0_minimum:
            output_broken_policy_message(
                spec0_minimum,
                package_name,
                dependency_minimum,
            )
            failure_detected = True
    if failure_detected:
        return 1
    return 0


def check_python_classifiers() -> Literal[0, 1]:
    """Check Python trove classifiers against requires-python."""
    classifiers: list[str] = project_data["project"].get("classifiers", [])

    advertised_versions: set[Version] = set()

    for classifier in classifiers:
        prefix = "Programming Language :: Python :: "
        if not classifier.startswith(prefix):
            continue

        version_part = classifier.removeprefix(prefix).strip()

        if version_part in {"3", "3 :: Only"}:
            continue

        advertised_versions.add(Version(version_part))

    minimum_required_python: Version = get_minimum_python_version()

    python_releases = fetch_python_releases()
    supported_versions = {
        version
        for version, release_date in python_releases.items()
        if (
            release_date >= current_quarter_start - python_support_window
            and version >= minimum_required_python
        )
    }

    failure_detected = False

    missing = supported_versions - advertised_versions
    extra = advertised_versions - supported_versions

    for version in sorted(missing):
        logger.warning(
            "❌ Missing Python classifier for supported version %s",
            version,
        )
        failure_detected = True

    for version in sorted(extra):
        logger.warning(
            "❌ Classifier advertises unsupported Python version %s",
            version,
        )
        failure_detected = True

    if "Programming Language :: Python :: 3 :: Only" not in classifiers:
        logger.warning(
            "❌ Missing classifier: 'Programming Language :: Python :: 3 :: Only'",
        )
        failure_detected = True

    if failure_detected:
        return 1
    return 0


def main() -> int:
    """Run all SPEC0 checks."""
    python_result: int = check_python_version()
    dependencies_result: int = check_dependencies()
    python_classifiers_result: int = check_python_classifiers()
    return python_result or dependencies_result or python_classifiers_result


if __name__ == "__main__":
    sys.exit(main())
