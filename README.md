
# Remote Check-in

Remote check-in is a self-hosted to handle the check-in for a B&B remotely. 

Setting up your structures (B&Bs) and relative rooms, you can add a reservation and ask clients to fill in mandatory informations and upload documents and selfie. 




## Documentation

[Documentation](https://tbd)


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DATABASE_IP`

`DATABASE_PORT`

`DATABASE_USERNAME`

`DATABASE_PASSWORD`
## Contributing

Contributions are always welcome!

See `contributing.md` for ways to get started.

Please adhere to this project's `code of conduct`.


## Run Locally

Clone the project

```bash
  git clone https://github.com/mrgionsi/remote-checkin.git
```

Go to the project directory

```bash
  cd remote-checkin/frontend
  npm install remote-checkin
  npm start
```
```bash
  cd remote-checkin/backend
  pip install -r requirements.txt
  python main.py
```


## Running Tests

To run tests, run the following command

```bash
  npm run test
```


## Usage/Examples

```javascript
import Component from 'my-project'

function App() {
  return <Component />
}
```


## Add Pre-commit hooks
1. Install Pre-Commit
```bash
pip install pre-commit
```

2. Create the Validation Script
Save the following as .git/hooks/commit-msg-check.py and make it executable:
```python
#!/usr/bin/env python3
import sys
import re

# Allowed commit types
ALLOWED_TYPES = {"feat", "fix", "perf", "refactor", "style", "test", "build", "ops", "docs", "merge"}

# Commit message pattern
COMMIT_REGEX = re.compile(rf"^({'|'.join(ALLOWED_TYPES)})(\(.+\))?: .+")

# Read the commit message
commit_msg_file = sys.argv[1]
with open(commit_msg_file, "r") as file:
    commit_msg = file.readline().strip()

if not COMMIT_REGEX.match(commit_msg):
    print(f"❌ ERROR: Invalid commit message format.\n")
    print("✅ Allowed format: `<type>(<scope>): <description>`")
    print(f"✅ Allowed types: {', '.join(ALLOWED_TYPES)}")
    print("💡 Example: `feat(ui): add dark mode toggle`")
    sys.exit(1)

sys.exit(0)

```

4. Make the Script Executable
Run:
```bash
chmod +x .git/hooks/commit-msg-check.py
```

5. Install the Hook
Run:
```bash
pre-commit install --hook-type commit-msg
```