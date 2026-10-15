# Bathna Primary School — Public Student Directory

A premium responsive static site hosted by GitHub Pages. A GitHub Actions workflow reads a **private** Google Sheet with a read-only Google service account, exports only approved rows and allowlisted fields, then deploys a static site. Visitors never contact Google Sheets or Apps Script.

## IMPORTANT PRIVACY NOTICE

**The resulting website and its `data/students.json` file are PUBLIC.** GitHub Pages is public even when source is private on eligible paid plans. Publish children's names only if the school has documented authorization and any legally required guardian consent. The sample data is fictional. Do not place private identifiers, roll numbers, birthdays, photos, addresses, phone numbers, Aadhaar, marks or confidential notes in the public directory. `APPROVED=YES` must be assigned only after review. The approval column is not a substitute for consent or compliance.

## Quick setup (no command line)

### 1. Create the private Sheet
1. Create or open a Google Spreadsheet. Keep General access **Restricted**.
2. Create a worksheet exactly named `PUBLIC_STUDENTS`.
3. Enter these headers in row 1: `APPROVED | PUBLIC NAME | CLASS | SECTION` (or import the included CSV).
4. Add approved public information only. Set `APPROVED` to `YES` for rows cleared for publication; all others should be `NO`.
5. Copy the spreadsheet ID from the URL between `/d/` and `/edit`.

### 2. Create a service account (one-time Google Cloud setup)
1. Open https://console.cloud.google.com/ and select/create a project.
2. Enable **Google Sheets API** under APIs & Services → Library.
3. Open IAM & Admin → Service Accounts → Create service account (e.g. `bathna-directory-reader`). **Do not grant broad project roles.**
4. Open the service account → Keys → Add key → Create new key → JSON. Download the JSON privately. Your organization may prohibit creating keys; if so, ask your administrator about Workload Identity Federation instead. Never upload the JSON file to GitHub.
5. Copy the service account email (ends with `gserviceaccount.com`). Share **only the private spreadsheet** with that address as **Viewer**. Keep General access Restricted.

### 3. Create GitHub repository
1. Open https://github.com/new and create a **public** repository called `bathna-student-directory` (GitHub Free Pages works with public repositories).
2. Upload the extracted project's files and folders, including the hidden `.github/workflows/publish.yml` file. GitHub's browser upload supports folders when dragged in from a file manager; check the workflow file is present afterward. Never upload the downloaded service-account JSON.
3. Go to Settings → Secrets and variables → Actions → New repository secret.
4. Add secret `GOOGLE_SHEET_ID` with your spreadsheet ID.
5. Add secret `GOOGLE_SERVICE_ACCOUNT_JSON` with the **entire contents** of your downloaded JSON credentials file (not the filename).
6. Go to Settings → Pages → Build and deployment → Source → **GitHub Actions**.
7. Go to Actions → **Publish approved school directory** → Run workflow → Run workflow. Wait for the green checkmark. On the first run, if Pages has not been enabled, enable it and rerun.
8. Your site will be at `https://YOUR-GITHUB-USERNAME.github.io/bathna-student-directory/`.

### 4. Embed in Google Sites
Open the Google Site editor → Insert → Embed → By URL → paste the published GitHub Pages URL → Insert → resize the frame → Publish. If embedding is blocked by browser/site policy, link to the portal instead.

### 5. Update students
Edit the private Google Sheet. The workflow runs approximately every 2 hours (GitHub scheduled jobs can be delayed or skipped under load). To update immediately, GitHub → Actions → Publish approved school directory → Run workflow. No site edits required.

## How it protects the private spreadsheet
- The service account can only read the shared sheet (Viewer), using read-only Sheets API scope.
- Credentials and sheet ID are stored in GitHub Actions secrets, never in website JavaScript or public files.
- The exporter reads only the `PUBLIC_STUDENTS` worksheet, publishes only rows marked `YES`, and outputs only `name`, `class`, `section`.
- If an export fails, deployment stops; it does not publish a partially generated site.
- The output is intentionally PUBLIC. Anyone can download `data/students.json`.
- Revoking a student's approval removes them from the next successful deployment, but does not erase copies, caches or previously downloaded data. Consider whether publishing names is appropriate at all.

## Troubleshooting
- `KeyError GOOGLE_SERVICE_ACCOUNT_JSON`: GitHub Actions secret is missing.
- `SpreadsheetNotFound`: wrong sheet ID or sheet not shared with the service account email.
- `WorksheetNotFound`: name must be exactly `PUBLIC_STUDENTS`.
- `No approved records`: set at least one reviewed row to `YES`; for intentional emptying, workflow can be modified to pass `ALLOW_EMPTY_EXPORT=true`.
- Workflow is green but site missing: check Settings → Pages → Source is GitHub Actions, and wait for deployment propagation.
- Changes not visible: trigger the workflow manually; then use the site's Refresh button.
- Scheduled runs are best effort, not instantaneous.

## Files
- `site/index.html`: interface
- `site/styles.css`: premium styling and three-column cards
- `site/app.js`: client-side search, class filter, pagination and reload
- `site/data/students.json`: placeholder replaced in Actions before publishing
- `scripts/export_students.py`: read-only allowlisted export
- `.github/workflows/publish.yml`: scheduled/manual GitHub Pages deployment
- `PUBLIC_STUDENTS_template.csv`: starter worksheet

## Local preview
Opening `site/index.html` directly as a `file://` URL may block JSON fetch. Preview via a local HTTP server if desired; the hosted GitHub Pages site works without a local build step.
