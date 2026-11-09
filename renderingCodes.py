from subprocess import run, CalledProcessError
import os
import shutil

def render_qmd_files(sujet_file, corrige_file, n_copies, first_copy=1):
    output_dir = 'generated_files'
    os.makedirs(output_dir, exist_ok=True)

    for count in range(first_copy, first_copy + n_copies):
        sujet_name = f'pec-cc-sujet-{count}.pdf'
        corrige_name = f'pec-cc-corr-{count}.pdf'
        try:
            # The version number is passed to the templates as a Quarto parameter.
            run([
                'quarto', 'render', sujet_file, '--to',
                'pdf', '--output', sujet_name, '-P', f'sujet:{count}', '--no-execute-daemon'
            ], check=True)
            run([
                'quarto', 'render', corrige_file, '--to',
                'pdf', '--output', corrige_name, '-P', f'sujet:{count}', '--no-execute-daemon'
            ], check=True)

            # move generated files to dedicated folder
            shutil.move(sujet_name, os.path.join(output_dir, sujet_name))
            shutil.move(corrige_name, os.path.join(output_dir, corrige_name))

        except CalledProcessError as e:
            print(f'Error occurred while exporting: {e}')

if __name__ == "__main__":
    render_qmd_files()
