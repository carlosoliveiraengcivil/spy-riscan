"""
Módulo de Leitura e Extração de Dados do Projeto RiSCAN PRO (.RiSCAN / project.rsp)
Compatível com RiSCAN PRO 2.0 até 2.19+
Desenvolvido por Carlos Oliveira
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


class RiSCANProjectParser:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        if os.path.isdir(self.project_path):
            self.rsp_file = os.path.join(self.project_path, "project.rsp")
            self.log_file = os.path.join(self.project_path, "project.log")
        else:
            self.rsp_file = self.project_path
            self.project_path = os.path.dirname(self.rsp_file)
            self.log_file = os.path.join(self.project_path, "project.log")

        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self.project_name = os.path.basename(self.project_path).replace(".RiSCAN", "")
        self.last_modified = None
        self.known_values: Dict[str, float] = {}

        if os.path.exists(self.rsp_file):
            self.reload()

    def reload(self) -> bool:
        """Recarrega o arquivo XML project.rsp do disco."""
        try:
            if not os.path.exists(self.rsp_file):
                return False
            self.last_modified = os.path.getmtime(self.rsp_file)
            self.tree = ET.parse(self.rsp_file)
            self.root = self.tree.getroot()
            return True
        except Exception:
            return False

    def is_updated(self) -> bool:
        if not os.path.exists(self.rsp_file):
            return False
        current_mtime = os.path.getmtime(self.rsp_file)
        return self.last_modified is None or current_mtime > self.last_modified

    def get_all_volume_values(self) -> Dict[str, float]:
        """
        Extrai todos os volumes ativos salvos no project.rsp.
        Ex: {'Volume001_Fill': 30.17, 'Volume001_Cut': 0.035, 'Pilha1_Fill': 30.16}
        """
        values = {}
        if not self.reload() or self.root is None:
            return values

        for val_elem in self.root.iter("value"):
            if val_elem.get("states") == "deleted":
                continue

            name = val_elem.findtext("name") or val_elem.get("name") or ""
            vtype = val_elem.findtext("valuetype") or ""
            vval_str = val_elem.findtext("valuevalue") or val_elem.findtext("val") or val_elem.findtext("value")

            if (vtype == "VOLUME" or "fill" in name.lower() or "cut" in name.lower() or "volume" in name.lower()) and vval_str:
                try:
                    clean_str = vval_str.replace("m³", "").replace("m3", "").strip()
                    values[name] = float(clean_str)
                except (ValueError, TypeError):
                    pass

        return values

    def get_polylines_summary(self) -> List[str]:
        polys = []
        if self.root is None:
            return polys
        for p in self.root.iter("polyline_object"):
            if p.get("states") != "deleted":
                name = p.findtext("name") or p.get("name")
                if name and "@" not in name:
                    polys.append(name)
        return polys

    def get_meshes_summary(self) -> List[str]:
        meshes = []
        if self.root is None:
            return meshes
        for p in self.root.iter("polydata_object"):
            if p.get("states") != "deleted":
                name = p.findtext("name") or p.get("name")
                if name:
                    meshes.append(name)
        return meshes

    def get_planes_summary(self) -> List[str]:
        planes = []
        if self.root is None:
            return planes
        for p in self.root.iter("plane_object"):
            if p.get("states") != "deleted":
                name = p.findtext("name") or p.get("name")
                if name:
                    planes.append(name)
        return planes
