"""Detection commands for CheatCV."""

import click
from ..core.cv_utils import (
    load_image, save_image, detect_faces, draw_rectangles
)


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output path to save annotated image')
@click.option('--show-count', '-c', is_flag=True, help='Show count of detected faces')
def faces(input_path, output, show_count):
    """Detect faces in an image using Haar Cascade."""
    img = load_image(input_path)
    if img is None:
        click.echo(click.style(f"Error: Could not read image '{input_path}'", fg='red'))
        return

    detected_faces = detect_faces(img)

    if show_count or not output:
        count = len(detected_faces)
        if count == 0:
            click.echo(click.style("No faces detected", fg='yellow'))
        else:
            click.echo(click.style(f"Detected {count} face(s)", fg='green'))
            for i, (x, y, w, h) in enumerate(detected_faces, 1):
                click.echo(f"  Face {i}: position=({x}, {y}), size={w}x{h}")

    if output:
        if len(detected_faces) > 0:
            annotated = draw_rectangles(img, detected_faces)
            if save_image(annotated, output):
                click.echo(click.style(f"Annotated image saved to '{output}'", fg='green'))
            else:
                click.echo(click.style(f"Error: Could not save image to '{output}'", fg='red'))
        else:
            click.echo(click.style("No output saved (no faces detected)", fg='yellow'))
