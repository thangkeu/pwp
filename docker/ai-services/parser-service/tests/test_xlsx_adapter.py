from app.adapters.base import ParsingError
from app.adapters.xlsx_adapter import XlsxAdapter


class TestXlsxAdapter:
    def test_supported_extensions(self):
        assert set(XlsxAdapter().supported_extensions) == {"xlsx", "xlsm"}

    def test_parse_moi_sheet_thanh_1_table(self, sample_xlsx_bytes):
        result = XlsxAdapter().parse(sample_xlsx_bytes, "bom.xlsx")

        assert len(result.tables) == 1
        assert result.tables[0].caption == "BOM"
        assert result.tables[0].rows[0] == ["Part Number", "Qty", "Unit Price"]
        assert result.tables[0].rows[1] == ["FG-100F", "2", "15000000"]
        assert "FG-100F" in result.text
        assert result.metadata.page_count == 1

    def test_parse_file_hong_nem_parsing_error(self):
        try:
            XlsxAdapter().parse(b"not an xlsx", "fake.xlsx")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass
