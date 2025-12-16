#!/usr/bin/env python3
"""Reorganize GITHUB_ISSUES.md by migration strategy.

This script restructures issues into three categories based on the planned
frontend-v2/ UI redesign and microservices backend split:

- DEFERRED: Backend issues to fix during microservices migration (Weeks 3-10)
- OBSOLETE: Frontend issues replaced by UI redesign (removed from file)
- TRACKED: Low-priority improvements for later

Categorization saves ~35-42 hours (87% reduction) by avoiding throwaway work
on code that will be rewritten during the 10-week migration.

Usage:
    python scripts/reorganize_issues.py

Requirements:
    - GITHUB_ISSUES.md file exists in project root

What It Does:
    1. Reads original GITHUB_ISSUES.md
    2. Categorizes all issues by migration strategy
    3. Adds migration strategy notes to each issue
    4. Removes OBSOLETE issues from file (saved in git history)
    5. Generates new file with DEFERRED and TRACKED sections
    6. Prints summary statistics

Output:
    - Updated GITHUB_ISSUES.md with:
      - Migration strategy header
      - DEFERRED issues (7 backend issues)
      - TRACKED issues (10 low-priority issues)
      - OBSOLETE issues removed (47 frontend issues)
    - Summary statistics in terminal

Examples:
    # Reorganize issues
    python scripts/reorganize_issues.py

    # View obsolete issues in git history
    git log -p GITHUB_ISSUES.md

Exit Codes:
    0 - Successfully reorganized
    1 - File not found or error during processing
"""

# Issue categorization based on migration strategy analysis
DEFERRED_ISSUES = [6, 26, 28, 30, 31, 99, 113]
OBSOLETE_ISSUES = [
    35,
    38,
    39,
    40,
    41,
    42,
    43,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    78,
    79,
    82,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    107,
    108,
    109,
    110,
    111,
]
TRACKED_ISSUES = [14, 21, 100, 101, 102, 103, 104, 105, 106, 112]

HEADER = """# GitHub Issues - Migration Strategy

**Last Updated:** 2025-11-12

## 🎯 Migration Strategy Overview

**Context:** Planned UI redesign (frontend-v2/) + microservices split (10-week timeline)

**Architectural Changes:**
- Complete UI redesign with new design system (keep AG-UI Protocol + WebSocket)
- Backend split into 4 microservices: Chat, Agent, State, Tool Services
- API Gateway (Kong) implementation
- Timeline: ~10 weeks parallel work

**Strategic Decision:** Categorize issues by migration impact to avoid wasted effort (87% time savings).

---

## 📊 Summary Statistics

**Total Issues:** 75

### By Category:
- **⏭️ DEFERRED:** 7 backend issues (9%) - Fix during service implementation
- **🗑️ OBSOLETE:** 47 frontend issues (63%) - **REMOVED FROM FILE** (will be replaced by frontend-v2/)
- **📋 TRACKED:** 10 low-priority issues (13%) - Fix when time permits
- **TOTAL IN FILE:** 17 issues (DEFERRED + TRACKED only)

### By Priority:
- **CRITICAL/HIGH:** 0 issues (✅ PRODUCTION READY)
- **MEDIUM:** 7 issues (deferred to migration)
- **LOW:** 10 issues (tracked for later)

**Obsolete Issues Removed:** 47 frontend issues deleted from file (Issues 35, 38-43, 52-82, 91-98, 107-111). These will not exist in frontend-v2/ redesign.

**Time Savings:** ~35-42 hours (87% reduction) by strategic deferral + removal of obsolete work.

---

## 💡 How to Use This Document

### ⏭️ DEFERRED Issues
**What:** Backend issues that require refactoring during microservices split.
**When to Fix:** During corresponding service implementation (Weeks 3-10 of migration).
**Why Deferred:** Code will be refactored anyway; fixing now = wasted effort.

### 📋 TRACKED Issues
**What:** Low-priority quality improvements that don't block anything.
**When to Fix:** When spare time available, not urgent.
**Why Tracked:** Nice-to-haves that can wait until after migration.

### ❌ OBSOLETE Issues (REMOVED)
**What:** 47 frontend issues (Issues 35, 38-43, 52-82, 91-98, 107-111) have been removed from this file.
**Why Removed:** Complete UI redesign (frontend-v2/) means these issues won't exist in new codebase.
**Reference:** See git history (commit before this reorganization) if you need to review deleted issues.

---

## ⏭️ DEFERRED ISSUES (7 Backend Issues)

**Strategy:** Fix during microservices implementation, not before.

**Rationale:** All these issues affect backend code that will be refactored when splitting into microservices. Fixing them now would create throwaway work since we'll rewrite these components during the migration.

**Migration Timeline:**
- **Weeks 3-4:** State Service implementation → Fix Issue 99
- **Weeks 5-6:** Chat Service implementation → Fix Issues 30, 31
- **Weeks 7-8:** Agent Service implementation → Fix Issues 6, 113
- **Weeks 9-10:** API Gateway implementation → Fix Issues 26, 28

---

"""


