"""Settings for main.py."""

# Number of exam versions to render, and the version number of the first one.
# Versions premier_sujet .. premier_sujet + number_of_copies - 1 are rendered.
number_of_copies = 2
premier_sujet = 1

# Quarto templates for the student copy and the answer key.
question_file = 'pec-cc.qmd'
answer_file = 'pec-cc-answers.qmd'

# Output folder and file names; {n} is replaced by the version number.
output_dir = 'generated_files'
sujet_output_name = 'pec-cc-sujet-{n}.pdf'
corrige_output_name = 'pec-cc-corr-{n}.pdf'
