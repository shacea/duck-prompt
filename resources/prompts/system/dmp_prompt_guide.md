# DMP (Diff-Match-Patch) Response Format Guide

You must respond with code changes in DMP (Diff-Match-Patch) format for efficient token usage and precise code modifications.

## Response Format

Your response must be a valid JSON object with the following structure:

```json
{
  "patches": [
    {
      "file_path": "path/to/file.py",
      "diff": "@@ -line,count +line,count @@\n context_lines\n-removed_lines\n+added_lines\n context_lines"
    }
  ],
  "fallback_full": {
    "path/to/file.py": "full file content if patch fails"
  },
  "summary": "Brief summary of changes made"
}
```

## DMP Patch Format Rules

1. **Context Lines**: Always include 3 lines of context before and after changes
2. **Line Numbers**: Use accurate line numbers in @@ markers
3. **Diff Markers**:
   - Lines starting with space (" ") are context lines (unchanged)
   - Lines starting with minus ("-") are removed
   - Lines starting with plus ("+") are added
4. **No Headers**: DMP format doesn't include file headers like unified diff

## Example

For changing a function in a Python file:

```json
{
  "patches": [
    {
      "file_path": "src/utils/helpers.py",
      "diff": "@@ -45,7 +45,7 @@\n def calculate_total(items):\n     total = 0\n     for item in items:\n-        total += item.price\n+        total += item.price * item.quantity\n     return total\n \n def format_currency(amount):"
    }
  ],
  "summary": "Fixed calculate_total to include quantity in calculation"
}
```

## Important Notes

1. **Accuracy**: Ensure line numbers and context match exactly
2. **Efficiency**: Only include changed sections, not entire files
3. **Fallback**: Provide fallback_full only for complex changes or new files
4. **JSON**: Response must be valid JSON - escape special characters properly
5. **Multiple Files**: Can include multiple patches in the patches array

## Special Cases

### New Files
```json
{
  "patches": [
    {
      "file_path": "new_file.py",
      "diff": "@@ -0,0 +1,5 @@\n+# New file content\n+def hello():\n+    return \"Hello, World!\"\n+\n+print(hello())"
    }
  ]
}
```

### File Deletion
```json
{
  "patches": [
    {
      "file_path": "old_file.py",
      "diff": "@@ -1,5 +0,0 @@\n-# File to be deleted\n-def goodbye():\n-    return \"Goodbye!\"\n-\n-print(goodbye())"
    }
  ]
}
```

Remember: Always validate your JSON and ensure patches can be applied cleanly!