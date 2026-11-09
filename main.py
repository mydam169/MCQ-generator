"""Render the exam versions configured in config.py."""
import config
from renderingCodes import render_qmd_files

render_qmd_files(
    config.question_file,
    config.answer_file,
    config.number_of_copies,
    config.premier_sujet,
    output_dir=config.output_dir,
    sujet_name=config.sujet_output_name,
    corrige_name=config.corrige_output_name,
)