def extract_issue_content(lines, issue_num):
    """Extract complete issue content from file lines."""
    start_marker = f"## Issue {issue_num}:"
    content = []
    found = False

    for _, line in enumerate(lines):
        if found:
            # Stop at next issue or end of file
            if line.startswith("## Issue ") and f"Issue {issue_num}:" not in line:
                break
            if line.startswith("## Summary of") or line.startswith("## Agent Review"):
                break
            content.append(line)
        elif start_marker in line:
            found = True
            content.append(line)

    return "".join(content).strip()


def add_migration_note(issue_num, category):
    """Generate migration strategy note for an issue."""

    # DEFERRED notes by issue
    deferred_notes = {
        6: {
            "service": "Agent Service",
            "week": "Weeks 7-8",
            "rationale": "ReasoningRouter configuration will be redesigned as part of Agent Service microservice. New service will have proper config management patterns.",
            "workaround": "Phase 1 placeholder feature, not needed for Phase 0.",
        },
        26: {
            "service": "API Gateway",
            "week": "Weeks 9-10",
            "rationale": "API Gateway (Kong) will implement centralized health checks with dependency status for all microservices. Don't build this in monolith.",
            "workaround": "Basic health check works for Phase 0.",
        },
        28: {
            "service": "All Microservices",
            "week": "Weeks 9-10",
            "rationale": "Each microservice will have its own version management. Implement consistent versioning strategy during service creation.",
            "workaround": "Hardcoded version acceptable for Phase 0.",
        },
        30: {
            "service": "Chat Service",
            "week": "Weeks 5-6",
            "rationale": "Chat Service microservice will implement proper timeout handling for SSE streams with configurable limits.",
            "workaround": "Not critical for Phase 0 single-user dev environment.",
        },
        31: {
            "service": "Chat Service",
            "week": "Weeks 5-6",
            "rationale": "Event transformation will be redesigned in Chat Service microservice. May implement new event pipeline architecture.",
            "workaround": "Current implementation works, will be refactored.",
        },
        99: {
            "service": "State Service + Agent Service",
            "week": "Weeks 3-4",
            "rationale": "Agent Service microservice will have new initialization pattern with dependency injection. State Service provides checkpointer.",
            "workaround": "Errors caught at FastAPI level, manageable for MVP.",
        },
        113: {
            "service": "Agent Service",
            "week": "Weeks 7-8",
            "rationale": "Agent Service will implement incremental synthesis to avoid 45s timeout. Complex architectural change better done during service split.",
            "workaround": "Users can limit parallel tools by rephrasing queries.",
        },
    }

    # TRACKED notes
    tracked_notes = {
        14: "Optional quality improvement - 89.89% coverage already exceeds 80% requirement.",
        21: "Code duplication exists but doesn't affect functionality. Backend models will remain in microservices architecture.",
        100: "Security feature validation. Worth adding but not blocking Phase 0.",
        101: "Would raise coverage from 85% to ~90%. Quality improvement, not blocking.",
        102: "Test reliability improvement. Current tests work, just need better assertions.",
        103: "Improves developer experience. Backend verification will be useful during migration.",
        104: "Code quality improvement for IDE support. Non-functional change.",
        105: "Documentation clarity. Update comment to reference Phase 1.",
        106: "CI/CD debugging improvement. Useful for migration testing.",
        112: "Security tooling fix. Manual reviews working, can defer to Phase 1.",
    }

    if category == "DEFERRED":
        note = deferred_notes.get(issue_num, {})
        return f"""
---

**🔄 MIGRATION STRATEGY: DEFERRED**

**Will Be Fixed In:** {note.get('service', 'TBD')} microservice
**Timeline:** {note.get('week', 'TBD')} of migration
**Rationale:** {note.get('rationale', 'Will be refactored during microservices split.')}
**Workaround:** {note.get('workaround', 'Acceptable for Phase 0 MVP.')}

"""

    elif category == "OBSOLETE":
        return """
---

**🗑️ MARKED AS OBSOLETE**

**Obsoleted By:** frontend-v2/ complete UI redesign
**Rationale:** All frontend components will be rebuilt from scratch with new design system (Radix UI primitives + custom theme). This issue will not exist in the new implementation.
**Action:** Issue will be closed when starting frontend-v2/ development (Week 9 of migration).

"""

    elif category == "TRACKED":
        rationale = tracked_notes.get(issue_num, "Low-priority quality improvement.")
        return f"""
---

**📋 TRACKED (LOW PRIORITY)**

**Priority:** NON-BLOCKING
**Rationale:** {rationale}
**When to Fix:** When spare time available, not urgent for migration.

"""

    return ""


