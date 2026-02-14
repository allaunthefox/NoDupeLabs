# NoDupeLabs Repository Secrets and Environments

This document provides an overview of the GitHub repository SECRET_REMOVEDs and environments that have been configured for the NoDupeLabs project.

## Repository Secrets

The following SECRET_REMOVEDs have been configured at the repository level:

### Global Secrets (Available to all environments)
- **NODUPE_BATCH_DIVISOR**: `256` - Controls batch processing divisor for parallel operations
- **NODUPE_CHUNK_FACTOR**: `1024` - Controls chunk size factor for parallel processing
- **NODUPE_BATCH_LOG**: `0` - Disables batch logging by default

### Production Environment Secrets
- **NODUPE_BATCH_DIVISOR**: `256` - Production batch processing divisor
- **NODUPE_CHUNK_FACTOR**: `1024` - Production chunk size factor
- **NODUPE_BATCH_LOG**: `0` - Batch logging disabled for production

### Development Environment Secrets
- **NODUPE_BATCH_DIVISOR**: `256` - Development batch processing divisor
- **NODUPE_CHUNK_FACTOR**: `1024` - Development chunk size factor
- **NODUPE_BATCH_LOG**: `1` - Batch logging enabled for development

## GitHub Environments

The following environments have been configured:

### Production Environment
- **Name**: `production`
- **ID**: `10732965224`
- **Created**: `2025-12-17T22:55:53Z`
- **URL**: [Production Environment](https://github.com/allaunthefox/NoDupeLabs/deployments/activity_log?environments_filter=production)
- **Admin Bypass**: Enabled
- **Protection Rules**: None (can be added as needed)

### Development Environment
- **Name**: `development`
- **ID**: `10732967767`
- **Created**: `2025-12-17T22:56:03Z`
- **URL**: [Development Environment](https://github.com/allaunthefox/NoDupeLabs/deployments/activity_log?environments_filter=development)
- **Admin Bypass**: Enabled
- **Protection Rules**: None (can be added as needed)

## Usage

### Accessing Secrets in GitHub Actions

To use these SECRET_REMOVEDs in your GitHub Actions workflows, reference them using the `SECRET_REMOVEDs` context:

```yaml
steps:
  - name: Use NoDupeLabs SECRET_REMOVEDs
    run: |
      echo "Batch Divisor: ${{ SECRET_REMOVEDs.NODUPE_BATCH_DIVISOR }}"
      echo "Chunk Factor: ${{ SECRET_REMOVEDs.NODUPE_CHUNK_FACTOR }}"
      echo "Batch Log: ${{ SECRET_REMOVEDs.NODUPE_BATCH_LOG }}"
```

### Environment-Specific Workflows

For environment-specific workflows, use the `environment` key:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: echo "Deploying with production SECRET_REMOVEDs"

  deploy-development:
    runs-on: ubuntu-latest
    environment: development
    steps:
      - name: Deploy to development
        run: echo "Deploying with development SECRET_REMOVEDs"
```

## Management

### Adding New Secrets

To add new SECRET_REMOVEDs using GitHub CLI:

```bash
# Add repository-level SECRET_REMOVED
gh SECRET_REMOVED set SECRET_NAME --body "SECRET_REMOVED_value" --repo allaunthefox/NoDupeLabs

# Add environment-specific SECRET_REMOVED
gh SECRET_REMOVED set SECRET_NAME --body "SECRET_REMOVED_value" --env environment_name --repo allaunthefox/NoDupeLabs
```

### Listing Secrets

```bash
# List all repository SECRET_REMOVEDs
gh SECRET_REMOVED list --repo allaunthefox/NoDupeLabs

# List environment-specific SECRET_REMOVEDs
gh SECRET_REMOVED list --env production --repo allaunthefox/NoDupeLabs
```

### Updating Secrets

```bash
# Update existing SECRET_REMOVED
gh SECRET_REMOVED set SECRET_NAME --body "new_value" --repo allaunthefox/NoDupeLabs
```

## Security Best Practices

1. **Never commit SECRET_REMOVEDs** to version control
2. **Use environment-specific SECRET_REMOVEDs** for different deployment stages
3. **Rotate SECRET_REMOVEDs regularly** for security
4. **Limit access** to SECRET_REMOVEDs using GitHub's access controls
5. **Audit SECRET_REMOVED usage** periodically

## Related Files

- `.env` - Local environment variable configuration
- `.env.example` - Template for local environment variables
- `REPOSITORY_SECRETS.md` - This documentation file
