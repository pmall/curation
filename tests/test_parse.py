"""The converters of drakkar-parse, on small samples of each file type (no network)."""

import subprocess
from datetime import datetime
from pathlib import Path

import docx
import openpyxl
import pymupdf
import pytest
import xlwt

from drakkar.parse import ParseError, markdown_table, parse

# ppat.1002331.s00*.doc: supplementary tables of PMID 22046132 (CC BY). Ours, made once with
# LibreOffice from a .docx (LibreOffice is no dependency): beyond-bmp.doc, and page-break.doc,
# whose first paragraph mark was then turned into a page break, as Word writes one.
SAMPLES = Path(__file__).parent / "samples"

JATS = """<?xml version="1.0"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front><article-meta>
    <title-group><article-title>NS1 binds <italic>TRIM25</italic></article-title></title-group>
    <abstract><p>We show that NS1 binds TRIM25.</p></abstract>
  </article-meta></front>
  <body>
    <sec><title>Results</title>
      <p>NS1 co-precipitates TRIM25 (<xref ref-type="fig" rid="f1">Fig. 1</xref>).
        <table-wrap><label>Table 1</label><caption><p>Interactions.</p></caption>
          <table>
            <thead><tr><th>Bait</th><th colspan="2">Prey</th></tr></thead>
            <tbody>
              <tr><td rowspan="2">NS1</td><td>TRIM25</td><td>Q14258</td></tr>
              <tr><td>RIG-I</td><td>O95786</td></tr>
            </tbody>
          </table>
        </table-wrap>
      </p>
      <fig id="f1"><label>Figure 1</label>
        <caption><title>Co-IP.</title><p>Anti-FLAG.</p></caption></fig>
      <sec><title>Mapping</title><p>Residues 1-73 of NS1.</p></sec>
    </sec>
  </body>
  <back>
    <ack><p>We thank everyone.</p></ack>
    <ref-list><ref><mixed-citation>A cited paper.</mixed-citation></ref></ref-list>
    <sec><title>Supporting Information</title>
      <supplementary-material xlink:href="s1.xlsx"><label>Table S1</label>
        <caption><p>Y2H screen.</p></caption></supplementary-material>
    </sec>
  </back>
</article>
"""


def test_jats(tmp_path: Path):
    path = tmp_path / "a.xml"
    path.write_text(JATS)
    assert parse(path) == (
        "# NS1 binds TRIM25\n\n"
        "## Abstract\n\nWe show that NS1 binds TRIM25.\n\n"
        "## Results\n\n"
        "NS1 co-precipitates TRIM25 (Fig. 1).\n\n"
        "**Table 1.** Interactions.\n\n"
        "| Bait | Prey | Prey |\n|---|---|---|\n"
        "| NS1 | TRIM25 | Q14258 |\n| NS1 | RIG-I | O95786 |\n\n"
        "**Figure 1.** Co-IP. Anti-FLAG.\n\n"
        "### Mapping\n\nResidues 1-73 of NS1.\n\n"
        "## Supporting Information\n\n"
        "**Table S1.** Y2H screen. (file s1.xlsx)\n"
    )


def test_jats_formula_alternatives_and_bad_spans(tmp_path: Path):
    path = tmp_path / "a.xml"
    path.write_text(
        "<article><body><p>K<sub>d</sub> = <inline-formula><alternatives>"
        "<tex-math>10^{-6}</tex-math><mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML'>"
        "<mml:mn>10</mml:mn></mml:math></alternatives></inline-formula> M</p>"
        "<table-wrap><table><tr><td colspan='x'>a</td><td>b</td></tr></table></table-wrap>"
        "</body></article>"
    )
    assert parse(path) == "Kd = 10^{-6} M\n\n**Table.**\n\n| a | b |\n|---|---|\n"


def test_jats_block_alternatives(tmp_path: Path):
    path = tmp_path / "a.xml"
    path.write_text(
        "<article><body><p>The ratio:</p><disp-formula><alternatives><tex-math>a/b</tex-math>"
        "<mml:math xmlns:mml='http://www.w3.org/1998/Math/MathML'><mml:mi>a</mml:mi></mml:math>"
        "</alternatives></disp-formula><alternatives><p>First notation.</p><p>Second.</p>"
        "</alternatives></body></article>"
    )
    assert parse(path) == "The ratio:\n\na/b\n\nFirst notation.\n"


def test_jats_namespaced(tmp_path: Path):
    path = tmp_path / "a.xml"
    path.write_text(
        '<article xmlns="http://jats.nlm.nih.gov"><front><article-meta><title-group>'
        "<article-title>NS1 binds TRIM25</article-title></title-group></article-meta></front>"
        "<body><sec><title>Results</title><p>Co-IP.</p></sec></body></article>"
    )
    assert parse(path) == "# NS1 binds TRIM25\n\n## Results\n\nCo-IP.\n"


