import re
from dataclasses import dataclass


@dataclass
class SongEntry:
    raw_line: str
    artists: list[str]
    title: str
    line_number: int

    @property
    def search_query(self) -> str:
        artist_str = " ".join(self.artists)
        return f"{self.title} {artist_str}"

    @property
    def clean_filename(self) -> str:
        name = self.title.strip()
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.rstrip('.')
        if not name:
            name = "untitled"
        return name


def parse_line(line: str, line_number: int) -> SongEntry | None:
    line = line.strip()
    if not line:
        return None

    if ' - ' not in line:
        return SongEntry(
            raw_line=line,
            artists=[],
            title=line,
            line_number=line_number,
        )

    parts = line.rsplit(' - ', 1)
    artist_part = parts[0].strip()
    title = parts[1].strip()

    artists = [a.strip() for a in artist_part.split(',') if a.strip()]

    return SongEntry(
        raw_line=line,
        artists=artists,
        title=title,
        line_number=line_number,
    )


def parse_file(filepath: str) -> list[SongEntry]:
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            entry = parse_line(line, i)
            if entry:
                entries.append(entry)
    return entries
