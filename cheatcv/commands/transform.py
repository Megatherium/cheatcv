"""Transform commands for CheatCV."""

import click
from ..core.cv_utils import (
    load_image, save_image, resize_image,
    convert_colorspace, detect_edges
)


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--width', '-w', type=int, required=True, help='Target width')
@click.option('--height', '-h', type=int, required=True, help='Target height')
def resize(input_path, output_path, width, height):
    """Resize an image to specific dimensions."""
    img = load_image(input_path)
    if img is None:
        click.echo(click.style(f"Error: Could not read image '{input_path}'", fg='red'))
        return

    resized = resize_image(img, width, height)

    if save_image(resized, output_path):
        click.echo(click.style(f"Image resized to {width}x{height} and saved to '{output_path}'", fg='green'))
    else:
        click.echo(click.style(f"Error: Could not save image to '{output_path}'", fg='red'))


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--conversion', '-c',
              type=click.Choice(['bgr2gray', 'gray2bgr', 'bgr2hsv', 'hsv2bgr', 'bgr2rgb', 'rgb2bgr'], case_sensitive=False),
              required=True,
              help='Color space conversion type')
def convert(input_path, output_path, conversion):
    """Convert image between color spaces."""
    img = load_image(input_path)
    if img is None:
        click.echo(click.style(f"Error: Could not read image '{input_path}'", fg='red'))
        return

    converted = convert_colorspace(img, conversion)
    if converted is None:
        click.echo(click.style(f"Error: Invalid conversion '{conversion}'", fg='red'))
        return

    if save_image(converted, output_path):
        click.echo(click.style(f"Image converted ({conversion}) and saved to '{output_path}'", fg='green'))
    else:
        click.echo(click.style(f"Error: Could not save image to '{output_path}'", fg='red'))


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--threshold1', '-t1', type=int, default=100, help='First threshold for Canny edge detection')
@click.option('--threshold2', '-t2', type=int, default=200, help='Second threshold for Canny edge detection')
def edges(input_path, output_path, threshold1, threshold2):
    """Detect edges in an image using Canny edge detection."""
    img = load_image(input_path)
    if img is None:
        click.echo(click.style(f"Error: Could not read image '{input_path}'", fg='red'))
        return

    edge_img = detect_edges(img, threshold1, threshold2)

    if save_image(edge_img, output_path):
        click.echo(click.style(f"Edge detection completed and saved to '{output_path}'", fg='green'))
    else:
        click.echo(click.style(f"Error: Could not save image to '{output_path}'", fg='red'))
