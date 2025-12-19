# JIRA Smart Commits Reference

This document provides detailed guidance on using JIRA Smart Commits for the Deep Agent One project.

## Overview

JIRA Smart Commits automatically link commits to issues and can trigger workflow transitions when issue keys are detected in commit messages.

**Relationship to Repository Conventions:** Smart Commits automation (`#resolve`, `#comment`) coexists with repository-level commit conventions. The `Resolves: DA1-XXX` format remains valid for GitHub/GitLab linking but does not trigger JIRA automation.

## Key Placement

- Issue key (e.g., `DA1-123`) should appear in subject line for visibility
- JIRA auto-links commits when issue key is detected anywhere in message

## Smart Commits Commands

Each command must be on its own line:

| Command | Description | Example |
|---------|-------------|---------|
| `#comment <text>` | Add a comment to the JIRA issue | `#comment Fixed the bug` |
| `#resolve` | Transition issue to resolved/done status | `#resolve` |
| `#time <duration>` | Log work time | `#time 2h 30m` |
| `#<transition>` | Trigger specific workflow transition | `#in-progress`, `#done` |

**Note:** Transition names are generally case-insensitive, but behavior may vary by JIRA instance. Query your project's workflow for valid transition names.

## Requirements

- Smart Commits must be enabled in JIRA (Admin → DVCS accounts → Enable Smart Commits)
- Repository must be connected via DVCS or GitHub/Bitbucket app link
- **Git committer email must exactly match a JIRA user email** (most common failure cause)

### Verify Email Matching

```bash
# Check your Git email
git config user.email

# Must match your JIRA account email exactly (case-insensitive)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Commands ignored silently | Email mismatch | Verify `git config user.email` matches JIRA email |
| `#resolve` doesn't work | Wrong transition name | Check project workflow for exact transition names |
| No JIRA link created | Smart Commits disabled | Admin → DVCS accounts → Enable Smart Commits |
| Partial processing | Push timing | Commands process on push, not local commit |

**Note:** JIRA sends failure notifications to the committer email, but in rare cases failures are silent. Test with a dummy ticket before team rollout.

## Limitations

- Smart Commits only process the first 100 lines of a commit message
- Each command must be on its own line (cannot combine on same line)
- Blank lines between commands are allowed and recommended for readability
- Commands are processed once when pushed to remote (not on local commit)
- Time format: `#time 1w 2d 4h 30m` (weeks, days, hours, minutes)

## Commit Template

```bash
fix(scope): DA1-XXX brief description

Detailed explanation of the change.

#comment Implemented the fix as described in the ticket.
#resolve

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

## Example Smart Commits

```bash
# Simple issue reference (auto-links to JIRA)
git commit -m "feat(api): DA1-123 add user authentication endpoint"

# With comment and resolve (using heredoc for multi-line - recommended)
git commit -m "$(cat <<'EOF'
fix(parser): DA1-456 handle null values

Fixed null pointer exception in JSON parser.

#comment Fixed null pointer in parser module
#resolve
EOF
)"

# With time logging
git commit -m "$(cat <<'EOF'
refactor(db): DA1-789 optimize query performance

#time 2h 30m
#comment Refactored slow queries
EOF
)"
```

**Note:** The heredoc format `$(cat <<'EOF' ... EOF)` is more portable and clearer for multi-line commit messages than embedding literal newlines in `-m` strings.

## Migration from Old Format

The `Resolves: DA1-XXX` format (GitHub/GitLab convention) does not trigger JIRA Smart Commits automation but remains valid for repository-level linking.

| Format | JIRA Automation | Repository Linking |
|--------|-----------------|-------------------|
| `#resolve` with issue key in subject | ✅ Yes | ✅ Yes |
| `Resolves: DA1-123` in body | ❌ No | ✅ Yes (GitHub/GitLab) |

**Recommendation:** Use Smart Commits syntax for JIRA automation while maintaining issue keys in commit messages for traceability.
