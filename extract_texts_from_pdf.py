from argparse import ArgumentParser
from itertools import repeat
import os

from pdfminer.high_level import extract_text
from tqdm.contrib.concurrent import process_map


def handle_pdf(pdf_name: str, pdf_folder: str, output_folder: str):
    text = extract_text(os.path.join(pdf_folder, pdf_name))
    with open(os.path.join(output_folder, f"{pdf_name}.txt"), "w+") as f:
        f.write(text)


def handle_pdf_single_arg(args):
    handle_pdf(*args)


def main(pdf_folder: str, output_folder: str, n_workers: int):
    os.makedirs(output_folder, exist_ok=True)
    
    pdf_names = list(filter(
        lambda filename: filename.endswith(".pdf"),
        os.listdir(pdf_folder)
    ))
    map_arguments = list(zip(
        pdf_names,
        repeat(pdf_folder, len(pdf_names)),
        repeat(output_folder, len(pdf_names))
    ))
    
    process_map(handle_pdf_single_arg, map_arguments, max_workers=n_workers)


if __name__ == "__main__":
    parser = ArgumentParser("PDF converter")
    parser.add_argument("--pdf_folder", type=str, required=True, help="path to folder with PDFs")
    parser.add_argument("--output_folder", type=str, required=True, help="path to output folder with TXTs")
    parser.add_argument("--n_workers", type=int, default=2, help="number of processes to run")
    args = parser.parse_args()

    main(args.pdf_folder, args.output_folder, args.n_workers)
