from asf_search.ASFSearchOptions import ASFSearchOptions

def run_test_ASFSearchOptions(**kwargs):
    test_info = kwargs["test_info"]
    exception = test_info["exception"] # Can be "None" for don't.
    if "expect_output" in test_info:
        expect_output = test_info["expect_output"]
        del test_info["expect_output"]
    else:
        expect_output = {}

    # Take out anything that isn't supposed to reach the options object:
    del test_info["title"]
    del test_info["exception"]

    try:
        options_obj = ASFSearchOptions(**test_info)
    except (KeyError, ValueError) as e:
        assert type(e).__name__ == exception, f"ERROR: Didn't expect exception {type(e).__name__} to occur."
        return
    else:
        assert exception == None, f"ERROR: Expected exception {exception}, but SearchOptions never threw."

    for key, val in expect_output.items():
        assert getattr(options_obj, key) == val, f"ERROR: options object param '{key}' should have value '{val}'. Got '{getattr(options_obj, key)}'."