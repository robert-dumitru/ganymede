from telegram import Update
from nbconvert.exporters import PDFExporter, WebPDFExporter
from nbconvert.preprocessors import LatexPreprocessor
from zipfile import ZipFile
from tarfile import TarFile
from tempfile import TemporaryDirectory
from pathlib import Path
import logging


def search_for_notebook(path: Path) -> Path:

    def _search(path: Path) -> list[Path]:
        if path.is_dir():
            notebooks = []
            for file in path.iterdir():
                if file.suffix == ".ipynb":
                    notebooks.append(file)
                elif file.is_dir():
                    notebooks.append(_search(file))
            return notebooks
        elif path.suffix == ".ipynb":
            return [path]
        else:
            raise ValueError("Path must be a directory or a jupyter notebook")

    paths = _search(path)
    if len(paths) == 0:
        raise ValueError("No jupyter notebooks found")
    elif len(paths) == 1:
        return paths[0]
    else:
        raise ValueError("Multiple jupyter notebooks found")


async def convert(update: Update) -> None:
    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        file = await update.message.document.get_file()
        archive_path = temp_dir / update.message.document.file_name
        await file.download_to_drive(custom_path=archive_path)

        match archive_path.suffix:
            case ".ipynb":
                pass
            case ".zip":
                with ZipFile(archive_path, "r") as zip_file:
                    zip_file.extractall(temp_dir)
            case ".tar":
                with TarFile(archive_path, "r") as tar_file:
                    tar_file.extractall(temp_dir)
            case _:
                raise ValueError("File must be a .ipynb, .zip, or .tar")

        notebook_path = search_for_notebook(temp_dir)
        pdf_path = None
        for mode in ("latex", "webpdf"):
            try:
                pdf_path = nbconvert_wrapper(notebook_path, mode)
            except Exception as e:
                logging.warning(f"Conversion error in {mode} mode: {e}")
                pass
        if pdf_path:
            await update.message.reply_document(pdf_path)
        else:
            raise ValueError("Conversion failed")


def nbconvert_wrapper(notebook_path: Path, conversion_mode: str) -> Path:
    match conversion_mode:
        case "latex":
            exporter = PDFExporter()
            exporter.register_preprocessor(LatexPreprocessor())
            # exporter.template_file = "article.tplx"
        case "webpdf":
            exporter = WebPDFExporter()
        case _:
            raise ValueError("Invalid conversion mode")
    pdf_data, resources = exporter.from_filename(str(notebook_path))
    pdf_path = notebook_path.with_suffix(".pdf")
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(pdf_data)  # noqa
    return pdf_path
