"""Render each exam version and its answer key to PDF with Quarto."""
from subprocess import run, CalledProcessError
import os
import shutil

# Fixed PDF timestamps (2025-01-01) so that rendering the same version twice
# gives byte-identical PDFs (honoured by TeX Live / TinyTeX). An existing
# SOURCE_DATE_EPOCH in the environment takes precedence.
_REPRODUCIBLE_ENV = {'SOURCE_DATE_EPOCH': '1735689600', 'FORCE_SOURCE_DATE': '1'}


def _render(qmd_file: str, output_name: str, sujet: int) -> None:
    """Render one template for one version number."""
    env = {**_REPRODUCIBLE_ENV, **os.environ}
    run([
        'quarto', 'render', qmd_file, '--to', 'pdf', '--output', output_name,
        # The version number is passed to the template as a Quarto parameter.
        '-P', f'sujet:{sujet}',
        # Fresh kernel for every render: never reuse modules from a previous one.
        '--no-execute-daemon',
    ], check=True, env=env)


def render_qmd_files(sujet_file: str, corrige_file: str, n_copies: int, first_copy: int = 1,
                     output_dir: str = 'generated_files',
                     sujet_name: str = 'pec-cc-sujet-{n}.pdf',
                     corrige_name: str = 'pec-cc-corr-{n}.pdf') -> None:
    """Render versions first_copy .. first_copy + n_copies - 1.

    For each version, render the student copy (``sujet_file``) and the answer
    key (``corrige_file``) and move both PDFs to ``output_dir``. ``{n}`` in
    the output names is replaced by the version number.
    """
    os.makedirs(output_dir, exist_ok=True)

    for count in range(first_copy, first_copy + n_copies):
        sujet_pdf = sujet_name.format(n=count)
        corrige_pdf = corrige_name.format(n=count)
        try:
            _render(sujet_file, sujet_pdf, count)
            _render(corrige_file, corrige_pdf, count)
            shutil.move(sujet_pdf, os.path.join(output_dir, sujet_pdf))
            shutil.move(corrige_pdf, os.path.join(output_dir, corrige_pdf))
        except CalledProcessError as e:
            print(f'Error occurred while exporting version {count}: {e}')
