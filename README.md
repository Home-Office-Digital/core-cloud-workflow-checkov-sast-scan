# core-cloud-workflow-checkov-sast-scan

## Overview
This repository contains reusable Github Actions workflow files.

# Checkov

## Overview
This is a reusable workflow for SAST scanning source code and artifacts. This is a mandatory requirement for all Core Cloud repositories. If you require implementation assistance or have any additional questions, please reach out to the maintainer's team.

There are 2 Checkov reusable workflow files that your workflow can use. NOTE: These are for informational purposes only.

1. [checkov-scan-base.yaml](https://github.com/Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/blob/main/.github/workflows/checkov-scan-base.yaml) - For scanning [compatible](https://spacelift.io/blog/what-is-checkov#what-is-checkov) source code at rest.
2. [checkov-scan-tfplan.yaml](https://github.com/Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/blob/main/.github/workflows/checkov-scan-tfplan.yaml) - To be used for scanning Terraform plan files and source code.
3. [checkov-scan-tfplan-only.yaml](https://github.com/Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/blob/main/.github/workflows/checkov-scan-tfplan-only.yaml) - To be used for scanning just the Terraform plan files.

## Implementation for source code 
The simplest config to use is:

     name: Checkov SAST Scan
     
     on:
       workflow_call:

     permissions:
       contents: read
       id-token: write
       actions: read
       security-events: write

     jobs:
       checkov-scan:
         uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/.github/workflows/checkov-scan-base.yaml@1.5.0

## Implementation for Terraform Plan files and source code.

Add the above config into the following directory in your repository `.github/workflow/checkov-scan-tfplan.yaml`, or build into your own workflow logic if more complex. For scanning Terraform Plan files as well, please use:

     name: "Checkov SAST Scan for Terraform .tfplan files as well as source code"
     
     on:
       workflow_dispatch:
       push:
         branches:
           - '*'
         paths:
           - ./**
       pull_request:
         branches:
           - main
         types:
           - opened
           - synchronize
         paths:
           - ./**
     
     permissions:
       contents: read
       id-token: write
       actions: read
       security-events: write
     
     jobs:
       sast-checkov-scan-plan:
         uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/.github/workflows/checkov-scan-tfplan.yaml@1.5.0
         with:
           # Optional inputs depending on code structure
           path: 'e.g. terraform/environment/sandbox-ops-tooling'
           env_name: 'e.g. sandbox-ops-tooling'
           plan_role: '<role with permissions for generating a plan>'
           TF_VAR_source-repo: ${{ inputs.TF_VAR_source-repo }}
         # Github secret containing the AWS Account ID.
         secrets:
           account_id: ${{ e.g secrets.corecloud_sandbox_ops_tooling_account_id }}

## Implementation for tfplan files only

     name: "Checkov SAST Scan for Terraform .tfplan files as well as source code"

     on:
       workflow_dispatch:
       push:
         branches:
           - '*'
         paths:
           - ./**
       pull_request:
         branches:
           - main
         types:
           - opened
           - synchronize
         paths:
           - ./**

     permissions:
       contents: read
       id-token: write
       actions: read
       security-events: write

     jobs:
       sast-checkov-scan-tfplan-files:
         uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/.github/workflows/checkov-scan-tfplan-only.yaml@1.14.0
         with:
           # Optional inputs depending on code structure
           plan_role: '<role with permissions for generating a plan>'
           path: 'e.g. terraform/environment/sandbox-ops-tooling'
           env_name: 'e.g. sandbox-ops-tooling'
           TF_VAR_source-repo: ${{ inputs.TF_VAR_source-repo }}
         # Github secret containing the AWS Account ID.
         secrets:
           account_id: ${{ secrets.ACCOUNT_ID }}

       sast-sonar-scan:
         uses: ./.github/workflows/sonarqube-scan.yaml
         secrets:
           sonar_token: ${{ secrets.sonar_token }}
           sonar_host_url: ${{ secrets.sonar_host_url }}

       terragrunt-standard-pipeline:
         # Should always be used to prevent state lock issues with checkov tfplan scan
         needs: [sast-checkov-scan-tfplan-files,sast-sonar-scan]
         uses: Home-Office-Digital/core-cloud-workflow-terragrunt-actions/.github/workflows/standard-pipeline.yml@main
         with:
           github-environment: 'e.g. sandbox-ops-tooling'
           # etc etc 

## Custom Policies

Core Cloud centrally manages custom policies within this repo. These can be found at [central-checkov-policies](https://github.com/Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/central-checkov-policies) and are run against all repos. If you wish to add additional custom policies after developing and testing these locally, please raise a PR and contact this maintainer's team who will carry out further testing before merging for general use. Checkov supports policies written in both YAML and Python.

## Composite Action

If you wish to just add a step to your existing workflow logic, you can use the composite action instead. Make sure these minimum permissions are added.

      permissions:
        contents: read
        id-token: write
        actions: read
        security-events: write
        
      jobs:
        example-job:
          runs-on: ubuntu-latest
          steps:  
            - name: Run Checkov Scan on the source code and existing plan files
              uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan@1.5.0
              with:
                path: '.'

## HIGH/CRITICAL exemptions
Exemptions for HIGH/CRITICAL Checkov findings can be applied by the Core Cloud team when approved and required. The following secrets are required in order to use exemptions and will be applied by the Core Cloud team:
- `EXEMPTIONS_APP_ID`
- `EXEMPTIONS_APP_PRIVATE_KEY`

These are declared under the same names whether you're calling a reusable workflow or the composite action directly — only the block they go under changes: `secrets:` for a workflow, `with:` for an action.

If you're calling one of the reusable workflows (`checkov-scan-base.yaml`, `checkov-scan-tfplan.yaml`, `checkov-scan-tfplan-only.yaml`):

      jobs:
        checkov-scan:
          uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan/.github/workflows/checkov-scan-base.yaml@1.5.0
          secrets:
            EXEMPTIONS_APP_ID: ${{ secrets.EXEMPTIONS_APP_ID }}
            EXEMPTIONS_APP_PRIVATE_KEY: ${{ secrets.EXEMPTIONS_APP_PRIVATE_KEY }}

If you're using the composite action directly:

      jobs:
        example-job:
          runs-on: ubuntu-latest
          steps:
            - name: Run Checkov Scan on the source code and existing plan files
              uses: Home-Office-Digital/core-cloud-workflow-checkov-sast-scan@1.5.0
              with:
                path: '.'
                EXEMPTIONS_APP_ID: ${{ secrets.EXEMPTIONS_APP_ID }}
                EXEMPTIONS_APP_PRIVATE_KEY: ${{ secrets.EXEMPTIONS_APP_PRIVATE_KEY }}

## Findings and severity levels
No PRs can be merged if there are any findings with a severity level of HIGH or CRITICAL. If there are any findings with a severity level of MEDIUM or LOW, these will be reported in the PR but will not block the merge. A full list of the findings can be found in the Github Security Dashboard or the `Listing findings and severity levels` step in the calling workflow's build.`
