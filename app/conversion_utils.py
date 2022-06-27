import os
import subprocess


def latex_convert(ipynb_path: str, workdir: str = "/tmp") -> str:
    """
    Converts the ipynb file into a pdf using latex.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: directory to process and store pdf.

    Returns: path of pdf.
    """
    subprocess.run(["jupyter", "nbconvert", "--to", "pdf", f"{ipynb_path}"], cwd=f"{workdir}/")
    pdf_path = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path


def chromium_convert(ipynb_path: str, workdir: str = "/tmp") -> str:
    """
    Converts the ipynb file into a pdf using chromium and pyppeteer.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: directory to process and store pdf.

    Returns: path of pdf.

    """
    raise NotImplementedError
