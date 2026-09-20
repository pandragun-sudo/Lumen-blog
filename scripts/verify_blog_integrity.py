#!/usr/bin/env python3
"""
Lumen Insights - Blog Integrity & Quality Linter
================================================
A strict, mechanical verification script that inspects compiled build artifacts (dist/)
to enforce zero-hallucination, zero-leakage, and zero-markdown-breakage rules.

Exit Codes:
  0: All integrity checks passed.
  1: One or more violations detected.
"""

import os
import sys
import re
from pathlib import Path

BLOG_DIR = Path("/Volumes/SSD_Main/03 for YouTube/YouTube Search/Lumen-blog")
DIST_DIR = BLOG_DIR / "dist"
CONTENT_DIR = BLOG_DIR / "src" / "content" / "blog"

# Deleted slugs in v3.0.9 (Must be 301 redirected and removed from sitemap)
DELETED_SLUGS = [
    "2026-08-05-single-video-algorithm-viral",
    "2026-08-24-saas-onboarding-retention",
    "2026-07-21-ai-mastery-digital-clone",
    "2026-08-02-ai-cofounder-leverage",
    "2026-07-20-stop-development-feature-creep",
    "2026-07-20-shorts-reference-chrome-extension",
    "2026-08-12-antigravity-gemini-solo-saas-ep9",
    "2026-08-14-antigravity-gemini-solo-saas-ep11",
]

# Sensitive credentials & forbidden patterns
SENSITIVE_PATTERNS = [
    re.compile(r"1MIN\s*DRAMA", re.IGNORECASE),
    re.compile(r"@onemindrama", re.IGNORECASE),
    re.compile(r"kFeoFxc-DJE"),
    re.compile(r"app\.lumeninsights\.kr"),
    re.compile(r"verifyAccessCodeAPI"),
]

# Broken Korean grammatical patterns from past replacements
BROKEN_KOREAN_PATTERNS = [
    re.compile(r"채널\s+채널"),
    re.compile(r"가파른\s+으로"),
    re.compile(r"가파른\s+이지"),
]

def check_dist_exists():
    if not DIST_DIR.exists():
        print(f"[ERROR] dist/ directory not found at {DIST_DIR}. Run 'npm run build' in Lumen-blog first.")
        return False
    return True

def audit_html_files():
    html_files = list(DIST_DIR.rglob("*.html"))
    if not html_files:
        print("[ERROR] No HTML files found in dist/")
        return False

    violations = []
    
    # 1. Check for raw markdown asterisks (outside of normal script/style where rare)
    # Specifically looking for **word** rendered as raw text in HTML body
    raw_asterisk_pattern = re.compile(r"(?<!\*)\*\*([^*]+)\*\*(?!\*)")

    for html_path in html_files:
        rel_path = html_path.relative_to(DIST_DIR)
        try:
            content = html_path.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(f"Could not read {rel_path}: {e}")
            continue

        # Check raw **
        asterisk_matches = raw_asterisk_pattern.findall(content)
        if asterisk_matches:
            for match in asterisk_matches[:3]:
                violations.append(f"[RAW ASTERISK] {rel_path}: **{match}**")

        # Check sensitive leaks
        for pat in SENSITIVE_PATTERNS:
            found = pat.findall(content)
            if found:
                violations.append(f"[SENSITIVE LEAK] {rel_path}: matched pattern '{pat.pattern}' ({found[:2]})")

        # Check broken Korean
        for pat in BROKEN_KOREAN_PATTERNS:
            found = pat.findall(content)
            if found:
                violations.append(f"[BROKEN KOREAN] {rel_path}: matched pattern '{pat.pattern}' ({found[:2]})")

    if violations:
        print(f"[FAIL] Found {len(violations)} HTML content violations:")
        for v in violations:
            print(f"  - {v}")
        return False

    print(f"[PASS] Audited {len(html_files)} HTML files: 0 raw asterisks, 0 sensitive leaks, 0 broken Korean.")
    return True

