import subprocess
import logging
import os


def latex_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using latex.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    root_path: str = os.environ["ROOT_PATH"]
    completed_process: subprocess.CompletedProcess = subprocess.run(
        ["jupyter", "nbconvert", "--to", "pdf", ipynb_path],
        cwd=root_path + workdir + "/",
        timeout=60,
    )
    logging.debug(f"Completed process: {completed_process}")
    if completed_process.returncode != 0:
        logging.error(
            f"Error converting {ipynb_path} to pdf: {completed_process.stdout}"
        )
        raise Exception()
    pdf_path: str = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path


def chromium_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using chromium and pyppeteer.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    root_path: str = os.environ["ROOT_PATH"]
    completed_process: subprocess.CompletedProcess = subprocess.run(
        ["jupyter", "nbconvert", ipynb_path, "--to", "webpdf", "--disable-chromium-sandbox"],
        cwd=root_path + workdir + "/",
        timeout=60,
    )
    logging.debug(f"Completed process: {completed_process}")
    if completed_process.returncode != 0:
        logging.error(
            f"Error converting {ipynb_path} to pdf: {completed_process.stdout}"
        )
        raise Exception()
    pdf_path: str = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path
