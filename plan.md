1. Replace `mergeable_state` with `mergeStateStatus` in `.github/workflows/auto-merge-jules.yml` using `replace_with_git_merge_diff`. The `gh pr view` command fails in CI (see error log in task instructions: `Unknown JSON field: "mergeable_state"`) because `mergeable_state` is not a valid field, but `mergeStateStatus` is.
2. Verify the changes using `run_in_bash_session` to grep for `mergeStateStatus` and ensure `mergeable_state` is completely removed from `.github/workflows/auto-merge-jules.yml`.
3. Use `run_in_bash_session` to run tests via `PYTHONPATH=. pytest tests/` to ensure no regressions.
4. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
5. Use `submit` to submit the fix.