def audit_sitemap_and_redirects():
    violations = []

    # Check sitemap
    sitemap_path = DIST_DIR / "sitemap-0.xml"
    if sitemap_path.exists():
        sitemap_content = sitemap_path.read_text(encoding="utf-8")
        for slug in DELETED_SLUGS:
            if f"/blog/{slug}" in sitemap_content:
                violations.append(f"[SITEMAP LEAK] Deleted slug '{slug}' still present in sitemap-0.xml")
    else:
        violations.append("[WARNING] sitemap-0.xml not found in dist/")

    # Check _redirects
    redirects_path = DIST_DIR / "_redirects"
    if redirects_path.exists():
        redirects_content = redirects_path.read_text(encoding="utf-8")
        for slug in DELETED_SLUGS:
            pattern = f"/blog/{slug}"
            if pattern not in redirects_content:
                violations.append(f"[MISSING REDIRECT] Deleted slug '{slug}' missing 301 rule in dist/_redirects")
    else:
        violations.append("[ERROR] _redirects file not found in dist/")

    if violations:
        print(f"[FAIL] Found {len(violations)} sitemap/redirect violations:")
        for v in violations:
            print(f"  - {v}")
        return False

    print(f"[PASS] Sitemap & 301 Redirects: All {len(DELETED_SLUGS)} deleted slugs excluded from sitemap and 100% mapped in _redirects.")
    return True

def audit_content_markdown():
    # Also verify source .md files in content/blog
    if not CONTENT_DIR.exists():
        return True
    
    md_files = list(CONTENT_DIR.glob("*.md"))
    violations = []
    
    for md_path in md_files:
        slug = md_path.stem
        if slug in DELETED_SLUGS:
            violations.append(f"[ZOMBIE POST] Deleted post file still exists in content/blog: {md_path.name}")
            
    if violations:
        print(f"[FAIL] Found {len(violations)} content source violations:")
        for v in violations:
            print(f"  - {v}")
        return False
        
    print(f"[PASS] Source content/blog: 0 zombie posts found ({len(md_files)} active posts).")
    return True

def audit_content_depth():
    # Enforce minimum content depth threshold to prevent Thin Content
    if not CONTENT_DIR.exists():
        return True
        
    md_files = list(CONTENT_DIR.glob("*.md"))
    violations = []
    MIN_CHAR_COUNT = 1500
    MIN_LINE_COUNT = 60
    
    for md_path in md_files:
        content = md_path.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        body = parts[2] if len(parts) >= 3 else content
        body_clean = re.sub(r"\s+", " ", body).strip()
        
        char_count = len(body_clean)
        line_count = len(content.splitlines())
        
        if char_count < MIN_CHAR_COUNT:
            violations.append(f"[THIN CONTENT] {md_path.name}: character count {char_count} < minimum {MIN_CHAR_COUNT}")
        if line_count < MIN_LINE_COUNT:
            violations.append(f"[THIN CONTENT] {md_path.name}: line count {line_count} < minimum {MIN_LINE_COUNT}")
            
    if violations:
        print(f"[FAIL] Found {len(violations)} thin content violations:")
        for v in violations:
            print(f"  - {v}")
        return False
        
    print(f"[PASS] Content Depth Gate: All {len(md_files)} posts satisfy minimum depth (>= {MIN_CHAR_COUNT} chars, >= {MIN_LINE_COUNT} lines).")
    return True

def main():
    print("==================================================")
    print(" Lumen Insights Blog Integrity & Quality Linter  ")
    print("==================================================")
    
    if not check_dist_exists():
        sys.exit(1)

    checks = [
        audit_content_markdown(),
        audit_content_depth(),
        audit_html_files(),
        audit_sitemap_and_redirects(),
    ]

    if all(checks):
        print("==================================================")
        print("[SUCCESS] All blog integrity checks passed (Exit code: 0).")
        print("==================================================")
        sys.exit(0)
    else:
        print("==================================================")
        print("[FAILURE] Blog integrity verification failed. Fix above errors before reporting completion.")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
