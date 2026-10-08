#!/usr/bin/env python3
"""Create a Windows source-installer ZIP from an already built source distribution."""
import argparse
from pathlib import Path
import tarfile
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sdist', type=Path)
    parser.add_argument('--output', type=Path, default=Path('dist/Pulse-Windows-preview.zip'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pulse-windows-package-') as directory:
        root = Path(directory)
        with tarfile.open(args.sdist) as archive:
            archive.extractall(root, filter='data')
        folders = list(root.iterdir())
        if len(folders) != 1 or not folders[0].is_dir():
            raise ValueError('Expected one project directory in the source distribution.')
        source = folders[0]
        for required in ['install-windows.cmd', 'tools/install_windows.py', 'assets/pulse.ico', 'pyproject.toml']:
            if not (source / required).is_file():
                raise ValueError(f'Missing installer file: {required}')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob('*')):
                if path.is_file():
                    archive.write(path, Path('Pulse-Windows') / path.relative_to(source))
    print(args.output)


if __name__ == '__main__':
    main()
