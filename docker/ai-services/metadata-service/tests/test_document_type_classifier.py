from app.engine.document_type_classifier import DocumentTypeClassifier


class TestDocumentTypeClassifier:
    def test_nhan_dien_bom(self):
        classifier = DocumentTypeClassifier()
        assert classifier.classify("Bill of Material cho dự án nâng cấp mạng.") == "bom"

    def test_nhan_dien_meeting_minutes(self):
        classifier = DocumentTypeClassifier()
        assert classifier.classify("Biên bản họp ngày 12/07/2026 giữa 2 bên.") == "meeting_minutes"

    def test_nhan_dien_contract(self):
        classifier = DocumentTypeClassifier()
        assert classifier.classify("Hợp đồng cung cấp thiết bị số 001/2026.") == "contract"

    def test_dua_vao_ten_file_khi_noi_dung_khong_ro(self):
        classifier = DocumentTypeClassifier()
        result = classifier.classify("Nội dung chung chung.", filename="BOQ_du_an_ABC.xlsx")
        assert result == "boq"

    def test_khong_khop_gi_tra_none(self):
        classifier = DocumentTypeClassifier()
        assert classifier.classify("Văn bản không rõ loại nào cả.") is None

    def test_uu_tien_theo_thu_tu_dictionary(self):
        # 'bom' được liệt kê trước 'proposal' trong DEFAULT_DOCTYPE_KEYWORDS -> ưu tiên hơn
        classifier = DocumentTypeClassifier()
        result = classifier.classify("Đề xuất giải pháp kèm bill of material chi tiết.")
        assert result == "bom"
