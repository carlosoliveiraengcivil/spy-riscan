"""
SPY RiSCAN - Auditor de Inventários Volumétricos
Módulo de Escuta (Listener) Híbrido:
- Identificação precisa da janela modal 'Calculate volume & surface area...' (sem falso-positivo com a vista 3D).
- Classificação inteligente dos parâmetros com base no projeto RiSCAN.
- Gatilho instantâneo via project.log e fechamento de janela com debounce.
- Sincronização automática dos volumes em m³ ao salvar o projeto no RiSCAN (Ctrl+S).
Desenvolvido por Carlos Oliveira
"""

import os
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

try:
    import uiautomation as auto
    auto.SetGlobalSearchTimeout(0.2)
    HAS_UIAUTOMATION = True
except ImportError:
    HAS_UIAUTOMATION = False

from project_parser import RiSCANProjectParser


def debug_log(msg: str):
    try:
        base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base, "spy_debug.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def safe_get_text(ctrl) -> str:
    """Extrai texto de um controle de forma segura e imediata."""
    try:
        for ch in ctrl.GetChildren():
            try:
                ct = ch.ControlType
                if ct in (auto.ControlType.EditControl, auto.ControlType.TextControl):
                    t = ch.Name or ""
                    if not t:
                        try:
                            t = ch.GetWindowText()
                        except Exception:
                            pass
                    if t and t.strip():
                        return t.strip()
            except Exception:
                pass
    except Exception:
        pass

    try:
        if ctrl.Name and ctrl.Name.strip():
            return ctrl.Name.strip()
    except Exception:
        pass

    try:
        leg = ctrl.GetLegacyIAccessiblePattern()
        if leg and leg.Value and leg.Value.strip():
            return leg.Value.strip()
    except Exception:
        pass

    try:
        vp = ctrl.GetValuePattern()
        if vp and vp.Value and vp.Value.strip():
            return vp.Value.strip()
    except Exception:
        pass

    try:
        t = ctrl.GetWindowText()
        if t and t.strip():
            return t.strip()
    except Exception:
        pass

    return ""


