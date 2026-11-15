#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 1
FILES = ("manifest.json", "main.js")
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com/{repo}/{tag}/{file}"


def download(url: str, token: str | None = None) -> bytes | None:
    headers = {"User-Agent": "guoapp-modules-index"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def latest_tag(repo: str, token: str | None) -> str | None:
    raw = download(f"{API}/repos/{repo}/releases/latest", token)
    return None if raw is None else json.loads(raw)["tag_name"]


def entry_for(repo: str, tag: str, files: dict[str, bytes]) -> dict:
    manifest = json.loads(files["manifest.json"])
    return {
        "id": manifest["id"],
        "name": manifest["name"],
        "version": manifest["version"],
        "description": manifest.get("description", ""),
        "api": manifest["api"],
        "adult": manifest["adult"],
        "repo": repo,
        "tag": tag,
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="按各模块仓库的最新 Release 更新 index.json")
    parser.add_argument("--checker", type=Path, required=True, help="check_module.py 所在目录")
    parser.add_argument("--trusted", required=True, help="可信组织，其下的仓库直接更新")
    parser.add_argument("--scope", choices=("trusted", "community"), required=True)
    parser.add_argument("--summary", type=Path, help="把变更说明写入此文件")
    args = parser.parse_args()
    sys.path.insert(0, str(args.checker.resolve()))
    from check_module import problems

    token = os.environ.get("GH_TOKEN")
    repos = json.loads((ROOT / "modules.json").read_text(encoding="utf-8"))["repos"]
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    entries = {}
    changes, warnings = [], []
    for entry in index["modules"]:
        if entry["repo"] in repos:
            entries[entry["repo"]] = entry
        else:
            changes.append(f"- 撤下 {entry['name']}（{entry['repo']}）")
    for repo in repos:
        trusted = repo.split("/")[0].lower() == args.trusted.lower()
        if trusted != (args.scope == "trusted"):
            continue
        tag = latest_tag(repo, token)
        if tag is None:
            warnings.append(f"{repo}：仓库不存在或还没有 Release")
            continue
        previous = entries.get(repo)
        if previous and previous["tag"] == tag:
            continue
        files = {name: download(RAW.format(repo=repo, tag=tag, file=name)) for name in FILES}
        missing = [name for name, data in files.items() if data is None]
        if missing:
            warnings.append(f"{repo} {tag}：缺少 {'、'.join(missing)}")
            continue
        errors = problems(files["manifest.json"], files["main.js"], repo=repo.split("/")[1], tag=tag)
        if errors:
            warnings.append(f"{repo} {tag}：" + "；".join(errors))
            continue
        entry = entry_for(repo, tag, files)
        clash = next((other["repo"] for other in entries.values() if other["id"] == entry["id"] and other["repo"] != repo), None)
        if clash:
            warnings.append(f"{repo} {tag}：标识 {entry['id']} 已被 {clash} 使用")
            continue
        entries[repo] = entry
        if previous:
            changes.append(f"- {entry['name']}（{repo}）{previous['version']} → {entry['version']}，"
                           f"[代码差异](https://github.com/{repo}/compare/{previous['tag']}...{tag})")
        else:
            changes.append(f"- 上架 {entry['name']}（{repo}）{entry['version']}，[代码](https://github.com/{repo}/tree/{tag})")
    index = {"format": FORMAT, "modules": sorted(entries.values(), key=lambda entry: entry["id"])}
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for warning in warnings:
        print(f"::warning::{warning}")
    summary = "\n".join(changes) or "没有变更"
    print(summary)
    if args.summary:
        args.summary.write_text(summary + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
