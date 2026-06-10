import json
from collections import defaultdict, Counter
from datetime import date
import os

def categorise(msg):
    if 'resourceTypeGeneral' in msg and 'enumeration' in msg:
        return 'invalid_resource_type'
    if "'licenses_uri__' not defined" in msg or ('rightsURI' in msg and 'anyURI' in msg):
        return 'invalid_rights_uri'
    if 'familyName' in msg and 'creatorName' in msg:
        return 'creator_element_order'
    if "contributorType' is required but missing" in msg:
        return 'missing_contributor_type'
    if 'Missing child element' in msg and 'contributorName' in msg:
        return 'missing_contributor_name'
    if 'funderName' in msg and 'minLength' in msg:
        return 'empty_funder_name'
    if 'resourceTypeGeneral' in msg and 'required' in msg:
        return 'missing_required_attr'
    return 'other'


LABELS = {
    'invalid_resource_type':    'Invalid resourceTypeGeneral value',
    'invalid_rights_uri':       'Invalid rightsURI (unresolved placeholder)',
    'creator_element_order':    'Wrong element order in <creator>',
    'missing_contributor_type': 'Missing contributorType attribute',
    'missing_contributor_name': 'Missing <contributorName> child element',
    'empty_funder_name':        'Empty <funderName> (minLength violated)',
    'missing_required_attr':    'Missing required resourceTypeGeneral attribute',
    'other':                    'Other / uncategorised',
}

FIXES = {
    'invalid_resource_type':    'Value stored as "ConferenceProceeding\\"" — remove the trailing double-quote character.',
    'invalid_rights_uri':       "Field contains the literal string ['licenses_uri__' not defined] instead of a real URI. Fix the template/export pipeline that generates this field.",
    'creator_element_order':    '<familyName> and <givenName> appear before <creatorName>, but the schema requires <creatorName> first.',
    'missing_contributor_type': 'Each <contributor> element must have a contributorType attribute (e.g. ContactPerson, Editor, etc.).',
    'missing_contributor_name': '<contributor> block is present but contains no <contributorName> child.',
    'empty_funder_name':        '<funderName> exists but its text content is an empty string; minLength=1 requires at least one character.',
    'missing_required_attr':    '<resourceType> element is missing the required resourceTypeGeneral attribute entirely.',
    'other':                    'See affected files for details.',
}


def generate_report(results_path, out_dir="logs/"):
    with open(results_path) as f:
        data = json.load(f)

    out_dir.replace("/", os.sep)
    out_path = os.path.join(out_dir, ("validation_report_" + results_path[-24:-5] + ".txt"))
    print(out_path)
    
    total = len(data)
    valid = sum(1 for v in data.values() if v['valid'])
    invalid = total - valid

    category_files = defaultdict(set)
    category_errors = Counter()

    for fname, result in data.items():
        for err in result['errors']:
            k = categorise(err)
            category_files[k].add(fname)
            category_errors[k] += 1

    lines = []
    lines.append("=" * 72)
    lines.append("  DATACITE XML VALIDATION REPORT")
    lines.append(f"  Generated: {date.today().isoformat()}")
    lines.append("=" * 72)
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total records examined : {total:,}")
    lines.append(f"  Valid                  : {valid:,}  ({valid/total*100:.1f}%)")
    lines.append(f"  Invalid                : {invalid:,}  ({invalid/total*100:.1f}%)")
    lines.append(f"  Total error instances  : {sum(category_errors.values()):,}")
    lines.append("")
    lines.append("")
    lines.append("ERROR BREAKDOWN BY TYPE")
    lines.append("-" * 40)

    for i, (k, count) in enumerate(category_errors.most_common(), 1):
        n_files = len(category_files[k])
        lines.append(f"{i}. {LABELS[k]}")
        lines.append(f"   Affected files   : {n_files}  |  Error instances: {count}")
        lines.append(f"   How to fix       : {FIXES[k]}")
        lines.append(f"   Affected files:")
        for fname in sorted(category_files[k]):
            lines.append(f"     - {fname}")
        lines.append("")

    lines.append("")
    lines.append("=" * 72)
    lines.append("END OF REPORT")
    lines.append("=" * 72)

    report = "\n".join(lines)
    with open(out_path, "w") as f:
        f.write(report)
    print(f"Report written to: {out_path}")

    return out_path


if __name__ == "__main__":
    filename = os.path.join("logs", "validation_report_") + date.today().isoformat() + ".txt"
    generate_report("logs/validation_results_2026-06-09_13-14-14.json", filename)
