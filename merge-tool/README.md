# Merge Tool - Interactive Upstream Merge Workflow

This tool helps you merge changes from the parent omarchy repository (basecamp/omarchy) into homerchy, file-by-file, with interactive review and AI-assisted conflict resolution.

## Quick Start

```bash
cd merge-tool
./fetch-upstream.sh    # Fetch latest from upstream
./merge.sh             # Start interactive merge
```

## Overview

The merge tool provides a systematic way to:
1. Fetch latest changes from upstream omarchy
2. Review each changed file individually
3. Accept, reject, or skip changes
4. Resolve conflicts with AI assistance
5. Track progress and resume if interrupted

## Directory Structure

```
merge-tool/
├── merge.sh                    # Main interactive merge script
├── fetch-upstream.sh           # Fetch latest from parent repo
├── review-change.sh            # Review individual file changes
├── apply-change.sh             # Apply accepted changes
├── resolve-conflict.sh         # AI-assisted conflict resolution
├── state/                      # State tracking directory
│   └── merge-state.json       # JSON state for resuming
├── preprompts/
│   ├── conflict-resolution.md # Prompt for AI conflict resolution
│   └── change-review.md       # Prompt template for change review
└── README.md                   # This file
```

## Workflow

### 1. Fetch Upstream Changes

```bash
./fetch-upstream.sh
```

This script:
- Adds/updates the `upstream` remote pointing to `basecamp/omarchy`
- Fetches the latest `master` branch
- Identifies all files that differ between your branch and upstream
- Creates a state file (`state/merge-state.json`) tracking all changes

### 2. Start Interactive Merge

```bash
./merge.sh
```

The interactive merge will:
- Show each changed file one by one
- Display the diff between your version and upstream
- Present options: Accept, Reject, Skip, View Full Diff, Add Note
- For conflicts: Offer AI-assisted resolution or manual editing
- Track your decisions in the state file

### 3. Resolve Conflicts

When a conflict is detected, you have several options:

**Option A: AI-Assisted Resolution**
```bash
./resolve-conflict.sh <file_path>
```

This creates a preprompt file in `state/` that you can provide to an AI agent (like Cursor). The preprompt includes:
- Full context of the conflict
- Your version, their version, and base version
- Guidelines for preserving homerchy-specific changes

After the AI resolves it, apply the resolved file:
```bash
cat <resolved-file> > <file_path>
```

**Option B: Manual Resolution**
- The script will open your editor (`$EDITOR` or `nano` by default)
- Resolve the conflict markers manually
- Save and continue

### 4. Resume Interrupted Session

If you exit the merge process, you can resume later:
```bash
./merge.sh
```

The tool will automatically resume from the last file you were reviewing.

## State Management

The state file (`state/merge-state.json`) tracks:
- Upstream remote and branch information
- List of all changed files
- Status of each file (pending, accepted, rejected, skipped, conflict)
- Current position in the review process
- Statistics (total, accepted, rejected, skipped, conflicts)

You can inspect the state:
```bash
cat state/merge-state.json | jq
```

## Options During Review

For each file, you can:

- **Accept upstream**: Apply the upstream version (replaces your changes)
- **Keep ours**: Reject upstream changes (keep your version)
- **Skip for now**: Defer decision (file remains pending)
- **View full diff**: See complete diff in pager
- **Add note**: Add a note to the file entry for later reference

For conflicts, additional options:

- **Resolve with AI**: Generate preprompt for AI agent
- **Resolve manually**: Open in editor to resolve manually
- **Skip for now**: Defer conflict resolution
- **Keep ours**: Reject upstream version
- **Accept theirs**: Accept upstream version (may lose your changes)

## Preprompts

### Conflict Resolution

The `preprompts/conflict-resolution.md` template is designed for AI agents. It includes:
- Context about the merge workflow
- All three versions (ours, theirs, base)
- Guidelines for preserving homerchy-specific changes
- Instructions for output format

### Change Review

The `preprompts/change-review.md` template helps review non-conflicting changes:
- Questions to consider
- File context and diff
- Recommendation format

## Examples

### Example 1: Simple Merge

```bash
$ ./fetch-upstream.sh
Found 15 changed file(s)
State saved to state/merge-state.json

$ ./merge.sh
=== File 1 of 15: install/helpers/logging.sh ===
[shows diff]
Options:
  1) Accept upstream
  2) Keep ours
  3) Skip for now
Choice [1-5]: 1
Applied upstream version of install/helpers/logging.sh
```

### Example 2: Conflict Resolution

```bash
=== File 5 of 15: config/hypr/hyprland.conf ===
[shows diff]
⚠ CONFLICT DETECTED

Options:
  1) Resolve with AI
  2) Resolve manually
Choice [1-5]: 1

Conflict resolution preprompt created:
  state/conflict-prompt-config_hypr_hyprland.conf.md

[Provide preprompt to AI agent, get resolved file]
$ cat resolved-file > config/hypr/hyprland.conf
```

### Example 3: Resume Session

```bash
$ ./merge.sh
No pending files to review.

Summary:
  Accepted: 10
  Rejected: 2
  Skipped: 3
  Conflicts: 0
  Pending: 0
```

## Dependencies

- `bash` (4.0+)
- `git`
- `jq` (for JSON state management)
- `gum` (optional, for better interactive experience)

Install dependencies:
```bash
pacman -S jq gum
```

## Tips

1. **Review in batches**: You can skip files and come back to them later
2. **Use notes**: Add notes to files you're unsure about for later review
3. **Check git status**: After accepting changes, review with `git status` before committing
4. **Test after merge**: Always test your system after merging upstream changes
5. **Commit incrementally**: Consider committing in logical groups rather than one large commit

## Safety Features

- **No auto-commit**: Changes are staged but not committed automatically
- **Resumable**: Can pause and resume at any time
- **Auditable**: All decisions tracked in state file
- **Reversible**: Can review git status and unstage if needed

## Troubleshooting

### "State file not found"
Run `./fetch-upstream.sh` first to initialize the state.

### "jq not found"
Install with: `pacman -S jq`

### "gum not found"
Install with: `pacman -S gum` (optional but recommended)

### Want to start over
Delete `state/merge-state.json` and run `./fetch-upstream.sh` again.

### Files not showing up
Ensure you've fetched the latest: `git fetch upstream master`

## Integration with Cursor AI

The preprompts are designed to work with Cursor's AI agent:

1. When a conflict occurs, run `./resolve-conflict.sh <file>`
2. Open the generated preprompt file in Cursor
3. Ask Cursor to resolve the conflict using the preprompt
4. Apply the resolved content to the file
5. Continue with the merge

The preprompts include all necessary context and guidelines for the AI to make informed decisions.