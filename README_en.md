# Diplomas exploratory analysis

Russian universities diploma analysis

## Install dependencies

Python: `3.9.7`

Packages: `python -m pip install -r requirements.txt`

## Fetch data

Compressed data:
* [GDrive](https://drive.google.com/drive/folders/1jHQWitJkqHN23rJa8OX3vpvJg_osRz13?usp=sharing)

### HSE

1. Parse data from [website](https://www.hse.ru/edu/vkr/?language=ru): `python get_diplomas_hse.py --output_path parsed_results/hse_data.json`

### ITMO

*Note: I couldn't find all diplomas compilation, only those who participated in __scientific diplomas competition__*

1. Download PDF [with diplomas descriptions](https://research.itmo.ru/ru/stat/48/nivkr.htm) and save them to the folder `itmo_nivkr/`
2. Extract texts from PDF (they are being saved to the folder `itmo_nivkr_txt/`): `python extract_texts_from_pdf.py --pdf_folder itmo_nivkr/ --output_folder itmo_nivkr_txt --n_workers 4`
3. Parse diplomas texts: `python get_diplomas_itmo.py --txts_folder itmo_nivkr_txt/ --output_path parsed_results/itmo_data.json`

## Analysis

[Notebook](analysis.ipynb) consists of those chapters:

1. Read the data
2. Data cleaning and field extraction
3. Plot of distributions (like diplomas count by educational programme or by level: bachelor or master)
4. Plot of distributions over time (like educational level by time)
5. Count of diplomas with DS or close topics mentions (ML, DS, AI)