# playwright-tests

## Running the tests

```bash
# install dependencies
pip install -r requirements.txt
playwright install

# set environment variables
export OPHUB_URL=https://ophub.example.com
export OPHUB_USERNAME=your_username
export OPHUB_PASSWORD=your_password
export OPHUB_IGNORE_HTTPS_ERRORS=1

# run tests
pytest
```
