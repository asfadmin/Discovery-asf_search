---
name: Bug report
about: Create a report to help us improve
title: "[Bug]"
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Provide a minimal python snippet to reproduce the behavior.

\*Reminder: If authentication is required **do not** leave any sensitive credentials in the snippet. Use the `getpass` module https://docs.python.org/3/library/getpass.html

Example snippet:
``` python
import asf_search as asf
from getpass import getpass

granule_list= ['S1A_IW_GRDH_1SDV_20250922T162824_20250922T162849_061103_079DCA_9515']
response = asf.search(granule_list=granule_list)

session = asf.ASFSession()
session.auth_with_token(getpass('Earth Data Login Token'))

# The line below raises an error for some reason
response[0].download('./', session=session)
```

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Desktop (please complete the following information):**
 - OS: [e.g. Ubuntu 20.04]
 - Python Version [e.g. python3.11]
 - Pip Environment ['python3 -m pip freeze']

**Additional context**
Add any other context about the problem here.
