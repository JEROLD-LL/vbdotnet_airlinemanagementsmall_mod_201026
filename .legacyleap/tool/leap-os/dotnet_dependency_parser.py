import os
import json
import xml.etree.ElementTree as ET


# --------------------------
# Path Normalization
# --------------------------
def normalize_path(path: str) -> str:
    """Normalize Windows-style slashes coming from .sln files."""
    return path.replace("\\", "/")


# --------------------------
# Parse packages.config (OLD NuGet format)
# --------------------------
def parse_packages_config(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse packages.config: {str(e)}"}

    packages = []
    for pkg in root.findall("package"):
        packages.append({
            "id": pkg.attrib.get("id"),
            "version": pkg.attrib.get("version"),
            "targetFramework": pkg.attrib.get("targetFramework")
        })
    return packages


# --------------------------
# Parse .csproj (NEW + OLD formats)
# --------------------------
def parse_csproj(csproj_path):
    try:
        tree = ET.parse(csproj_path)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse .csproj: {str(e)}"}

    # Extract namespace (for legacy MSBuild format)
    ns = ""
    if "}" in root.tag:
        ns = root.tag.split("}")[0] + "}"

    project_info = {
        "path": csproj_path,
        "sdk": root.attrib.get("Sdk"),
        "target_frameworks": [],
        "package_references": [],
        "project_references": [],
        "assembly_references": [],
        "packages_config": None,
    }

    # NEW format: <TargetFramework> or <TargetFrameworks>
    tf = root.find(f".//{ns}TargetFramework")
    tfs = root.find(f".//{ns}TargetFrameworks")

    if tf is not None and tf.text:
        project_info["target_frameworks"].append(tf.text)

    if tfs is not None and tfs.text:
        project_info["target_frameworks"] += [x.strip() for x in tfs.text.split(";")]

    # OLD format: <TargetFrameworkVersion>
    tfv = root.find(f".//{ns}TargetFrameworkVersion")
    if tfv is not None and tfv.text:
        project_info["target_frameworks"].append(tfv.text)

    # PARSE PackageReference (modern NuGet)
    for pkg in root.findall(f".//{ns}PackageReference"):
        project_info["package_references"].append({
            "name": pkg.attrib.get("Include"),
            "version": pkg.attrib.get("Version")
        })

    # PARSE ProjectReference
    for pref in root.findall(f".//{ns}ProjectReference"):
        project_info["project_references"].append({
            "name": pref.attrib.get("Include"),
            "path": pref.attrib.get("Include")
        })

    # PARSE OLD Reference + HintPath
    for ref in root.findall(f".//{ns}Reference"):
        name = ref.attrib.get("Include")
        hint_node = ref.find(f"{ns}HintPath")

        version = None
        hint_path = hint_node.text if hint_node is not None else None
        is_from_package = False

        # Extract version from Include="Foo, Version=x.x.x.x"
        if name and "Version=" in name:
            try:
                version = name.split("Version=")[1].split(",")[0]
            except:
                pass

        # Extract version from HintPath .../Package.1.2.3/lib/...
        if hint_path:
            # Check if this assembly is from a NuGet package (contains "packages" folder)
            normalized_hint = hint_path.replace("\\", "/").lower()
            if "packages/" in normalized_hint or "/packages/" in normalized_hint:
                is_from_package = True
            
            parts = hint_path.replace("\\", "/").split("/")
            for p in parts:
                if any(c.isdigit() for c in p) and "." in p:
                    version = p
                    break

        # Only add assembly if it's NOT from a NuGet package
        # (package will be represented separately in packages_config)
        if not is_from_package:
            project_info["assembly_references"].append({
                "name": name,
                "version": version,
                "hint_path": hint_path
            })

    # Read packages.config if present
    pkg_config = os.path.join(os.path.dirname(csproj_path), "packages.config")
    if os.path.exists(pkg_config):
        project_info["packages_config"] = parse_packages_config(pkg_config)

    return project_info


# --------------------------
# Parse .sln
# --------------------------
def parse_sln(sln_path):
    solution_dir = os.path.dirname(sln_path)

    solution = {
        "solution_path": sln_path,
        "projects": [],
        "dependencies": {
            "package_references": [],
            "project_references": [],
            "assembly_references": []
        }
    }

    with open(sln_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith("Project("):
            parts = line.split("=")
            if len(parts) < 2:
                continue

            project_info = parts[1].strip().split(",")

            if len(project_info) < 2:
                continue

            project_name = project_info[0].strip().strip('"')
            project_relative_path = project_info[1].strip().strip('"')

            # normalize slashes
            project_relative_path = normalize_path(project_relative_path)

            # Only process .csproj
            if project_relative_path.endswith(".csproj"):
                solution["projects"].append({
                    "name": project_name,
                    "relative_path": project_relative_path,
                    "parsed": None
                })

    # Parse all csproj files
    for proj in solution["projects"]:
        rel = proj["relative_path"]
        csproj_full = os.path.abspath(os.path.join(solution_dir, rel))

        if os.path.exists(csproj_full):
            parsed = parse_csproj(csproj_full)
            proj["parsed"] = parsed

            # Aggregate dependencies at solution level
            if parsed and isinstance(parsed, dict):
                solution["dependencies"]["package_references"] += parsed.get("package_references", [])
                solution["dependencies"]["assembly_references"] += parsed.get("assembly_references", [])
                solution["dependencies"]["project_references"] += parsed.get("project_references", [])
        else:
            proj["parsed"] = {"error": f"csproj not found at: {csproj_full}"}

    return solution


# --------------------------
# Main
# --------------------------
def scan_dotnet_project(root_folder):
    results = {"solutions": []}

    for dirpath, _, files in os.walk(root_folder):
        for f in files:
            if f.endswith(".sln"):
                sln_path = os.path.join(dirpath, f)
                results["solutions"].append(parse_sln(sln_path))

    return results


# --------------------------
# Run script
# --------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse .NET solutions and dependencies.")
    parser.add_argument("folder", help="Root folder containing .NET project")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output JSON file (default: dependency_report.json in the target folder)",
        default=None,
    )
    args = parser.parse_args()

    output = scan_dotnet_project(args.folder)
    # Determine output path
    if args.output:
        out_path = args.output
    else:
        out_path = os.path.join(os.path.abspath(args.folder), "dependency_report.json")

    # Write JSON to file
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    # Also print where the file was written
    print(f"JSON output written to: {out_path}")
