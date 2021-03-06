# Diplomas exploratory analysis

Анализ ВКР российских вузов

[English README version](README_en.md) 🇬🇧

## Установка зависимостей

Python: `3.9.7`

Packages: `python -m pip install -r requirements.txt`

## Получение данных

Сжатые данные:
* [GDrive](https://drive.google.com/drive/folders/1jHQWitJkqHN23rJa8OX3vpvJg_osRz13?usp=sharing)

### HSE

1. спарсить данные с [сайта](https://www.hse.ru/edu/vkr/?language=ru): `python get_diplomas_hse.py --output_path parsed_results/hse_data.json`

### ITMO

*Примечание: не нашел сборник всех ВКР, только тех, что участвовали в конкурсе __научно-исследовательских ВКР__*

1. скачать PDF [с описаниями ВКР](https://research.itmo.ru/ru/stat/48/nivkr.htm) и сохранить в папку `itmo_nivkr/` (на случай, если ссылка перестала работать, гуглить "ИТМО сборники НИВКР")
2. извлечь из PDF тексты (сохраняются в папку `itmo_nivkr_txt/`): `python extract_texts_from_pdf.py --pdf_folder itmo_nivkr/ --output_folder itmo_nivkr_txt --n_workers 4`
3. спарсить данные о ВКР: `python get_diplomas_itmo.py --txts_folder itmo_nivkr_txt/ --output_path parsed_results/itmo_data.json`

## Анализ

[Ноутбук](analysis.ipynb) разделен на несколько частей:

1. Импорт зависимостей и чтение данных
2. Очистка данных, извлечение полей из сырого текста
3. Распределение некоторых величин в дипломах (например, количество работ по образовательной программе или по уровню: бакалавриат или магистратура)
4. Изменение величин в течение времени (например, как распределялись работы по уровню обучения на протяжении нескольких лет)
5. Подсчет работ с упоминанием машинного обучения и близкой тематики (ML, DS, AI)
