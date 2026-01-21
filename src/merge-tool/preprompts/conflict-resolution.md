# Conflict Resolution Prompt

You are helping to resolve a merge conflict between the homerchy fork and the upstream omarchy repository.

## Context

- **Repository**: homerchy (fork of omarchy)
- **File**: `{{FILE_PATH}}`
- **Upstream**: basecamp/omarchy (master branch)
- **Goal**: Merge upstream changes while preserving homerchy-specific customizations

## Important Guidelines

1. **Preserve homerchy-specific changes**: Look for references to "homerchy", homeserver, or custom branding/functionality
2. **Accept upstream improvements**: Bug fixes, security updates, and general improvements should be incorporated
3. **Merge intelligently**: When both sides have valid changes, comsrc/bine them appropriately
4. **Maintain consistency**: Ensure the resolved file follows the same coding style and patterns

## Conflict Details

### File Path
```
{{FILE_PATH}}
```

### Conflict Content
```
{{CONFLICT_CONTENT}}
```

### Our Version (homerchy)
```
{{OURS_CONTENT}}
```

### Their Version (upstream omarchy)
```
{{THEIRS_CONTENT}}
```

### Base Version (common ancestor)
```
{{BASE_CONTENT}}
```

## Task

Resolve this conflict by:
1. Analyzing what changed in each version
2. Identifying homerchy-specific customizations that must be preserved
3. Incorporating upstream improvements
4. Producing a clean, conflict-free version

## Output Format

Provide the complete resolved file content, with all conflict markers removed. The output should be ready to use as-is.

---

**Note**: If youre using this in Cursor, you can provide the resolved content directly, and it will be applied to the file.