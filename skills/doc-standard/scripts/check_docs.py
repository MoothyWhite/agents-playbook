#!/usr/bin/env python3
"""文档机械检查门禁。

检查项:
- 一段一行（段落拆成多个物理行）
- 历史叙述禁用词（只写当前状态）
- 相对链接与锚点有效性
- 每文件恰好一个 H1，且为 frontmatter 之后的第一行内容
- 逐文件长度预算（doc-budgets.json manifest，或 --max-lines 全局上限）
- 命名与章节骨架（doc-structure.json manifest：按目录声明文件名正则与必备 H2 章节，
  同目录的 README.md/AGENTS.md 豁免；目录值可用 {"rules": [...]} 为混居的多个文档家族
  各定模式与骨架，规则内 exclude 按文件名或相对目录路径豁免特殊文件）
- 文档代码块真实编译/语法检查（python/json/bash 内建；js 需 node；ts 需 tsc，
  ts 块仅缺模块导入（TS2307）时记为跳过而非失败）

用法: python3 check_docs.py [--max-lines N] [--budget-manifest FILE] [--structure-manifest FILE] [--no-code] <文件或目录>...
退出码: 0 全部通过; 1 存在违规。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HISTORY_WORDS = [
    "之前是", "现在是", "不再是", "曾经是", "已改名", "已移动", "以前",
    " formerly", "previously", "no longer", "used to", "renamed", "was moved",
]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
H1_RE = re.compile(r"^#\s+")
H2_RE = re.compile(r"^##(?!#)\s+(.*)$")
FENCE_RE = re.compile(r"^\s*```(\w*)")

# 结构检查中豁免的导航/指令文件（按小写文件名匹配）
STRUCT_EXEMPT = {"readme.md", "agents.md"}

# 单条结构规则: (文件名正则, 必备 H2 章节, 豁免文件名/相对路径)
StructRule = tuple[re.Pattern | None, list[str], set[str]]


def iter_md_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md" and p.is_file():
            files.append(p)
    return files


def slugify(heading: str) -> str:
    """GitHub 风格锚点：小写、去标点、空格转连字符（CJK 字符保留）。"""
    text = heading.strip().lower()
    text = re.sub(r"[^\w一-鿿\- ]", "", text)
    return text.replace(" ", "-")


# ---------- 代码块检查 ----------

def check_python(code: str) -> str | None:
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"python 语法错误: {exc.msg}（块内第 {exc.lineno} 行）"


def check_json(code: str) -> str | None:
    try:
        json.loads(code)
        return None
    except json.JSONDecodeError as exc:
        return f"json 解析错误: {exc.msg}（块内第 {exc.lineno} 行）"


def check_bash(code: str) -> str | None:
    bash = shutil.which("bash")
    if not bash:
        return None
    proc = subprocess.run([bash, "-n"], input=code, capture_output=True, text=True)
    if proc.returncode != 0:
        return f"bash 语法错误: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else '未知'}"
    return None


def check_js(code: str) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        proc = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if proc.returncode != 0:
            lines = proc.stderr.strip().splitlines()
            detail = next((l for l in lines if "Error" in l), lines[-1] if lines else "未知")
            return f"js 语法错误: {detail}"
        return None
    finally:
        Path(tmp).unlink(missing_ok=True)


def find_tsc() -> str | None:
    local = Path.cwd() / "node_modules" / ".bin" / "tsc"
    if local.is_file():
        return str(local)
    return shutil.which("tsc")


def check_ts(code: str) -> str | None:
    tsc = find_tsc()
    if not tsc:
        return None
    # 在空临时目录中编译：cwd 存在 tsconfig.json 时新版 tsc 报 TS5112 拒绝编译
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "block.ts").write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [tsc, "--noEmit", "--strict", "--skipLibCheck", "--target", "es2022",
                 "--module", "esnext", "--moduleResolution", "bundler", "block.ts"],
                capture_output=True, text=True, timeout=60, cwd=tmpdir,
            )
            if proc.returncode == 0:
                return None
            errors = [l for l in proc.stdout.splitlines() if "error TS" in l]
            # 仅缺模块导入（TS2307）视为不可移植检查，跳过
            if errors and all("TS2307" in l for l in errors):
                return None
            first = errors[0] if errors else (proc.stdout.strip().splitlines() or ["未知"])[0]
            return f"ts 编译错误: {first}"
        except subprocess.TimeoutExpired:
            return "ts 编译超时"


CODE_CHECKERS = {
    "python": check_python, "py": check_python,
    "json": check_json,
    "bash": check_bash, "sh": check_bash,
    "javascript": check_js, "js": check_js, "mjs": check_js,
    "typescript": check_ts, "ts": check_ts,
}


# ---------- 单文件检查 ----------

def check_file(
    path: Path,
    max_lines: int,
    budget: dict | None = None,
    check_code: bool = True,
    langs_seen: set[str] | None = None,
) -> list[str]:
    problems: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{path}: 无法读取: {exc}"]
    lines = text.splitlines()

    line_limit = (budget or {}).get("max_lines", max_lines)
    char_limit = (budget or {}).get("max_chars")
    if len(lines) > line_limit:
        problems.append(f"{path}: {len(lines)} 行，超过上限 {line_limit}（先迁移、再压缩、最后才提额）")
    if char_limit is not None and len(text) > char_limit:
        problems.append(f"{path}: {len(text)} 字符，超过上限 {char_limit}（先迁移、再压缩、最后才提额）")

    # 跳过 YAML frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break

    in_code = False
    code_lang = ""
    code_start = 0
    code_buf: list[str] = []
    headings: set[str] = set()
    h1_count = 0
    for i, line in enumerate(lines, 1):
        fence = FENCE_RE.match(line)
        if fence:
            if in_code:
                if check_code and code_lang in CODE_CHECKERS:
                    err = CODE_CHECKERS[code_lang]("\n".join(code_buf))
                    if err:
                        problems.append(f"{path}:{code_start}: ```{code_lang} 代码块无法编译/解析——{err}")
                in_code = False
                code_buf = []
            else:
                in_code = True
                code_lang = fence.group(1)
                code_start = i
                if langs_seen is not None and code_lang in CODE_CHECKERS:
                    langs_seen.add(code_lang)
            continue
        if in_code:
            code_buf.append(line)
            continue
        if i <= start:
            continue
        m = HEADING_RE.match(line)
        if m:
            headings.add(slugify(m.group(1)))
            if H1_RE.match(line):
                h1_count += 1
        # 一段一行：连续的非空正文行（排除列表、表格、标题、引用、HTML、代码围栏）
        if (
            line.strip()
            and i < len(lines)
            and lines[i].strip()
            and not FENCE_RE.match(lines[i])
            and not re.match(r"^\s*([-*+]|\d+\.)\s", line)
            and not re.match(r"^\s*([-*+]|\d+\.)\s", lines[i])
            and not line.lstrip().startswith(("#", "|", ">", "<"))
            and not lines[i].lstrip().startswith(("#", "|", ">", "<"))
        ):
            problems.append(f"{path}:{i}: 段落被拆成多个物理行（应一段一行，用编辑器软换行）")
        # 行内代码与引号内的提及是规则示例，不算违规
        prose = re.sub(r"`[^`]*`", "", line)
        prose = re.sub(r'"[^"]*"', "", prose)
        prose = re.sub(r'"[^"]*"', "", prose)
        for word in HISTORY_WORDS:
            if word in prose:
                problems.append(f"{path}:{i}: 历史叙述禁用词 {word.strip()!r}（只写当前状态）")

    # H1：frontmatter 之后的第一行内容必须是全文唯一的 H1
    first_content = next((l for l in lines[start:] if l.strip()), None)
    if first_content is None or not H1_RE.match(first_content):
        problems.append(f"{path}: 文首第一行内容不是 H1（每份文档恰好一个 H1，点明主题）")
    if h1_count > 1:
        problems.append(f"{path}: H1 有 {h1_count} 个，每份文档恰好一个")

    # 相对链接与锚点
    for i, line in enumerate(lines, 1):
        for m in LINK_RE.finditer(line):
            target = m.group(1).split()[0] if m.group(1) else ""
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path
            if file_part and not dest.exists():
                problems.append(f"{path}:{i}: 链接目标不存在: {target}")
            elif anchor and dest.suffix == ".md" and dest.is_file():
                try:
                    dest_headings = {
                        slugify(h.group(1))
                        for h in (HEADING_RE.match(l) for l in dest.read_text(encoding="utf-8").splitlines())
                        if h
                    }
                except (OSError, UnicodeDecodeError):
                    continue
                if slugify(anchor) not in dest_headings and anchor not in dest_headings:
                    problems.append(f"{path}:{i}: 锚点不存在: {target}")
    return problems


# ---------- 预算 manifest ----------

def load_budgets(manifest_arg: str | None) -> tuple[dict[str, dict], Path | None, list[str]]:
    """返回 (按文件预算, manifest 目录, 问题列表)。路径相对于 manifest 所在目录解析。"""
    problems: list[str] = []
    manifest: Path | None = None
    if manifest_arg:
        manifest = Path(manifest_arg)
    else:
        candidate = Path.cwd() / "doc-budgets.json"
        if candidate.is_file():
            manifest = candidate
    if manifest is None:
        return {}, None, problems
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, None, [f"{manifest}: 预算 manifest 无法解析: {exc}"]
    base = manifest.parent.resolve()
    budgets: dict[str, dict] = {}
    for rel, limits in data.get("budgets", data).items():
        target = (base / rel).resolve()
        if not target.is_file():
            problems.append(f"{manifest}: 预算文件缺失: {rel}")
        budgets[str(target)] = limits
    return budgets, base, problems


# ---------- 命名与骨架 manifest ----------

def load_structure(manifest_arg: str | None) -> tuple[list[tuple[Path, list[StructRule]]], list[str]]:
    """返回 (规则列表[(目录, [(文件名正则, 必备 H2 章节, 豁免文件)])], 问题列表)。路径相对于 manifest 所在目录解析。

    目录值可以是单条规则对象，或 {"rules": [...]} 为混居的多个文档家族各定规则；
    规则的 exclude 按文件名或相对目录路径豁免该文件的全部结构检查。
    """
    problems: list[str] = []
    manifest: Path | None = None
    if manifest_arg:
        manifest = Path(manifest_arg)
    else:
        candidate = Path.cwd() / "doc-structure.json"
        if candidate.is_file():
            manifest = candidate
    if manifest is None:
        return [], problems
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{manifest}: 结构 manifest 无法解析: {exc}"]
    base = manifest.parent.resolve()
    rules: list[tuple[Path, list[StructRule]]] = []
    for rel, rule in data.get("structure", data).items():
        target = (base / rel).resolve()
        if not target.is_dir():
            problems.append(f"{manifest}: 结构目录缺失: {rel}")
            continue
        rule_list = rule["rules"] if isinstance(rule, dict) and "rules" in rule else [rule]
        compiled: list[StructRule] = []
        for r in rule_list:
            filename_re: re.Pattern | None = None
            if "filename" in r:
                try:
                    filename_re = re.compile(r["filename"])
                except re.error as exc:
                    problems.append(f"{manifest}: {rel} 的 filename 正则无效: {exc}")
                    break
            compiled.append((filename_re, list(r.get("sections", [])), set(r.get("exclude", []))))
        else:
            rules.append((target, compiled))
    return rules, problems


def extract_h2s(path: Path) -> list[str] | None:
    """按出现顺序提取 H2 文本，跳过 frontmatter 与代码块。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break
    h2s: list[str] = []
    in_code = False
    for i, line in enumerate(lines, 1):
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code or i <= start:
            continue
        m = H2_RE.match(line)
        if m:
            h2s.append(m.group(1).strip().rstrip("#").strip())
    return h2s


