
# GitHub Pages Setup

## Steps to Enable GitHub Pages

1. **Set the target repository variable**
   - Go to: `Settings` → `Secrets and variables` → `Actions` → **Variables** tab
   - Click **"New repository variable"**
   - **Name**: `TARGET_REPOSITORY`
   - **Value**: `openwdl/learn-wdl` (or another repository in the format `owner/repo`)
   - Click **"Add variable"**

2. **Configure GitHub Pages**
   - Go to: `Settings` → `Pages`
   - In **"Source"**, select **"GitHub Actions"**
   - Save the settings

3. **Run the workflow**
   - Go to the **"Actions"** tab in the repository
   - Select the documentation workflow (e.g., **"Generate and Deploy Documentation"**)
   - Click **"Run workflow"**
   - Or simply push to the main branch to trigger automatically

4. **Access the documentation**
   - After the workflow finishes (may take a few minutes), the documentation will be available at:
   - `https://openwdl.github.io/learn-wdl/` (or your repository's GitHub Pages URL)

## Changing the Target Repository

To document a different repository:

1. Edit the `TARGET_REPOSITORY` variable in `Settings` → `Secrets and variables` → `Actions` → **Variables** tab
2. Change the value to the new repository (format: `owner/repo`, e.g., `openwdl/learn-wdl`)
3. Run the workflow again

## How the Workflow Works

The `docs.yml` workflow performs the following steps:

1. **Build Job:**
   - Checks out the documentation tool repository
   - Installs Python (e.g., 3.13)
   - Installs the documentation tool (e.g., wdl2docs)
   - Clones the repository defined in the `TARGET_REPOSITORY` variable
   - Generates HTML documentation
   - Uploads the files as an artifact

2. **Deploy Job:**
   - Publishes the generated files to GitHub Pages
   - Provides the documentation URL

## Workflow Triggers

The workflow runs automatically when:
- There is a push to the main branch
- It is run manually via the GitHub Actions interface

In both cases, it uses the repository defined in the `TARGET_REPOSITORY` variable.

## Target Repository Configuration

The workflow uses the `TARGET_REPOSITORY` variable configured in:
- `Settings` → `Secrets and variables` → `Actions` → **Variables**

**Behavior:**
- If the `TARGET_REPOSITORY` variable is set: uses the defined value
- If the variable does not exist: uses the default value

**Format**: `owner/repo` (public GitHub repository)

**Examples:**
- `openwdl/learn-wdl`
- `your-username/your-wdl-repo`

## Required Permissions

The workflow is already configured with the necessary permissions:
- `contents: read` - To read the repository code
- `pages: write` - To write to GitHub Pages
- `id-token: write` - For OIDC authentication

## Verification

To verify everything is working:

1. Go to **Actions** and confirm the workflow ran successfully
2. Go to **Settings** → **Pages** and check for a green link with the site URL
3. Click the URL or access `https://openwdl.github.io/learn-wdl/`

## Troubleshooting

If the workflow fails:

1. **Permissions error**: Check if Actions permissions are enabled in Settings → Actions → General
2. **Generation error**: Check the workflow logs for specific details

## Automatic Updates

On every push to the main branch, the workflow will:
1. Regenerate documentation for the repository defined in `TARGET_REPOSITORY`
2. Automatically update GitHub Pages

To generate documentation for another repository:
1. Change the `TARGET_REPOSITORY` variable in **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Run the workflow manually in **Actions** → **Run workflow**

Or simply run the workflow manually without changing the variable to regenerate documentation for the current repository.
