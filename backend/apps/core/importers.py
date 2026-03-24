"""
兼容模块。

Excel 导入逻辑已经迁移到 apps.destinations.importers。
"""

from apps.destinations.importers import import_excel_directory, import_excel_file, load_sheet_rows, validate_headers


__all__ = ["import_excel_directory", "import_excel_file", "load_sheet_rows", "validate_headers"]