def test_jats_text_inside_paragraphs(tmp_path: Path):
    """In PMC XML, the text of list items, definitions, table cells and table footnotes sits in
    paragraphs of its own."""
    path = tmp_path / "a.xml"
    path.write_text(
        "<article><body><sec><title>Methods</title>"
        "<list><list-item><p>Y2H screen</p><list><list-item><p>ORFeome</p></list-item></list>"
        "</list-item><list-item><p>LUMIER</p></list-item></list>"
        "<glossary><def-list><def-item><term>IP</term><def><p>immunoprecipitation</p></def>"
        "</def-item></def-list></glossary>"
        "<table-wrap><table><tr><td><p>NS1</p></td><td><p>TRIM25<sup>a</sup></p></td></tr>"
        "</table><table-wrap-foot><fn><p><sup>a</sup> Confirmed by co-IP.</p></fn>"
        "</table-wrap-foot></table-wrap></sec></body></article>"
    )
    assert parse(path) == (
        "## Methods\n\n"
        "- Y2H screen\n- ORFeome\n- LUMIER\n\n"
        "- IP immunoprecipitation\n\n"
        "**Table.**\n\n| NS1 | TRIM25a |\n|---|---|\n\n"
        "a Confirmed by co-IP.\n"
    )


def test_markdown_table_escapes_pipes_and_pads_rows():
    assert markdown_table([["a", "b|c"], ["d"]]) == "| a | b\\|c |\n|---|---|\n| d |  |"


def test_html(tmp_path: Path):
    paragraphs = "".join(
        f"<p>Paragraph {i}: NS1 co-precipitates TRIM25 in HEK293 cells, as the blots show.</p>"
        for i in range(30)
    )
    path = tmp_path / "a.html"
    path.write_text(
        "<html><head><title>T</title><script>var x = 1;</script></head><body>"
        "<nav><a href='/'>Home</a></nav>"
        f"<article><h1>NS1 binds TRIM25</h1><h2>Results</h2>{paragraphs}"
        "<table><tr><th>Bait</th><th>Prey</th></tr><tr><td>NS1</td><td>TRIM25</td></tr></table>"
        "</article></body></html>"
    )
    text = parse(path)
    assert "Paragraph 29: NS1 co-precipitates TRIM25" in text
    assert "| NS1 | TRIM25 |" in text
    assert "var x" not in text


def test_html_charset(tmp_path: Path):
    paragraphs = "".join(
        f"<p>Prot&eacute;ine {i} : NS1 lie TRIM25, voir la figure.</p>" for i in range(30)
    )
    head = '<head><meta charset="iso-8859-1"></head>'
    page = f"<html>{head}<body><article>{paragraphs}</article></body></html>"
    path = tmp_path / "a.html"
    path.write_bytes(page.replace("&eacute;", "\u00e9").encode("iso-8859-1"))
    assert "Prot\u00e9ine 29 : NS1 lie TRIM25" in parse(path)


def test_pdf_pages(tmp_path: Path):
    document = pymupdf.open()
    for words in ("NS1 binds TRIM25", "Figure 2: co-IP"):
        page = document.new_page()
        page.insert_text((72, 72), words)
    path = tmp_path / "a.pdf"
    document.save(path)
    assert parse(path) == (
        "--- page 1 ---\n\nNS1 binds TRIM25\n\n--- page 2 ---\n\nFigure 2: co-IP\n\n"
    )


def test_scanned_pdf(tmp_path: Path):
    document = pymupdf.open()
    document.new_page()
    path = tmp_path / "a.pdf"
    document.save(path)
    with pytest.raises(ParseError, match="no text layer"):
        parse(path)


def test_xlsx(tmp_path: Path):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Y2H"
    sheet.append(["Bait", "Prey", "Score", None])
    sheet.append(["NS1", "TRIM25", 2.0, None])
    sheet.append([None, None, None, None])
    sheet.append(["NS2", "line\nbreak", 0.5])
    workbook.create_sheet("Empty")
    path = tmp_path / "a.xlsx"
    workbook.save(path)
    assert parse(path) == (
        "## Sheet Y2H\n\nBait\tPrey\tScore\nNS1\tTRIM25\t2\nNS2\tline break\t0.5\n\n"
        "## Sheet Empty\n\n(empty)\n"
    )


def test_xls(tmp_path: Path):
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Y2H")
    for column, value in enumerate(["Bait", "Prey", "Score"]):
        sheet.write(0, column, value)
    sheet.write(1, 0, "NS1")
    sheet.write(
        1, 1, datetime(2002, 9, 2), xlwt.easyxf(num_format_str="D-MMM")
    )  # SEPT2, as Excel saw it
    sheet.write(1, 2, 2.0)
    path = tmp_path / "a.xls"
    workbook.save(str(path))
    assert parse(path) == "## Sheet Y2H\n\nBait\tPrey\tScore\nNS1\t2002-09-02T00:00:00\t2\n"


