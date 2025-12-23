# Mirror Sync Bot

This bot automatically syncs all mirror repositories in an organization with their upstream sources.

## How It Works

1. **Daily Automated Sync**: A GitHub Actions workflow runs once a day (at 2 AM UTC)
2. **Repository Discovery**: The bot queries all repositories in the organization
3. **Mirror Identification**: Filters for repositories with custom property `repo-type` set to `"mirror"`
4. **Source Retrieval**: For each mirror, gets the `mirror-source` custom property (URL of the source repo)
5. **Sync Process**: Clones the source repository and pushes all updates to the mirror

## Setup

### Custom Properties

For each mirror repository, configure the following custom properties:

- **`repo-type`**: Set to `"mirror"`
- **`mirror-source`**: Set to the URL of the source repository (e.g., `https://github.com/original-org/original-repo`)

### Permissions

The workflow requires a GitHub token with write access to all mirror repositories in the organization. 

**Important**: The default `GITHUB_TOKEN` provided by GitHub Actions only has write access to the repository where the workflow runs. To push to other repositories in the organization, you must use a **Personal Access Token (PAT)** or **GitHub App** with the following permissions:

#### Option 1: Personal Access Token (Classic)
Create a PAT with these scopes:
- `repo` (Full control of private repositories)
- `read:org` (Read organization membership and custom properties)

#### Option 2: Fine-grained Personal Access Token
Create a fine-grained PAT with:
- Repository permissions: `Contents: Read and Write`, `Metadata: Read`
- Organization permissions: `Custom properties: Read`
- Grant access to all mirror repositories or the entire organization

#### Option 3: GitHub App (Recommended for organizations)
Create a GitHub App with:
- Repository permissions: `Contents: Read and Write`, `Metadata: Read`
- Organization permissions: `Custom properties: Read`
- Install the app on the organization with access to mirror repositories

**Setup**:
1. Create a PAT or GitHub App following one of the options above
2. Add it as a repository secret named `MIRROR_SYNC_TOKEN`
3. Update the workflow to use this token instead of `GITHUB_TOKEN`

### Manual Trigger

The workflow can be manually triggered from the Actions tab in GitHub:
1. Go to Actions → Sync Mirrors
2. Click "Run workflow"

## Files

- `sync_mirrors.py` - Main Python script that handles the sync logic
- `.github/workflows/sync-mirrors.yml` - GitHub Actions workflow configuration
- `requirements.txt` - Python dependencies

## How to Test

You can test the sync script locally:

```bash
export GITHUB_TOKEN="your-github-token"
export GITHUB_ORGANIZATION="your-org-name"
python sync_mirrors.py
```

## Troubleshooting

- Check the Actions tab for workflow run logs
- Ensure the GITHUB_TOKEN has sufficient permissions
- Verify custom properties are correctly set on mirror repositories
- Check that source repositories are accessible
