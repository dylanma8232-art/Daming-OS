gh pr view "$PR_NUMBER" -R "$REPO" --json state,mergeable,mergeStateStatus -q '[.state, .mergeable, .mergeStateStatus] | @tsv'
