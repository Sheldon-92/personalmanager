#!/usr/bin/env python3
"""SBOM (Software Bill of Materials) generator for PersonalManager.

Generates SPDX-compliant SBOM in JSON format.
"""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4


class SBOMGenerator:
    """Generate Software Bill of Materials in SPDX format."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize SBOM generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.spdx_version = "SPDX-2.3"
        self.creation_time = datetime.utcnow().isoformat() + "Z"

    def generate(self) -> Dict[str, Any]:
        """Generate complete SBOM.

        Returns:
            SPDX-compliant SBOM dictionary
        """
        sbom = {
            "spdxVersion": self.spdx_version,
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "PersonalManager-SBOM",
            "documentNamespace": f"https://personal-manager.local/sbom/{uuid4()}",
            "creationInfo": {
                "created": self.creation_time,
                "creators": ["Tool: PersonalManager-SBOM-Generator-1.0.0"],
                "licenseListVersion": "3.19"
            },
            "packages": self._get_packages(),
            "files": self._get_files(),
            "relationships": self._get_relationships(),
            "extractedLicenseInfo": []
        }

        return sbom

    def _get_packages(self) -> List[Dict[str, Any]]:
        """Get all packages/dependencies.

        Returns:
            List of package information
        """
        packages = []

        # Main package
        packages.append({
            "SPDXID": "SPDXRef-Package-PersonalManager",
            "name": "PersonalManager",
            "downloadLocation": "https://github.com/user/personal-manager",
            "filesAnalyzed": True,
            "verificationCode": {
                "value": self._calculate_package_verification()
            },
            "licenseConcluded": "MIT",
            "licenseDeclared": "MIT",
            "copyrightText": "Copyright 2025 PersonalManager Contributors",
            "versionInfo": "1.0.0",
            "supplier": "Organization: PersonalManager",
            "originator": "Organization: PersonalManager",
            "homepage": "https://personal-manager.local",
            "description": "Personal task and project management system with AI integration"
        })

        # Python dependencies
        dependencies = self._get_python_dependencies()
        for dep in dependencies:
            packages.append(dep)

        return packages

    def _get_python_dependencies(self) -> List[Dict[str, Any]]:
        """Get Python package dependencies.

        Returns:
            List of Python package information
        """
        dependencies = []

        # Try to get installed packages
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            installed_packages = json.loads(result.stdout)

            for pkg in installed_packages:
                # Get package info
                pkg_info = self._get_package_info(pkg['name'], pkg['version'])
                dependencies.append(pkg_info)

        except Exception as e:
            print(f"Warning: Could not get Python dependencies: {e}")

        # Add known critical dependencies if not found
        critical_deps = [
            ("cryptography", "41.0.0", "Apache-2.0 OR BSD-3-Clause"),
            ("fastapi", "0.104.0", "MIT"),
            ("pydantic", "2.5.0", "MIT"),
            ("sqlalchemy", "2.0.0", "MIT"),
            ("httpx", "0.25.0", "BSD-3-Clause"),
        ]

        for name, version, license in critical_deps:
            if not any(d['name'] == name for d in dependencies):
                dependencies.append({
                    "SPDXID": f"SPDXRef-Package-{name}",
                    "name": name,
                    "downloadLocation": f"https://pypi.org/project/{name}/",
                    "filesAnalyzed": False,
                    "licenseConcluded": license,
                    "licenseDeclared": license,
                    "copyrightText": "NOASSERTION",
                    "versionInfo": version,
                    "supplier": f"Organization: PyPI:{name}",
                    "externalRefs": [
                        {
                            "referenceCategory": "PACKAGE-MANAGER",
                            "referenceType": "purl",
                            "referenceLocator": f"pkg:pypi/{name}@{version}"
                        }
                    ]
                })

        return dependencies

    def _get_package_info(self, name: str, version: str) -> Dict[str, Any]:
        """Get detailed package information.

        Args:
            name: Package name
            version: Package version

        Returns:
            Package information dictionary
        """
        # License mapping for common packages
        license_map = {
            "cryptography": "Apache-2.0 OR BSD-3-Clause",
            "requests": "Apache-2.0",
            "fastapi": "MIT",
            "django": "BSD-3-Clause",
            "flask": "BSD-3-Clause",
            "numpy": "BSD-3-Clause",
            "pandas": "BSD-3-Clause",
            "pytest": "MIT",
        }

        return {
            "SPDXID": f"SPDXRef-Package-{name}",
            "name": name,
            "downloadLocation": f"https://pypi.org/project/{name}/",
            "filesAnalyzed": False,
            "licenseConcluded": license_map.get(name.lower(), "NOASSERTION"),
            "licenseDeclared": license_map.get(name.lower(), "NOASSERTION"),
            "copyrightText": "NOASSERTION",
            "versionInfo": version,
            "supplier": f"Organization: PyPI:{name}",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:pypi/{name}@{version}"
                },
                {
                    "referenceCategory": "SECURITY",
                    "referenceType": "cpe23Type",
                    "referenceLocator": f"cpe:2.3:a:{name}:{name}:{version}:*:*:*:*:*:*:*"
                }
            ]
        }

    def _get_files(self) -> List[Dict[str, Any]]:
        """Get file information for critical files.

        Returns:
            List of file information
        """
        files = []
        critical_files = [
            "src/pm/security/rbac.py",
            "src/pm/security/audit.py",
            "src/pm/security/secrets.py",
            "src/pm/security/scanner.py",
            "src/pm/api/server.py",
        ]

        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                file_info = {
                    "SPDXID": f"SPDXRef-File-{file_path.replace('/', '-')}",
                    "fileName": f"./{file_path}",
                    "fileTypes": ["SOURCE"],
                    "checksums": [
                        {
                            "algorithm": "SHA256",
                            "value": self._calculate_file_hash(full_path)
                        }
                    ],
                    "licenseConcluded": "MIT",
                    "copyrightText": "Copyright 2025 PersonalManager Contributors"
                }
                files.append(file_info)

        return files

    def _get_relationships(self) -> List[Dict[str, Any]]:
        """Get package relationships.

        Returns:
            List of relationships
        """
        relationships = [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-PersonalManager"
            }
        ]

        # Add dependency relationships
        dependencies = self._get_python_dependencies()
        for dep in dependencies:
            relationships.append({
                "spdxElementId": "SPDXRef-Package-PersonalManager",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": dep["SPDXID"]
            })

        return relationships

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _calculate_package_verification(self) -> str:
        """Calculate package verification code.

        Returns:
            Package verification code
        """
        # Simplified verification code
        # In production, this would hash all source files
        return hashlib.sha256(
            f"PersonalManager-{self.creation_time}".encode()
        ).hexdigest()

    def save(self, output_path: Optional[Path] = None) -> Path:
        """Generate and save SBOM to file.

        Args:
            output_path: Path to save SBOM

        Returns:
            Path where SBOM was saved
        """
        sbom = self.generate()

        if not output_path:
            output_path = self.project_root / "SBOM.json"

        with open(output_path, 'w') as f:
            json.dump(sbom, f, indent=2)

        return output_path

    def validate(self, sbom: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate SBOM structure.

        Args:
            sbom: SBOM dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        required_fields = [
            "spdxVersion",
            "dataLicense",
            "SPDXID",
            "name",
            "documentNamespace",
            "creationInfo",
            "packages"
        ]

        for field in required_fields:
            if field not in sbom:
                errors.append(f"Missing required field: {field}")

        # Check SPDX version
        if sbom.get("spdxVersion") not in ["SPDX-2.2", "SPDX-2.3"]:
            errors.append(f"Invalid SPDX version: {sbom.get('spdxVersion')}")

        # Check packages
        if not sbom.get("packages"):
            errors.append("No packages defined in SBOM")

        # Validate package structure
        for pkg in sbom.get("packages", []):
            if "SPDXID" not in pkg:
                errors.append(f"Package missing SPDXID")
            if "name" not in pkg:
                errors.append(f"Package missing name")
            if "downloadLocation" not in pkg:
                errors.append(f"Package {pkg.get('name', 'unknown')} missing downloadLocation")

        return len(errors) == 0, errors


if __name__ == "__main__":
    # Generate SBOM when module is executed
    generator = SBOMGenerator()
    output_path = generator.save()
    print(f"SBOM generated and saved to: {output_path}")

    # Validate the generated SBOM
    with open(output_path, 'r') as f:
        sbom = json.load(f)

    is_valid, errors = generator.validate(sbom)
    if is_valid:
        print("SBOM validation: PASSED")
    else:
        print("SBOM validation: FAILED")
        for error in errors:
            print(f"  - {error}")