def main():
    # Read original file
    with open("GITHUB_ISSUES.md") as f:
        lines = f.readlines()

    # Start building new file
    new_content = [HEADER]

    # === DEFERRED SECTION ===
    for issue_num in DEFERRED_ISSUES:
        issue_content = extract_issue_content(lines, issue_num)
        if issue_content:
            new_content.append(issue_content)
            new_content.append(add_migration_note(issue_num, "DEFERRED"))
            new_content.append("\n")

    # === OBSOLETE SECTION REMOVED PER USER REQUEST ===
    # 47 frontend issues (35, 38-43, 52-82, 91-98, 107-111) are NOT included in the new file
    # Rationale: Complete UI redesign means these issues won't exist

    # === TRACKED SECTION ===
    new_content.append("\n\n## 📋 TRACKED ISSUES (10 Low-Priority Issues)\n\n")
    new_content.append(
        "**Strategy:** Fix when time permits - Non-blocking quality improvements.\n\n"
    )
    new_content.append(
        "**Rationale:** These are nice-to-have improvements that don't block migration or production deployment. Can be addressed incrementally after migration completes.\n\n"
    )
    new_content.append("**Priority:** All issues in this section are LOW priority.\n\n")
    new_content.append("---\n\n")

    for issue_num in TRACKED_ISSUES:
        issue_content = extract_issue_content(lines, issue_num)
        if issue_content:
            new_content.append(issue_content)
            new_content.append(add_migration_note(issue_num, "TRACKED"))
            new_content.append("\n")

    # Write new file
    with open("GITHUB_ISSUES.md", "w") as f:
        f.write("".join(new_content))

    print("✅ Successfully reorganized GITHUB_ISSUES.md")
    print(f"   - DEFERRED: {len(DEFERRED_ISSUES)} issues (in file)")
    print(f"   - OBSOLETE: {len(OBSOLETE_ISSUES)} issues (REMOVED from file)")
    print(f"   - TRACKED: {len(TRACKED_ISSUES)} issues (in file)")
    print(f"   - TOTAL IN FILE: {len(DEFERRED_ISSUES) + len(TRACKED_ISSUES)} issues")
    print(
        f"   - ORIGINAL TOTAL: {len(DEFERRED_ISSUES) + len(OBSOLETE_ISSUES) + len(TRACKED_ISSUES)} issues"
    )


if __name__ == "__main__":
    main()
