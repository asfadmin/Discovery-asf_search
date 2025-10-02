# Merge Requirements:
The following requirements must be met for your pull request to be considered for review & merging. Until these requirements are met please mark the pull request as a draft.

## Purpose
Why is this pull request necessary? Provide a reference to a related issue in this repository that your pull request addresses (if applicable).

## Description
A brief description of the changes proposed in the pull request. If there are any changes to packaging requirements please list them.

## Snippet
If the pull request provides a new feature, provide an example demonstrating the use-case(s) for this pull request (If applicable).

Example:
``` python
import asf_search as asf

response = asf.search(dataset=asf.DATASET.SENTINEL1, maxResults=250)

useful_data = response.new_feature()
```

## Error/Warning/Regression Free
Your code runs without any unhandled errors, warnings, or regressions

## Unit Tests
You have added unit tests to the test suite see the [README Testing section](https://github.com/asfadmin/Discovery-asf_search?tab=readme-ov-file#testing) for an overview on adding tests to the test suite.

## Target Merge Branch
Your pull request targets the `master` branch


***

### Checklist
- [ ] Purpose
- [ ] Description
- [ ] Snippet
- [ ] Error/Warning/Regression Free
- [ ] Unit Tests
- [ ] Target Merge Branch