def check_structure(rules: list[tuple[Path, list[StructRule]]]) -> list[str]:
    problems: list[str] = []
    for directory, dir_rules in rules:
        for f in sorted(directory.rglob("*.md")):
            if f.name.lower() in STRUCT_EXEMPT:
                continue
            rel = str(f.relative_to(directory))
            applicable = [r for r in dir_rules if r[0] is None or r[0].match(f.name)]
            if any(f.name in r[2] or rel in r[2] for r in applicable):
                continue  # 显式豁免的特殊文件（见 doc-structure.json 的 exclude）
            if not applicable:
                patterns = "、".join(f'"{r[0].pattern}"' for r in dir_rules if r[0])
                problems.append(f"{f}: 文件名不符合该目录的模式 {patterns}（命名模式见 doc-structure.json）")
                continue
            sections = applicable[0][1]
            if not sections:
                continue
            h2s = extract_h2s(f)
            if h2s is None:
                problems.append(f"{f}: 无法读取")
                continue
            pos = 0
            missing: list[str] = []
            for req in sections:
                if req in h2s[pos:]:
                    pos = h2s.index(req, pos) + 1
                else:
                    missing.append(req)
            if missing:
                problems.append(f"{f}: 必备章节缺失或顺序错误: {missing}（骨架: {' → '.join(sections)}）")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="文档规范机械检查")
    parser.add_argument("paths", nargs="+", help="要检查的 Markdown 文件或目录")
    parser.add_argument("--max-lines", type=int, default=800, help="未列入预算的文件行数上限（默认 800）")
    parser.add_argument("--budget-manifest", help="逐文件预算 JSON（默认自动发现 ./doc-budgets.json）")
    parser.add_argument("--structure-manifest", help="命名与骨架 JSON（默认自动发现 ./doc-structure.json）")
    parser.add_argument("--no-code", action="store_true", help="跳过代码块编译检查")
    args = parser.parse_args()

    files = iter_md_files(args.paths)
    budgets, _, manifest_problems = load_budgets(args.budget_manifest)
    structure_rules, structure_problems = load_structure(args.structure_manifest)
    if not files:
        print("未找到 Markdown 文件", file=sys.stderr)
        return 1

    all_problems: list[str] = list(manifest_problems) + structure_problems
    langs_seen: set[str] = set()
    for f in files:
        all_problems.extend(
            check_file(f, args.max_lines, budgets.get(str(f.resolve())),
                       check_code=not args.no_code, langs_seen=langs_seen)
        )
    all_problems.extend(check_structure(structure_rules))

    # 工具链缺失不算违规，但必须明示跳过，避免"检查了"的错觉
    if not args.no_code:
        if langs_seen & {"javascript", "js", "mjs"} and not shutil.which("node"):
            print("注意：存在 js 代码块但找不到 node，js 编译检查已跳过", file=sys.stderr)
        if langs_seen & {"typescript", "ts"} and not find_tsc():
            print("注意：存在 ts 代码块但找不到 tsc，ts 编译检查已跳过", file=sys.stderr)

    if all_problems:
        print("\n".join(all_problems))
        print(f"\n共 {len(all_problems)} 处违规")
        return 1
    print(f"通过：{len(files)} 个文件无违规")
    return 0


if __name__ == "__main__":
    sys.exit(main())
