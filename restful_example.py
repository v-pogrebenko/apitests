import os

import restful

# select directory.
fd = os.path.dirname(__file__)
# run tests (test #2 should fail).
restful.Test(
    os.path.join(fd, "data_example", "results"),
    os.path.join(fd, "data_example", "samples"),
    os.path.join(fd, "data_example", "tests"),
    os.path.join(fd, "data_example", "errors"),
).run()
