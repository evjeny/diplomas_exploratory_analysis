from dataclasses import dataclass


@dataclass
class Diploma:
    title: str
    educational_programme: str
    year: int
    abstract: str
    level: str = ""
    faculty: str = ""
