Purpose:
Why is this pull request necessary? Provide a reference to a related issue in this repository that your pull request addresses (if applicable).

Description:
A description of the changes proposed in the pull request.

Snippet:
If the pull request provides a new feature, provide an example demonstrating the use-case(s) for this pull request (If applicable).

``` python
import asf_search as asf

response = asf.search(dataset=asf.DATASET.SENTINEL1, maxResults=250)

useful_data = response.new_feature()
```

Test Cases:
Please provide test cases for any new lines of code added via our testing suite

(Please target the `master` branch when opening a pull request)