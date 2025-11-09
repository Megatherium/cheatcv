# CheatCV

A CLI tool for quick computer vision operations using OpenCV and Click.

## Features

CheatCV provides a single entry point CLI with organized commands for:

- **Image Information**: Get details about images and list images in directories
- **Image Transformation**: Resize, convert color spaces, and detect edges
- **Object Detection**: Detect faces and other objects in images

## Installation

### From source (recommended for development)

1. Clone the repository:
```bash
git clone <repository-url>
cd cheatcv
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

### Using pip (after publishing)

```bash
pip install cheatcv
```

## Usage

CheatCV uses a hierarchical command structure with a single entry point:

```
cheatcv [OPTIONS] COMMAND [ARGS]...
```

### Available Command Groups

- `info` - Image information commands
- `transform` - Image transformation commands
- `detect` - Object detection commands

### Info Commands

#### Show image information
```bash
cheatcv info show <image_path>
```

Example:
```bash
cheatcv info show photo.jpg
```

#### List images in a directory
```bash
cheatcv info list <directory> [--extensions jpg,png,bmp]
```

Example:
```bash
cheatcv info list ./images --extensions jpg,png
```

### Transform Commands

#### Resize an image
```bash
cheatcv transform resize <input_path> <output_path> --width <w> --height <h>
```

Example:
```bash
cheatcv transform resize input.jpg output.jpg --width 800 --height 600
```

#### Convert color space
```bash
cheatcv transform convert <input_path> <output_path> --conversion <type>
```

Supported conversions:
- `bgr2gray` - Convert BGR to grayscale
- `gray2bgr` - Convert grayscale to BGR
- `bgr2hsv` - Convert BGR to HSV
- `hsv2bgr` - Convert HSV to BGR
- `bgr2rgb` - Convert BGR to RGB
- `rgb2bgr` - Convert RGB to BGR

Example:
```bash
cheatcv transform convert input.jpg output.jpg --conversion bgr2gray
```

#### Detect edges
```bash
cheatcv transform edges <input_path> <output_path> [--threshold1 100] [--threshold2 200]
```

Example:
```bash
cheatcv transform edges input.jpg edges.jpg --threshold1 50 --threshold2 150
```

### Detect Commands

#### Detect faces
```bash
cheatcv detect faces <input_path> [--output <path>] [--show-count]
```

Examples:
```bash
# Just count faces
cheatcv detect faces photo.jpg --show-count

# Save annotated image
cheatcv detect faces photo.jpg --output annotated.jpg

# Both
cheatcv detect faces photo.jpg --output annotated.jpg --show-count
```

## Project Structure

```
cheatcv/
├── cheatcv/
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Main CLI entry point (single entry point)
│   ├── commands/             # Command modules
│   │   ├── __init__.py
│   │   ├── detect.py         # Detection commands
│   │   ├── info.py           # Information commands
│   │   └── transform.py      # Transformation commands
│   └── core/                 # Core utilities
│       ├── __init__.py
│       └── cv_utils.py       # OpenCV utility functions
├── setup.py                  # Package installation configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── LICENSE                   # License file
└── .gitignore               # Git ignore patterns
```

## Architecture

CheatCV follows a **single entry point with commands** architecture using the Click library:

1. **Single Entry Point**: `cheatcv/cli.py` defines the main CLI group and organizes all commands
2. **Command Groups**: Commands are organized into logical groups (info, transform, detect)
3. **Command Modules**: Each command group has its own module in `cheatcv/commands/`
4. **Core Utilities**: Shared OpenCV functionality is in `cheatcv/core/cv_utils.py`
5. **Console Script**: The `setup.py` defines `cheatcv` as a console script entry point

This structure provides:
- Clear separation of concerns
- Easy extensibility (add new commands by creating new modules)
- Hierarchical command organization
- Single binary installation

## Development

### Adding New Commands

1. Create a new command module in `cheatcv/commands/` (e.g., `filters.py`)
2. Define commands using Click decorators
3. Import and register the commands in `cheatcv/cli.py`

Example:
```python
# In cheatcv/commands/filters.py
import click

@click.command()
@click.argument('input_path')
def blur(input_path):
    """Apply blur filter to an image."""
    # Implementation here
    pass

# In cheatcv/cli.py
from .commands import filters as filters_module

@cli.group()
def filters():
    """Image filtering commands."""
    pass

filters.add_command(filters_module.blur)
```

### Running Tests

```bash
# Install in development mode
pip install -e .

# Test the CLI
cheatcv --help
cheatcv info --help
cheatcv transform --help
```

## Virtual Environment Note

This project is designed to work with Python virtual environments. Always activate your virtual environment before using the CLI:

```bash
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows
```

## Requirements

- Python 3.8+
- OpenCV (opencv-python)
- Click
- NumPy

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
