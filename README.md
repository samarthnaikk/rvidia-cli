
# rvidia-cli

A command-line interface (CLI) tool for shared computing, supporting local and cross-network modes. Phase 1 focuses on local mode for users on the same network.

## Features (Phase 1)
- Local mode: Register users and join a shared room
- See all users running the CLI on the same network
- First user becomes admin and can share selected data files
- Admin generates a Dockerfile including chosen files from `rvidia-data/data` and `app.py`
- Cross-network mode: Coming soon

## Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/samarthnaikk/rvidia-cli.git
cd rvidia-cli
pip install -r requirements.txt
```

## Usage

Run the CLI tool:

```bash
python app.py --mode local
```

### Local Mode Flow
1. Choose mode: local or cross-network (cross-network displays "coming soon")
2. Enter your username
3. Join the room and see all users present
4. First user is admin; admin selects which data files to share
5. Dockerfile is generated in `rvidia-data/Dockerfile` including selected files

## Example

```bash
python app.py --mode local
# Enter username when prompted
# If you are admin, select data files to share (e.g. 1,2)
# Dockerfile will be created in rvidia-data/
```

## License
[MIT](LICENSE)

---

> This CLI is a companion tool for [rvidia](https://github.com/samarthnaikk/rvidia1). For more information, visit the main project repository.
