# Handling a reporting ticket (Freshdesk)

## 1. Read the WHOLE ticket
The Freshdesk API's `GET /api/v2/tickets/<id>?include=conversations` returns **only the first 10** conversations. Long tickets hide the latest message, which is usually the real ask or an escalation.
```bash
# loop pages until a page returns < per_page items
GET /api/v2/tickets/<id>/conversations?page=1&per_page=30
GET /api/v2/tickets/<id>/conversations?page=2&per_page=30 ...
```
- Open **every attachment** (xlsx order sheets, screenshots, CSV exports). The requirement often lives there, not in the body. Attachment URLs are pre-signed, so fetch them without an auth header.
- **Personal data in attachments** (beneficiary lists, ID cards, screenshots with names or phone numbers): do **not** pass them to the AI. Ask the client for a de-identified version (counts, IDs only), or run a local script that outputs counts. Ask the client to remove ID documents from the ticket.
- Read private notes too. A colleague may already have done half the work.

## 2. Reproduce before fixing
- Open the exact report link the client used. Test as a restricted user if RLS or permissions could be involved (admins see everything).
- "It doesn't load / download" has **two** common causes: no access (permissions) or a timeout (>60s Superset). Check both. Fixing one can leave the other.

## 3. Decide: is there a problem at all?
Many tickets are definition gaps or data-entry issues (see `count-mismatch.md`). Prove it with numbers and explain. Don't change the report to fit a mistaken expectation.

## 4. Fix → verify → reply
- Fix in place (`skills/*`), back up first, and prove it with `skills/report-qa`.
- Reply with `templates/client-reply.md`: what was wrong, what changed, how it was verified, and the link to retest. Claim nothing you didn't verify.
- If a fix needs something you can't do (prod DDL, ETL change), say who owns it. Don't escalate a hypothesis: prove it first. (One escalation for a "missing index" turned out unnecessary. Deleting a dead CTE fixed it.)

## 5. Learn
`python3 tools/add_learning.py …` for anything new (see `skills/report-learnings`).
