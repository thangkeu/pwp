"""MetadataEngine — orchestrator, phối hợp toàn bộ extractor thành 1 lần gọi duy nhất."""

from __future__ import annotations

from app.domain.extracted_metadata import ExtractedMetadata
from app.engine.date_extractor import DateExtractor
from app.engine.dictionary_extractor import DictionaryExtractor
from app.engine.document_type_classifier import DocumentTypeClassifier
from app.engine.security_level_classifier import SecurityLevelClassifier
from app.engine.vendor_dictionary import VendorModelExtractor
from app.engine.version_extractor import VersionExtractor

_MAX_TEXT_LENGTH_WARNING = 500_000  # ký tự — cảnh báo nếu văn bản quá dài, có thể ảnh hưởng hiệu năng regex


class MetadataEngine:
    """
    KHÔNG hard-code các extractor cụ thể ở nơi khác gọi trực tiếp — mọi tầng trên (API, Sprint
    sau là Sync Engine tự động gọi khi có tài liệu mới) chỉ cần biết `MetadataEngine.extract()`,
    giống triết lý `AIProviderAdapter`/`ParserAdapter` đã áp dụng ở Sprint 0.3 và 1.1.
    """

    def __init__(
        self,
        vendor_extractor: VendorModelExtractor | None = None,
        date_extractor: DateExtractor | None = None,
        version_extractor: VersionExtractor | None = None,
        security_classifier: SecurityLevelClassifier | None = None,
        doctype_classifier: DocumentTypeClassifier | None = None,
        dictionary_extractor: DictionaryExtractor | None = None,
    ):
        self._vendor_extractor = vendor_extractor or VendorModelExtractor()
        self._date_extractor = date_extractor or DateExtractor()
        self._version_extractor = version_extractor or VersionExtractor()
        self._security_classifier = security_classifier or SecurityLevelClassifier()
        self._doctype_classifier = doctype_classifier or DocumentTypeClassifier()
        self._dictionary_extractor = dictionary_extractor or DictionaryExtractor()

    def extract(self, text: str, filename: str | None = None) -> ExtractedMetadata:
        """
        @param text: nội dung văn bản đã parse (thường là `ParsedDocument.text` từ Parser Service)
        @param filename: tên file gốc, dùng thêm cho DocumentTypeClassifier (không bắt buộc)
        @returns: ExtractedMetadata — không bao giờ ném lỗi vì thiếu dữ liệu, chỉ trả kết quả
            rỗng/mặc định (Fail gracefully: 1 văn bản không khớp pattern nào KHÔNG phải lỗi hệ
            thống, chỉ đơn giản là không phát hiện được gì).
        """
        warnings: list[str] = []
        if len(text) > _MAX_TEXT_LENGTH_WARNING:
            warnings.append(
                f"Văn bản dài {len(text)} ký tự, vượt ngưỡng khuyến nghị {_MAX_TEXT_LENGTH_WARNING} "
                "— cân nhắc chunk trước khi đưa vào Metadata Engine ở Sprint sau."
            )

        return ExtractedMetadata(
            customers=self._dictionary_extractor.extract_customers(text),
            projects=self._dictionary_extractor.extract_projects(text),
            vendor_models=self._vendor_extractor.extract(text),
            security_level=self._security_classifier.classify(text),
            document_type=self._doctype_classifier.classify(text, filename),
            industries=self._dictionary_extractor.extract_industries(text),
            dates_found=self._date_extractor.extract(text),
            versions_found=self._version_extractor.extract(text),
            warnings=warnings,
        )
