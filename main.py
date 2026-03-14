from subprocess import run, CalledProcessError
from config import *
from renderingCodes import render_qmd_files

render_qmd_files(question_file, answer_file, number_of_copies, premier_sujet)
