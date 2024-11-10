import logging

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.backend.msword_backend import MsWordDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline


doc_converter = (
    DocumentConverter(  # all of the below is optional, has internal defaults.
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.PPTX,
            InputFormat.ASCIIDOC,
            InputFormat.MD,
        ],  # whitelist formats, non-matching files are ignored.
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend
            ),
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline, backend=MsWordDocumentBackend
            ),
        },
    )
)

from pathlib import Path


def parse_directory(path: Path | str, max_num_pages=5) -> dict[str, str]:
    contents = {}
    if isinstance(path, str):
        path = Path(path)
    for file in (x for x in path.rglob('*') if x.is_file() and not x.name.endswith('.content') and not x.name.endswith('.json')):
        cache_file = file.with_name(file.name + '.content')
        if not cache_file.exists():
            logging.info(f"Extracted content cache for file `{str(file)}` is not found, creating one...")
            try:
                content = doc_converter.convert(file, max_num_pages=max_num_pages, max_file_size=1024**2*100).document.export_to_markdown()
                cache_file.write_text(content)
                contents[str(file)] = content
            except StopIteration:
                logging.warning(f"Cannot parse file `{str(file)}`. Probably it is not supported yet.")
        else:
            contents[str(file)] = cache_file.read_text()
    return contents

if __name__ == '__main__':
    converted = parse_directory('..\\cvs')
    pass