def test_docx(tmp_path: Path):
    document = docx.Document()
    document.add_heading("Table S1", level=1)
    document.add_paragraph("Validated interactions.")
    table = document.add_table(rows=2, cols=2)
    for row, cells in zip(table.rows, [("Bait", "Prey"), ("NS1", "TRIM25")], strict=True):
        for cell, value in zip(row.cells, cells, strict=True):
            cell.text = value
    path = tmp_path / "a.docx"
    document.save(str(path))
    assert parse(path) == (
        "# Table S1\n\nValidated interactions.\n\n| Bait | Prey |\n|---|---|\n| NS1 | TRIM25 |\n"
    )


def table_rows(markdown: str) -> list[list[str]]:
    """The rows of the Markdown tables of a converted text, their header separator left out."""
    lines = [line for line in markdown.splitlines() if line.startswith("| ")]
    return [line[2:-2].split(" | ") for line in lines]


def test_doc():
    """Table S3, Word 97-2003."""
    rows = table_rows(parse(SAMPLES / "ppat.1002331.s006.doc"))
    assert len(rows) == 3
    assert rows[0][1].startswith("Fraction of SARS-CoV interaction partners")
    assert rows[2] == [
        "SARS interaction partners (complete)",
        "36/514=7%",
        "884/31,941=2.8%",
        "4.4e-07",
    ]


def test_doc_rows_end_where_word_ends_them():
    """Table S1: a header cell broken over two lines, empty cells, and row properties too large
    for their page (in the Data stream)."""
    rows = table_rows(parse(SAMPLES / "ppat.1002331.s004.doc"))
    assert {len(r) for r in rows} == {9}
    assert rows[0][4] == "Number of times this prey has been isolated."
    assert rows[1] == [
        "A",
        "ORF13",
        "RYBP",
        "23429",
        "5",
        "RING1 and YY1 binding protein",
        "ORFeome",
        "4,9",
        "78,4",
    ]
    assert len(rows) == 88


def test_doc_cell_spanning_columns():
    """Table S2: empty last cells, and a row whose second cell spans two columns."""
    rows = table_rows(parse(SAMPLES / "ppat.1002331.s005.doc"))
    assert {len(r) for r in rows} == {7}
    assert rows[3] == ["Nsp13", "nsp13", "DDX5", "1655", "Ddx5", "19224332", ""]
    spanning = next(r for r in rows if "(prev desig U122 and X4)" in r)
    assert spanning == ["", "(prev desig U122 and X4)", "(prev desig U122 and X4)", "", "", "", ""]


def test_doc_characters_beyond_the_basic_plane():
    """A character beyond U+FFFF takes 4 bytes in the text: the cell marks after it are still
    found."""
    assert parse(SAMPLES / "beyond-bmp.doc") == (
        "Binding of \U0001d6fc-actinin (\U0001d6fc beyond U+FFFF) to NS1.\n\n"
        "| Bait | Prey |\n|---|---|\n| \U0001d6fc-NS1 | TRIM25 |\n\nAfter the table.\n"
    )


def test_doc_page_break_ends_a_paragraph():
    assert parse(SAMPLES / "page-break.doc") == (
        "Before the break.\n\nAfter the break.\n\nNext paragraph.\n"
    )


def test_not_a_doc(tmp_path: Path):
    path = tmp_path / "a.doc"
    path.write_text("plain text")
    with pytest.raises(ParseError, match="not a Word 97-2003 document"):
        parse(path)


def test_text_is_kept_without_invisible_characters(tmp_path: Path):
    path = tmp_path / "a.csv"
    path.write_text("bait,prey\nNS1,TRIM\u200b25,co\u00adIP\n")
    assert parse(path) == "bait,prey\nNS1,TRIM25,coIP\n"


def test_text_in_windows_encoding(tmp_path: Path):
    path = tmp_path / "a.csv"
    path.write_bytes("bait;prey\nNS1;prot\u00e9ine\n".encode("cp1252"))
    assert parse(path) == "bait;prey\nNS1;prot\u00e9ine\n"


def test_unknown_type(tmp_path: Path):
    path = tmp_path / "a.tif"
    path.write_bytes(b"II*\x00")
    with pytest.raises(ParseError, match="no converter for .tif"):
        parse(path)


def test_damaged_file_is_refused(tmp_path: Path):
    path = tmp_path / "a.xlsx"
    path.write_bytes(b"PK\x03\x04 not really a workbook")
    with pytest.raises(ParseError, match="cannot be read"):
        parse(path)


def test_command_writes_the_output(tmp_path: Path):
    source, out = tmp_path / "a.xml", tmp_path / "a.md"
    source.write_text(JATS)
    done = subprocess.run(
        ["uv", "run", "drakkar-parse", str(source), str(out)], capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    assert out.read_text().startswith("# NS1 binds TRIM25")
    done = subprocess.run(
        ["uv", "run", "drakkar-parse", str(tmp_path / "a.tif"), str(tmp_path / "b.md")],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 1
    assert "no converter" in done.stderr
    assert not (tmp_path / "b.md").exists()
