"""Render a versioned project review as an offline character-card HTML."""
from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse

SKILL_ROOT = Path(__file__).resolve().parents[1]
TOKEN = "__REPORT_JSON__"


def validate_improvement_plans(report):
    protocol=report.get('recommendation_protocol')
    if protocol is None:
        return
    if protocol!='real-life-improvement-v1':
        raise ValueError('Unknown recommendation protocol')
    for axis in report['axes']:
        plan=axis.get('improvement_plan')
        if not isinstance(plan,dict):
            raise ValueError('Every axis needs a real-life improvement plan')
        for key in ('title','current_gap','target','standard_basis','success'):
            if not isinstance(plan.get(key),str) or not plan[key].strip():
                raise ValueError(f'Improvement plan needs a nonempty {key}')
        targets=plan.get('target_items')
        available={axis['id']+str(i) for i in range(1,7)}
        if not isinstance(targets,list) or not targets or any(not isinstance(i,str) or i not in available for i in targets) or len(set(targets))!=len(targets):
            raise ValueError('Improvement targets must identify unique items from the same axis')
        steps=plan.get('steps')
        if not isinstance(steps,list) or not 1<=len(steps)<=3 or any(not isinstance(s,str) or not s.strip() for s in steps):
            raise ValueError('Provide one to three actual improvement steps')
        if axis.get('actions'):
            raise ValueError('Do not mix legacy actions into the explicit improvement protocol')
        maintenance=axis.get('assessment_maintenance',[])
        if not isinstance(maintenance,list) or any(not isinstance(s,str) or not s.strip() for s in maintenance):
            raise ValueError('Assessment maintenance must be a separate text list')
        sources=plan.get('sources',[])
        if not isinstance(sources,list):
            raise ValueError('Improvement sources must be a list')
        for source in sources:
            if not isinstance(source,dict) or not isinstance(source.get('title'),str) or not source['title'].strip() or not isinstance(source.get('url'),str):
                raise ValueError('Sources need a title and an HTTPS URL')
            parsed=urlparse(source['url'])
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Improvement sources require public HTTPS URLs')


def validate_report(report):
    if not isinstance(report, dict) or report.get("rating_type") not in {"subjective", "anchored_review", "weighted_character"}:
        raise ValueError("rating_type must explicitly identify a subjective or anchored project review")
    title = report.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 10:
        raise ValueError("The review headline must contain 1 to 10 characters")
    axes = report.get("axes")
    if not isinstance(axes, list) or len(axes) != 6 or not all(isinstance(axis, dict) for axis in axes) or [axis.get("id") for axis in axes] != list("ABCDEF"):
        raise ValueError("Provide exactly six axes in A, B, C, D, E, F order; never invent a missing axis")
    for axis in axes:
        score = axis.get("score")
        if score is not None and (type(score) is not int or not 0 <= score <= 100):
            raise ValueError("An axis score must be an integer from 0 to 100, or null when unknown")
    if not isinstance(report.get("method"), dict) or not report["method"].get("label"):
        raise ValueError("Provide a visible method label for the subjective review")
    if not report.get("version"):
        raise ValueError("A review version is required")
    validate_improvement_plans(report)
    life=report.get('life_direction')
    if report.get('presentation_version')=='life-direction-v0.8' and not isinstance(life,dict):
        raise ValueError('Life presentation requires a separately saved life-direction report')
    if life is not None:
        if not isinstance(life,dict) or life.get('version')!='life-direction-report-v1':
            raise ValueError('Unknown life-direction report version')
        if type(life.get('source_revision')) is not int or life['source_revision']<1:
            raise ValueError('Life direction needs its own saved source revision')
        if life.get('score') is not None:
            raise ValueError('Life-direction scores are not defined; retain null')
        observations=life.get('observations',[])
        if not isinstance(observations,list) or any(not isinstance(o,dict) or o.get('score') is not None for o in observations):
            raise ValueError('Life observations must not introduce invented numeric scores')
        directions=life.get('directions',[])
        if not isinstance(directions,list):
            raise ValueError('Life directions must be a list')
        seen=set()
        for direction in directions:
            if not isinstance(direction,dict) or not isinstance(direction.get('id'),str) or not direction['id'] or direction['id'] in seen:
                raise ValueError('Life direction identifiers must be unique nonempty strings')
            seen.add(direction['id'])
            if direction.get('score') is not None:
                raise ValueError('A direction is not a seventh numeric axis')
            relations=direction.get('axis_links',[])
            if not isinstance(relations,list) or any(not isinstance(link,dict) or link.get('axis_id') not in list('ABCDEF') for link in relations):
                raise ValueError('Life context can only refer to the existing six axes')


