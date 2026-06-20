# Daily Philosophy - TRMNL Private Plugin

A private plugin for your TRMNL e-ink display that delivers a fresh, AI-generated
philosophical question every morning at 6 AM local time. Questions range from
playfully lighthearted to profoundly deep - always intellectually engaging.

## How It Works

1. A GitHub Actions workflow fires at 6 AM (Brussels/CET) every day - no server needed.
2. It calls the Anthropic API (Claude) to generate a unique philosophical question with
   a category (e.g. Epistemology, Free Will, Aesthetics) and a depth rating.
3. The question is POSTed to your TRMNL via the private plugin Webhook API.
4. Your device wakes up and displays it.

## Prerequisites

- A TRMNL device and account (trmnl.com)
- A GitHub account (free tier is fine)
- An Anthropic API key (console.anthropic.com) - cost is a fraction of a cent/day

## Setup - Step by Step

### 1. Create the TRMNL Private Plugin

1. Log in to trmnl.com and go to Plugins -> Private Plugin -> Add New.
2. Name it "Daily Philosophy".
3. Set the Strategy to Webhook and click Save.
4. TRMNL generates a Webhook URL like:
   https://trmnl.com/api/custom_plugins/YOUR-UUID-HERE
5. Copy just the UUID at the end - you'll need it in Step 4.

### 2. Add the Markup Template

1. On your plugin's settings page, click Edit Markup.
2. Switch to the Full layout tab.
3. Paste the contents of plugin/full.liquid into the editor.
4. Click Save Markup.

You can also import the plugin via ZIP: zip the contents of the plugin/ folder
and use Plugins -> Private Plugin -> Import New on TRMNL.

### 3. Set Up the GitHub Repository

Create a new GitHub repository (or fork this one) and add these files,
preserving their paths:
  .github/workflows/daily_question.yml
  send_question.py

### 4. Add Repository Secrets

Go to Settings -> Secrets and variables -> Actions and add two Secrets:

  ANTHROPIC_API_KEY   - your key from console.anthropic.com
  TRMNL_WEBHOOK_UUID  - the UUID from your TRMNL Webhook URL (Step 1)

### 5. Enable Actions & Run a Test

1. Go to the Actions tab of your repo.
2. Select the "Daily Philosophical Question" workflow.
3. Click Run workflow -> Run workflow for a manual test.
4. Watch the logs - you should see Claude's question and a "Success!" line.
5. Check your TRMNL device or the plugin preview to confirm it arrived.

## Timezone & DST

The workflow schedules two cron jobs to cover Brussels time all year:

  0 4 * * *   ->  04:00 UTC  ->  06:00 CEST (Apr-Oct, UTC+2)
  0 5 * * *   ->  05:00 UTC  ->  06:00 CET  (Nov-Mar, UTC+1)

On DST transition days, both crons fire in the same local day. The Python
script guards against double-sending by checking the LAST_SENT_DATE
repository variable (written automatically after each successful run).

If you're in a different timezone, adjust the cron lines and use
crontab.guru to find the right UTC offset.

## Permissions Note (important)

The workflow needs `actions: write` permission on its GITHUB_TOKEN so the
final step can save the LAST_SENT_DATE repository variable via `gh variable
set`. This is already declared in the workflow YAML:

  permissions:
    contents: read
    actions: write

If your organization enforces read-only default tokens at the org level,
this declared permission in the workflow file should still override it for
this specific workflow. If it doesn't (some orgs lock this down completely),
go to Settings -> Actions -> General -> Workflow permissions on the repo and
select "Read and write permissions".

## Customisation

Change the AI model - in send_question.py:
  ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"   # cheapest & fast
  # swap to "claude-sonnet-4-6" for richer questions

Change the question style - edit SYSTEM_PROMPT in send_question.py.

Change the schedule - update the two cron lines in
.github/workflows/daily_question.yml.

## File Structure

.
├── .github/workflows/daily_question.yml   Scheduled GitHub Actions workflow
├── plugin/
│   ├── settings.yml                       TRMNL plugin metadata (ZIP import)
│   └── full.liquid                        Full-screen e-ink template
├── send_question.py                       Generates & sends the question
└── README.md

## Troubleshooting

Job fails only on the last step ("Save last-sent date")
  -> Almost always a permissions issue. See "Permissions Note" above.

Nothing appears on TRMNL after the workflow succeeds
  -> Check TRMNL_WEBHOOK_UUID is the UUID only (not the full URL), and that
     the plugin is in an active Playlist.

JSONDecodeError in the logs
  -> The script strips markdown fences automatically; if it persists, check
     the raw log output.

429 rate limit from TRMNL
  -> Enable Debug Logs on the plugin settings page if testing frequently.

Both crons fired on the same day
  -> Only possible on DST transition days; harmless, and self-corrects after
     the first successful run of the day.

## Cost Estimate

Using claude-haiku-4-5-20251001: roughly 260 tokens/day, well under
$0.003/month. GitHub Actions usage is well within the free 2,000
minutes/month tier.

## License

MIT - use, modify, and share freely.
