# Phase 13: Human review pause and resume

When the critic marks a result for review, the graph now stops at
`human_review` with session status `review`. The workflow can be resumed with:

```powershell
Invoke-RestMethod "http://localhost:8000/api/sessions/$id/review" `
  -Method Post -ContentType "application/json" `
  -Body '{"approved":true,"comment":"Approved by finance"}'
```

Rejecting a review marks the session `failed`. Approving it runs the composer
and marks the session `completed`. Durable deployments checkpoint the paused
state before the review decision is made.