def build_dashboard(report, template, portrait_path=None):
    if template.count(TOKEN) != 1:
        raise ValueError("The HTML template must contain exactly one report-data token")
    data = copy.deepcopy(report)
    is_v06 = isinstance(data, dict) and data.get('version') == 'weighted-character-v0.6'
    if is_v06:
        spec = importlib.util.spec_from_file_location('character_review_v06', SKILL_ROOT / 'scripts' / 'review_v06.py')
        scoring = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoring)
        data = scoring.calculate_report(data)
    if data.get('presentation_version') in {'joint-profile-v0.7','life-direction-v0.8'}:
        if not is_v06:
            raise ValueError('Joint v0.7 presentation requires the v0.6 scoring protocol')
        joint_spec = importlib.util.spec_from_file_location('character_joint_review', SKILL_ROOT/'scripts'/'joint_review.py')
        joint = importlib.util.module_from_spec(joint_spec)
        joint_spec.loader.exec_module(joint)
        data = joint.calculate_joint(data)
        if isinstance(data.get('financial_facts'), dict):
            context_spec = importlib.util.spec_from_file_location('character_joint_context', SKILL_ROOT/'scripts'/'joint_context.py')
            context = importlib.util.module_from_spec(context_spec)
            context_spec.loader.exec_module(context)
            data['financial_context'] = context.calculate_context(data['financial_facts'])
    validate_report(data)
    if data.get('rating_type') == 'weighted_character' and not is_v06:
        weighted_spec=importlib.util.spec_from_file_location('character_weighted_review',SKILL_ROOT/'scripts'/'weighted_character.py')
        weighted=importlib.util.module_from_spec(weighted_spec)
        weighted_spec.loader.exec_module(weighted)
        data=weighted.calculate_report(data)
    if data.get("rating_type") == "anchored_review":
        spec = importlib.util.spec_from_file_location("character_score_review", SKILL_ROOT / "scripts" / "score_review.py")
        scoring = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoring)
        data = scoring.calculate_report(data)
    if not is_v06 and isinstance(data.get('benchmarks'), dict) and data['benchmarks'].get('version') == 'regional-income-v0.3':
        regional_spec = importlib.util.spec_from_file_location('character_regional_income', SKILL_ROOT / 'scripts' / 'regional_income.py')
        regional = importlib.util.module_from_spec(regional_spec)
        regional_spec.loader.exec_module(regional)
        data['benchmarks'] = regional.calculate_benchmarks(data['benchmarks'])
    if portrait_path is not None:
        portrait = Path(portrait_path)
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(portrait.suffix.lower())
        if not mime:
            raise ValueError("Use a JPEG, PNG, or WebP portrait")
        encoded = base64.b64encode(portrait.read_bytes()).decode("ascii")
        data["portrait"] = f"data:{mime};base64,{encoded}"
    if data.get("portrait") and not str(data["portrait"]).startswith(("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,")):
        raise ValueError("Portraits must be embedded data URLs; remote image URLs are not used")
    encoded = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for raw, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        encoded = encoded.replace(raw, escaped)
    return template.replace(TOKEN, encoded)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--portrait", type=Path)
    parser.add_argument("--template", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.output.suffix.lower() != ".html":
        parser.error("--output must be an HTML file, separate from current.md and the input JSON")
    try:
        report = json.loads(args.data.read_text(encoding="utf-8"))
        template_name = ('dashboard-v08.html' if report.get('presentation_version') == 'life-direction-v0.8'
                         else 'dashboard-v07.html' if report.get('presentation_version') == 'joint-profile-v0.7'
                         else 'dashboard-v06.html' if report.get('version') == 'weighted-character-v0.6'
                         else 'dashboard.html')
        template_path = args.template or SKILL_ROOT / 'assets' / template_name
        if args.output.resolve() in {args.data.resolve(), template_path.resolve()}:
            parser.error("Do not overwrite an input or the selected template")
        rendered = build_dashboard(report, template_path.read_text(encoding="utf-8"), args.portrait)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, prefix=".dashboard-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, args.output)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        print(json.dumps({"ok": True, "output": str(args.output.resolve()), "rating_type": report["rating_type"], "source_revision": report.get("source_revision")}, ensure_ascii=True))
        return 0
    except (OSError, ValueError) as error:
        parser.exit(1, f"Dashboard rendering failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
