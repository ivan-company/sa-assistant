from googleapiclient.discovery import build

from .base import GoogleAPI


class GoogleDocsAPI(GoogleAPI):
    def get_service(self):
        return build("docs", "v1", credentials=self.get_credentials())

    def get_document(self, document_id: str) -> dict:
        service = self.get_service()
        return service.documents().get(documentId=document_id).execute()

    def extract_data(self, document_id: str) -> str:
        doc_json = self.get_document(document_id)
        text_chunks = []
        for element in doc_json.get("body", {}).get("content", []):
            if "table" in element:
                text_chunks.append(self._extract_table(element))
            elif "paragraph" in element:
                paragraph = self._extract_paragraph(element)
                if paragraph:
                    text_chunks.append(paragraph)
        return text_chunks

    def _extract_paragraph(self, element) -> str:
        result = []
        # Detect heading style
        para_style = element["paragraph"].get("paragraphStyle", {})
        named_style = para_style.get("namedStyleType", "")
        heading_level = None
        if named_style.startswith("HEADING_"):
            try:
                heading_level = int(named_style.split("_")[1])
            except Exception:
                heading_level = None
        for e in element["paragraph"].get("elements", []):
            if "textRun" in e:
                content = e["textRun"].get("content", "")
                if content.endswith("\n"):
                    content = content[:-1]
                if content.strip() not in ["", "\n"]:
                    if heading_level:
                        result.append(f"{'#' * heading_level} {content.strip()}")
                    else:
                        result.append(content)
        return "".join(result).strip()

    def _clean_cells(self, cells):
        cleaned_cells = []
        for cell in cells:
            text_cell = self._extract_cell_text_simple(cell)
            if text_cell.strip() not in ["", "\n"]:
                cleaned_cells.append(cell)
        return cleaned_cells

    def _is_colored(self, cell):
        # Returns True if the cell's background is not white (or missing)
        style = cell.get("tableCellStyle", {})
        color = style.get("backgroundColor", {}).get("color", {}).get("rgbColor", {})
        # Default to white if not specified
        r = color.get("red", 1)
        g = color.get("green", 1)
        b = color.get("blue", 1)
        # Consider as colored if any channel is not 1 (not white)
        return (r, g, b) != (1, 1, 1)

    def _extract_cell_text_simple(self, cell):
        # Simple text extraction for table cell (no chips)
        text = ""
        for p in cell.get("content", []):
            for e in p.get("paragraph", {}).get("elements", []):
                if "textRun" in e:
                    text += e["textRun"].get("content", "")
        return text.strip()

    def _extract_table(self, element):
        table = element["table"]
        rows = table["tableRows"]
        if not rows:
            return ""
        n_cols = len(rows[0]["tableCells"]) if rows[0]["tableCells"] else 0
        if n_cols == 0:
            return ""
        # Horizontal table: scan for multi-column colored header row, treat single-cell colored rows as titles
        formatted_output = []
        row_idx = 0
        while row_idx < len(rows):
            row = rows[row_idx]
            cells = row["tableCells"]
            cells = self._clean_cells(cells)
            # If all cells are colored and only one cell, treat as title
            if len(cells) == 1 and self._is_colored(cells[0]):
                title = self._extract_cell_text_simple(cells[0])
                if title:
                    formatted_output.append(f"## {title}")
                row_idx += 1
                continue
            # If all cells are colored and more than one cell, treat as header row
            if len(cells) > 1 and all(self._is_colored(cell) for cell in cells):
                headers = [self._extract_cell_text_simple(cell) for cell in cells]
                data_rows = rows[row_idx + 1 :]
                formatted_rows = []
                for i, data_row in enumerate(data_rows):
                    values = [
                        self._extract_cell_text_simple(cell)
                        for cell in data_row["tableCells"]
                    ]
                    if all(v == "" for v in values):
                        continue
                    formatted = f"{len(formatted_rows) + 1}.\n"
                    for h, v in zip(headers, values):
                        formatted += f"  - {h if h else ''} -> {v}\n"
                    formatted_rows.append(formatted.rstrip())
                if formatted_rows:
                    formatted_output.append("\n".join(formatted_rows))
                break  # Done with this table
            # Otherwise, not a header row, move to next row
            row_idx += 1
        # If not horizontal, check for vertical header (all first column cells colored)
        else:
            if all(self._is_colored(row["tableCells"][0]) for row in rows):
                headers = [
                    self._extract_cell_text_simple(row["tableCells"][0]) for row in rows
                ]
                formatted_cols = []
                n_cols = len(rows[0]["tableCells"])
                for col_idx in range(1, n_cols):
                    values = [
                        self._extract_cell_text_simple(row["tableCells"][col_idx])
                        for row in rows
                    ]
                    if all(v == "" for v in values):
                        continue
                    formatted = f"{len(formatted_cols) + 1}.\n"
                    for h, v in zip(headers, values):
                        formatted += f"  - {h if h else ''} -> {v}\n"
                    formatted_cols.append(formatted.rstrip())
                if formatted_cols:
                    formatted_output.append("\n".join(formatted_cols))
        return "\n".join(formatted_output) if formatted_output else ""
