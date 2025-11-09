"""Info commands for CheatCV."""

import click
from pathlib import Path
from ..core.cv_utils import get_image_info


@click.command()
@click.argument('image_path', type=click.Path(exists=True))
def info(image_path):
    """Display information about an image."""
    info_data = get_image_info(image_path)

    if info_data is None:
        click.echo(click.style(f"Error: Could not read image '{image_path}'", fg='red'))
        return

    click.echo(click.style("Image Information:", fg='green', bold=True))
    click.echo(f"  Path: {info_data['path']}")
    click.echo(f"  Dimensions: {info_data['width']}x{info_data['height']}")
    click.echo(f"  Channels: {info_data['channels']}")
    click.echo(f"  Data Type: {info_data['dtype']}")
    click.echo(f"  Size: {info_data['size_bytes']:,} bytes")


@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--extensions', '-e', default='jpg,jpeg,png,bmp', help='Comma-separated image extensions')
def list_images(directory, extensions):
    """List all images in a directory."""
    ext_list = [f".{ext.strip().lower()}" for ext in extensions.split(',')]
    path = Path(directory)

    images = []
    for ext in ext_list:
        images.extend(path.glob(f"*{ext}"))
        images.extend(path.glob(f"*{ext.upper()}"))

    if not images:
        click.echo(click.style(f"No images found in '{directory}'", fg='yellow'))
        return

    click.echo(click.style(f"Found {len(images)} image(s):", fg='green', bold=True))
    for img in sorted(images):
        click.echo(f"  - {img.name}")
