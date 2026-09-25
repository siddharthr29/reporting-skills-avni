<p align="center"><img src="assets/avni-logo.png" alt="Avni" width="200"></p>

# Start here: build an Avni report with Claude

You don't need to know SQL. **Claude does the technical work. You explain, guide and check.**
This guide follows the session deck: https://siddharthr29.github.io/reporting-skills-avni/

---

## Words you'll hear

| Word | Means |
|---|---|
| **Metabase** | The website where Avni reports live |
| **Card** | One number, chart or table |
| **Dashboard** | A page with several cards |
| **Filter** | A dropdown to narrow things down (e.g. pick a village) |
| **Click-through** | Click a number to see the list behind it |
| **Read-only** | You can look at data but can't change it. Always the case here |
| **Data map** | A file listing every table and column for one NGO, so Claude doesn't guess |

Reports can be **up to ~1.5 hours behind** the Avni app. That's normal.

## Two rules, always
1. **Download the data map first** for every NGO you work on (the "Get ready" step). Claude reads that file instead of searching the live system, which is faster and cheaper. The tools refuse to run until it's done.
2. **Never share personal details with Claude.** Don't paste client Excel lists, beneficiary names, phone numbers or screenshots showing people's details. Claude never needs them: the tools hide names, phones, Aadhaar, dates of birth and addresses automatically, and every check uses counts. To see the real list, open the report in Metabase yourself.

---

## Get ready (once, ~10 minutes)
1. Get this folder and the **database access details** from your lead. Ask your admin for **your own Metabase API key**, and have your **Superset username and password** ready.
2. Open **Terminal** in this folder and run `./tools/setup.sh`. Enter **your own** Metabase API key and Superset login (they're hidden as you type). It checks each one works. Never use someone else's logins, and never paste passwords into Claude.
3. Type `claude`, then paste:
   > Set me up for reporting: open the read-only connection and download the data map for **&lt;org name&gt;**. Tell me in simple words when it's ready.

✓ Ready when Claude says **read-only** and **data map saved**.

If Claude gives you a line starting with `!`, copy and paste it. That's you approving the step.

---

## Step 1 · Explain
**Got a requirement sheet?** (Google Sheet, Excel or CSV. This is the usual case.)
> Read AGENTS.md. Here is the requirement sheet for **&lt;org&gt;**: **&lt;Google Sheet link or file path&gt;**. Read every tab and show me a table of each requirement marked buildable, needs clarification, or not in the data.

For a Google Sheet link, the sheet must be shared as **"Anyone with the link → Viewer"**. Otherwise download it (File → Download → Microsoft Excel) and give Claude the file.

**Just a message or ticket?**
> Read AGENTS.md. A client from **&lt;org&gt;** asked: "**&lt;paste their words&gt;**". Fill in the requirement form and ask me anything that's unclear before building.

Answer every question. **Don't know? Ask your lead or the client.** Don't guess.

## Step 2 · Find (nothing is created yet)
> Using the data map, find where **&lt;the things&gt;** are stored and explain it in simple words. Then show me the numbers (top 10) and the total. Don't create anything yet.

✓ The total is close to what the app or the client expects. If not, ask: *"The app shows X but you show Y. Why could that be?"*

## Step 3 · Build (plan first)
> Create this report in our practice folder: **&lt;the cards&gt;**, a **&lt;name&gt; dropdown filter**, and make the number **clickable to show the list**. Show me the plan first.

Read the plan, then say **"Yes, go ahead"**. Never change a client's live report without your lead.

## Step 4 · Check (open the link yourself)
- [ ] It opens within a few seconds
- [ ] The filter is a **dropdown**, and changing it changes the numbers
- [ ] Clicking a number shows a list with the **same count**
- [ ] The parts **add up** to the total
- [ ] No strange codes like `3f2a9c1e-…` in the list

> Run the checks on this report and tell me in simple words if anything is wrong.

Something off? Describe what you see: *"When I click 212, the list shows everyone."* Claude knows how that was fixed before.

## Step 5 · Deliver
> Write a short, friendly reply to the client: what we built, how to use the filter, and the link. Only mention what we checked.

Show it to your lead, then type **`/learn`** so the next person benefits from anything new.

---

## Stuck?
- Ask Claude: *"Which playbook covers this problem?"*
- Common problems and fixes: `playbooks/`
- Practise: `labs/`
