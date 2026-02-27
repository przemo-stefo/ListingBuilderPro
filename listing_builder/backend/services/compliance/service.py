# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/services/compliance/service.py
# Purpose: Orchestrator — receives file, delegates to parser + rules, saves report to DB
# NOT for: Parsing logic, rule definitions, or API routing

from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
import structlog

from models.compliance import ComplianceReport, ComplianceReportItem
from .parser_amazon import parse_amazon_xlsm
from .parser_ebay import parse_ebay_xlsx
from .parser_kaufland import parse_kaufland_csv
from .rules import validate_row

logger = structlog.get_logger()

# File extension → marketplace mapping for auto-detection
EXTENSION_MAP = {
    ".xlsm": "amazon",
    ".xlsx": "ebay",
    ".csv": "kaufland",
}

# Marketplace → parser function
PARSER_MAP = {
    "amazon": parse_amazon_xlsm,
    "ebay": parse_ebay_xlsx,
    "kaufland": parse_kaufland_csv,
}

# Marketplace → (sku_field, title_field) for extracting product identity
IDENTITY_FIELDS = {
    "amazon": ("item_sku", "item_name"),
    "ebay": ("Custom label (SKU)", "Title"),
    "kaufland": ("ean", "title"),
}


class ComplianceService:
    """
    Main compliance validation orchestrator.
    Takes a file, parses it, runs rules, saves report.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_file(
        self, file_bytes: bytes, filename: str, marketplace: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ComplianceReport:
        """
        Full validation pipeline:
        1. Detect marketplace from filename or explicit param
        2. Parse the file into product rows
        3. Run marketplace rules on each row
        4. Save report + items to DB
        5. Return the report
        """
        # Step 1: Detect marketplace
        if not marketplace:
            marketplace = self._detect_marketplace(filename)
        marketplace = marketplace.lower()

        if marketplace not in PARSER_MAP:
            raise ValueError(
                f"Unsupported marketplace: {marketplace}. "
                f"Supported: {', '.join(PARSER_MAP.keys())}"
            )

        logger.info(
            "compliance_validation_started",
            filename=filename,
            marketplace=marketplace,
        )

        # Step 2: Parse file
        parser = PARSER_MAP[marketplace]
        products = parser(file_bytes)

        if not products:
            raise ValueError(
                f"No product rows found in {filename}. "
                f"Check that the file format matches the {marketplace} template."
            )

        # Step 3: Validate each row and build items
        sku_field, title_field = IDENTITY_FIELDS[marketplace]
        items = []
        compliant_count = 0
        warning_count = 0
        error_count = 0

        for product in products:
            row_num = product.get("_row_number", 0)
            sku = product.get(sku_field, "")
            title = product.get(title_field, "")

            issues = validate_row(product, marketplace)

            # Determine worst severity for this product
            has_error = any(i["severity"] == "error" for i in issues)
            has_warning = any(i["severity"] == "warning" for i in issues)

            if has_error:
                status = "error"
                error_count += 1
            elif has_warning:
                status = "warning"
                warning_count += 1
            else:
                status = "compliant"
                compliant_count += 1

            item = ComplianceReportItem(
                row_number=row_num,
                sku=sku[:500] if sku else "",
                product_title=title[:1000] if title else "",
                compliance_status=status,
                issues=issues,
            )
            items.append(item)

        # Step 4: Calculate score and save report
        total = len(items)
        score = (compliant_count / total * 100) if total > 0 else 0.0

        report = ComplianceReport(
            user_id=user_id,
            marketplace=marketplace,
            filename=filename,
            total_products=total,
            compliant_count=compliant_count,
            warning_count=warning_count,
            error_count=error_count,
            overall_score=round(score, 1),
        )
        report.items = items

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(
            "compliance_validation_complete",
            report_id=report.id,
            total=total,
            compliant=compliant_count,
            warnings=warning_count,
            errors=error_count,
            score=report.overall_score,
        )

        return report

    def get_reports(
        self,
        limit: int = 20,
        offset: int = 0,
        marketplace: Optional[str] = None,
    ) -> Tuple[List[ComplianceReport], int]:
        """
        List past reports with pagination and optional marketplace filter.
        Returns (reports, total_count).
        """
        query = self.db.query(ComplianceReport)

        if marketplace:
            query = query.filter(ComplianceReport.marketplace == marketplace.lower())

        total = query.count()
        reports = (
            query
            .order_by(ComplianceReport.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return reports, total

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get a single report by ID, with all items loaded."""
        return (
            self.db.query(ComplianceReport)
            .filter(ComplianceReport.id == report_id)
            .first()
        )

    @staticmethod
    def _detect_marketplace(filename: str) -> str:
        """
        Auto-detect marketplace from file extension.
        .xlsm → amazon, .xlsx → ebay, .csv → kaufland
        """
        filename_lower = filename.lower()
        for ext, marketplace in EXTENSION_MAP.items():
            if filename_lower.endswith(ext):
                return marketplace

        raise ValueError(
            f"Cannot detect marketplace from filename '{filename}'. "
            f"Supported extensions: {', '.join(EXTENSION_MAP.keys())}. "
            f"Or pass marketplace= parameter explicitly."
        )
