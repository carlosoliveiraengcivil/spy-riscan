"""
SPY RiSCAN - Auditor de Inventários Volumétricos
Módulo de Geração de Relatório Excel
Desenvolvido por Carlos Oliveira
"""

import os
from datetime import datetime
from typing import List, Dict, Any

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class VolumeReportGenerator:
    def __init__(self, project_name: str, operator_name: str = "Projetista"):
        self.project_name = project_name
        self.operator_name = operator_name

    def generate_excel_report(self, records: List[Dict[str, Any]], output_path: str) -> bool:
        """Gera a planilha Excel de auditoria."""
        if not HAS_OPENPYXL:
            return self._generate_csv_fallback(records, output_path.replace(".xlsx", ".csv"))

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "SPY RiSCAN - Auditoria"

            # Estilos
            hdr_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
            hdr_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            title_font = Font(name="Segoe UI", size=16, bold=True, color="1A365D")
            sub_font = Font(name="Segoe UI", size=10, italic=True, color="4A5568")
            cell_font = Font(name="Segoe UI", size=10)
            bold_font = Font(name="Segoe UI", size=10, bold=True)
            thin = Border(
                left=Side(style='thin', color='E2E8F0'),
                right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'),
                bottom=Side(style='thin', color='E2E8F0')
            )

            # Cabeçalho
            ws.merge_cells("A1:G1")
            ws["A1"] = "SPY RiSCAN - RELATÓRIO DE AUDITORIA VOLUMÉTRICA"
            ws["A1"].font = title_font
            ws["A1"].alignment = Alignment(vertical="center")
            ws.row_dimensions[1].height = 30

            ws.merge_cells("A2:G2")
            ws["A2"] = f"Projeto: {self.project_name}  |  Responsável: {self.operator_name}  |  Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ws["A2"].font = sub_font
            ws.row_dimensions[2].height = 20

            # Cabeçalhos da tabela
            headers = [
                "#", "Nome Volume", "Base Mesh (Nuvem/Smooth)",
                "Primitivo (Ref. Mesh)", "Plano de Referência",
                "Polilinha", "Volume [m³]", "Data / Hora"
            ]

            row = 4
            ws.row_dimensions[row].height = 25
            for ci, txt in enumerate(headers, start=1):
                c = ws.cell(row=row, column=ci, value=txt)
                c.fill = hdr_fill
                c.font = hdr_font
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = thin

            # Dados e Identificação de Duplicidades
            vol_counts = {}
            for r in records:
                v = r.get("volume_value")
                if isinstance(v, (int, float)) and v > 0:
                    rounded = round(float(v), 2)
                    vol_counts[rounded] = vol_counts.get(rounded, 0) + 1

            dup_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            dup_font = Font(name="Segoe UI", size=10, bold=True, color="991B1B")

            for i, r in enumerate(records, start=1):
                row += 1
                ws.row_dimensions[row].height = 22
                vol = r.get("volume_value", 0.0)
                is_dup = False
                if isinstance(vol, (int, float)) and vol > 0:
                    rounded = round(float(vol), 2)
                    if vol_counts.get(rounded, 0) > 1:
                        is_dup = True
                    vol_disp = vol
                else:
                    vol_disp = 0.0

                item_num = f"⚠️ {i:02d}" if is_dup else f"{i:02d}"

                vals = [
                    item_num,
                    r.get("volume_name", ""),
                    r.get("base_mesh", ""),
                    r.get("reference_mesh", ""),
                    r.get("reference_plane", ""),
                    r.get("polyline", ""),
                    vol_disp,
                    r.get("timestamp", "")
                ]

                for ci, v in enumerate(vals, start=1):
                    c = ws.cell(row=row, column=ci, value=v)
                    c.border = thin
                    if is_dup:
                        c.fill = dup_fill
                        c.font = dup_font
                    else:
                        c.font = cell_font

                    if ci in (1, 5, 8):
                        c.alignment = Alignment(horizontal="center", vertical="center")
                    elif ci == 7:
                        c.number_format = '#,##0.00'
                        c.alignment = Alignment(horizontal="right", vertical="center")
                        if not is_dup:
                            c.font = bold_font
                    else:
                        c.alignment = Alignment(horizontal="left", vertical="center")

            # Larguras das Colunas
            widths = [10, 22, 30, 30, 20, 18, 18, 20]
            for i, w in enumerate(widths, start=1):
                ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

            wb.save(output_path)
            return True
        except Exception as e:
            print(f"[Report] Erro Excel: {e}")
            return False

    def _generate_csv_fallback(self, records: List[Dict[str, Any]], output_path: str) -> bool:
        try:
            vol_counts = {}
            for r in records:
                v = r.get("volume_value")
                if isinstance(v, (int, float)) and v > 0:
                    rounded = round(float(v), 2)
                    vol_counts[rounded] = vol_counts.get(rounded, 0) + 1

            with open(output_path, "w", encoding="utf-8-sig") as f:
                f.write(f"PROJETO:;{self.project_name};RESPONSÁVEL:;{self.operator_name};DATA:;{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write("#;Nome Volume;Base Mesh;Primitivo;Plano Ref;Polilinha;Volume [m3];Data/Hora;Status\n")
                for i, r in enumerate(records, start=1):
                    v = r.get('volume_value')
                    is_dup = isinstance(v, (int, float)) and v > 0 and vol_counts.get(round(float(v), 2), 0) > 1
                    status = "DUPLICADO / ATENCAO" if is_dup else "OK"
                    f.write(f"{i};{r.get('volume_name')};{r.get('base_mesh')};{r.get('reference_mesh')};{r.get('reference_plane')};{r.get('polyline')};{r.get('volume_value')};{r.get('timestamp')};{status}\n")
            return True
        except Exception:
            return False