class RiSCANVolumeListener:
    def __init__(self, on_calculation_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_rsp_update_callback: Optional[Callable[[], None]] = None,
                 project_path: str = ""):
        self.callback = on_calculation_callback
        self.on_rsp_update = on_rsp_update_callback
        self.project_path = project_path
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._window_was_open = False
        self._cached_dialog_data: Optional[Dict[str, Any]] = None
        self._last_dispatch_time = 0.0

        self.parser: Optional[RiSCANProjectParser] = None
        self._last_log_size = 0
        self._last_rsp_mtime = 0
        self._log_file = ""
        self._rsp_file = ""

        if project_path:
            self.set_project(project_path)

    def set_project(self, project_path: str):
        self.project_path = project_path
        self.parser = RiSCANProjectParser(project_path)
        self._log_file = os.path.join(project_path, "project.log")
        self._rsp_file = os.path.join(project_path, "project.rsp")
        if os.path.exists(self._log_file):
            try:
                self._last_log_size = os.path.getsize(self._log_file)
            except Exception:
                self._last_log_size = 0
        if os.path.exists(self._rsp_file):
            try:
                self._last_rsp_mtime = os.path.getmtime(self._rsp_file)
            except Exception:
                self._last_rsp_mtime = 0
        debug_log(f"Projeto configurado: {project_path}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        debug_log("Listener iniciado.")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        debug_log("Listener parado.")

    def _monitor_loop(self):
        while self._running:
            try:
                if HAS_UIAUTOMATION:
                    self._check_dialog_uiautomation()

                self._check_project_log()
                self._check_project_rsp()
            except Exception as e:
                debug_log(f"Erro no loop: {e}")
            time.sleep(0.3)

    def _find_volume_dialog(self):
        """Busca estritamente a janela modal de cálculo (sem pegar a vista 3D VOLUME)."""
        if not HAS_UIAUTOMATION:
            return None

        try:
            # Padrão estrito que começa com 'Calculate volume'
            dlg = auto.WindowControl(searchDepth=3, RegexName="(?i)^Calculate volume.*")
            if dlg.Exists(maxSearchSeconds=0.05):
                name = dlg.Name or ""
                # Garante que não é a janela do SPY nem uma vista de objeto
                if "object view" not in name.lower() and "spy" not in name.lower():
                    return dlg
        except Exception:
            pass

        return None

    def _check_dialog_uiautomation(self):
        dlg = self._find_volume_dialog()

        if dlg:
            data = self._extract_dialog_fields(dlg)
            if data and data.get("base_mesh") != "N/D":
                self._cached_dialog_data = data
            self._window_was_open = True
        else:
            if self._window_was_open:
                debug_log("Janela de volume fechou.")
                if self._cached_dialog_data:
                    self._dispatch_event(self._cached_dialog_data)
                    self._cached_dialog_data = None
            self._window_was_open = False

    def _extract_dialog_fields(self, dialog) -> Optional[Dict[str, Any]]:
        try:
            combos = []
            edits = []

            def collect(ctrl, depth=0):
                if depth > 4:
                    return
                try:
                    children = ctrl.GetChildren()
                except Exception:
                    return

                for ch in children:
                    try:
                        ct = ch.ControlType
                        if ct == auto.ControlType.ComboBoxControl:
                            val = safe_get_text(ch)
                            combos.append((ch.Name or "", val))
                        elif ct == auto.ControlType.EditControl:
                            val = safe_get_text(ch)
                            edits.append((ch.Name or "", val))
                    except Exception:
                        pass
                    collect(ch, depth + 1)

            collect(dialog)

            # Classificação inteligente usando os objetos conhecidos do projeto
            polys = self.parser.get_polylines_summary() if self.parser else []
            planes = self.parser.get_planes_summary() if self.parser else []
            meshes = self.parser.get_meshes_summary() if self.parser else []

            data = {
                "base_mesh": "N/D",
                "reference_mesh": "N/D",
                "reference_plane": "N/D",
                "polyline": "N/D",
                "volume_name": "Volume001",
            }

            for _, val in combos:
                if not val:
                    continue
                if val in polys:
                    data["polyline"] = val
                elif val in planes:
                    data["reference_plane"] = val
                elif val in meshes:
                    if "primitiv" in val.lower():
                        data["reference_mesh"] = val
                    elif "smooth" in val.lower() or "vant" in val.lower():
                        data["base_mesh"] = val
                    elif data["base_mesh"] == "N/D":
                        data["base_mesh"] = val
                    elif data["reference_mesh"] == "N/D":
                        data["reference_mesh"] = val

            # Extração do nome do volume a partir dos edits (não numérico e não 'surface')
            for _, val in edits:
                if val and "surface" not in val.lower():
                    try:
                        float(val)
                    except ValueError:
                        data["volume_name"] = val
                        break

            debug_log(f"Campos identificados: {data}")
            return data
        except Exception as e:
            debug_log(f"Erro na extração: {e}")
            return None

    def _check_project_log(self):
        if not self._log_file or not os.path.exists(self._log_file):
            return

        try:
            cur_size = os.path.getsize(self._log_file)
            if cur_size > self._last_log_size:
                with open(self._log_file, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self._last_log_size)
                    new_text = f.read()
                self._last_log_size = cur_size

                if "calculate volume - finished" in new_text.lower():
                    debug_log("Gatilho imediato via project.log!")
                    event_data = self._cached_dialog_data or {
                        "base_mesh": "N/D",
                        "reference_mesh": "N/D",
                        "reference_plane": "N/D",
                        "polyline": "N/D",
                        "volume_name": "Volume001",
                    }
                    self._dispatch_event(event_data)
                    self._cached_dialog_data = None
        except Exception as e:
            debug_log(f"Erro log: {e}")

    def _check_project_rsp(self):
        if not self._rsp_file or not os.path.exists(self._rsp_file):
            return

        try:
            mtime = os.path.getmtime(self._rsp_file)
            if mtime > self._last_rsp_mtime:
                self._last_rsp_mtime = mtime
                debug_log("project.rsp salvo no disco (Ctrl+S)! Atualizando valores...")
                if self.on_rsp_update:
                    self.on_rsp_update()
        except Exception:
            pass

    def _dispatch_event(self, event_data: Dict[str, Any]):
        # Debounce de 1.0s para evitar evento duplicado entre fechar janela e log
        now = time.time()
        if now - self._last_dispatch_time < 1.0:
            return
        self._last_dispatch_time = now

        event_data["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        v_name = event_data.get("volume_name", "Volume001")

        # Verifica se os valores de Fill e Cut já estão no project.rsp
        all_vals = self.parser.get_all_volume_values() if self.parser else {}
        val_fill = None
        val_cut = None

        for k, v in all_vals.items():
            kl = k.lower()
            if v_name.lower() in kl:
                if "fill" in kl:
                    val_fill = v
                elif "cut" in kl:
                    val_cut = v

        # Envia linha de Fill
        rec_fill = dict(event_data)
        rec_fill["volume_name"] = f"{v_name}_Fill"
        rec_fill["volume_value"] = val_fill if val_fill is not None else 0.0
        if self.callback:
            self.callback(rec_fill)

        # Envia linha de Cut
        rec_cut = dict(event_data)
        rec_cut["volume_name"] = f"{v_name}_Cut"
        rec_cut["volume_value"] = val_cut if val_cut is not None else 0.0
        if self.callback:
            self.callback(rec_cut)
