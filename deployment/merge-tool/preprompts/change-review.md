# Change Review Prompt

You are reviewing a file change from the upstream omarchy repository to determine if it should be merged into homerchy.

## Context

- **Repository**: homerchy (fork of omarchy)
- **File**: `{{FILE_PATH}}`
- **Upstream**: basecamp/omarchy (master branch)
- **Goal**: Determine if this change affects homerchy-specific features or is safe to accept

## Review Questions

1. **Does this change affect homerchy-specific branding or references?**
   - Look for references to "omarchy" that should be "homerchy"
   - Check for branding, logos, or product names
   - Verify paths like `~/.local/share/omarchy` vs `~/.local/share/homerchy`

2. **Does this change conflict with homerchy customizations?**
   - Check if homerchy has modified this file in ways that conflict
   - Look for homerchy-specific features that might be affected

3. **Is this a beneficial upstream change?**
   - Bug fixes
   - Security updates
   - Performance improvements
   - New features that don't conflict

4. **Should this be accepted, rejected, or require manual review?**
   - **Accept**: Safe upstream improvement, no conflicts
   - **Reject**: Conflicts with homerchy-specific changes
   - **Review**: Needs manual inspection or partial merge

## File Change

### File Path
```
{{FILE_PATH}}
```

### Diff
```
{{DIFF_CONTENT}}
```

## Recommendation

Based on the analysis above, provide:
- **Action**: Accept / Reject / Review
- **Reasoning**: Brief explanation
- **Notes**: Any specific concerns or merge instructions