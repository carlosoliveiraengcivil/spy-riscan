"""
SPY RiSCAN - Auditor de Inventários Volumétricos
Interface Gráfica Principal
Desenvolvido por Carlos Oliveira
"""

import os
import sys
import webbrowser
from datetime import datetime
from typing import List, Dict, Any, Optional

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    USE_CTK = True
except ImportError:
    import tkinter as ctk
    USE_CTK = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from project_parser import RiSCANProjectParser
from riscan_listener import RiSCANVolumeListener
from report_generator import VolumeReportGenerator
import license_manager

# Configurar AppUserModelID para o Windows exibir o ícone correto na barra de tarefas
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("carlosoliveira.spyriscan.auditor.1.0")
except Exception:
    pass

LINKEDIN_URL = "https://www.linkedin.com/in/carlos-oliveira-038919259"


class SpyRiSCANApp:
    def __init__(self):
        if USE_CTK:
            self.root = ctk.CTk()
            self.root.geometry("1140x720")
            self.root.minsize(1000, 600)
        else:
            self.root = tk.Tk()
            self.root.geometry("1140x720")
            self.root.configure(bg="#0f172a")

        self.root.title("SPY RiSCAN - Auditor de Inventários Volumétricos")

        # Estado
        self.base_dir = get_base_dir()
        self.reports_dir = os.path.join(self.base_dir, "Relatorios")
        os.makedirs(self.reports_dir, exist_ok=True)

        # Definir ícone da janela
        for ico in [os.path.join(self.base_dir, "app_icon.ico"), os.path.join(getattr(sys, '_MEIPASS', ''), "app_icon.ico")]:
            if os.path.exists(ico):
                try:
                    self.root.iconbitmap(ico)
                    break
                except Exception:
                    pass

        self.project_path = ""
        self.parser: Optional[RiSCANProjectParser] = None
        self.listener: Optional[RiSCANVolumeListener] = None
        self.records: List[Dict[str, Any]] = []
        self.auditor_active = False
        self.license_info: Dict[str, Any] = {}

        # Verificação da licença de uso
        is_valid, msg, lic_data = license_manager.load_license()
        if is_valid:
            self.license_info = lic_data
            self._build_ui()
        else:
            self._build_activation_ui(msg)

    # ────────────────────────── TELA DE ATIVAÇÃO ──────────────────────────

    def _build_activation_ui(self, initial_msg: str = ""):
        for w in self.root.winfo_children():
            w.destroy()

        self.root.geometry("620x520")
        self.root.resizable(False, False)

        container = ctk.CTkFrame(self.root, fg_color="#0f172a", corner_radius=0) if USE_CTK else tk.Frame(self.root, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        card = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=12) if USE_CTK else tk.Frame(container, bg="#1e293b")
        card.pack(fill="both", expand=True, padx=8, pady=8)

        # Topo
        if USE_CTK:
            ctk.CTkLabel(card, text="🔒  SPY RiSCAN", font=("Segoe UI", 22, "bold"), text_color="#38bdf8").pack(pady=(18, 2))
            ctk.CTkLabel(card, text="Ativação de Licença Obrigatória", font=("Segoe UI", 13, "bold"), text_color="#f8fafc").pack()
            ctk.CTkLabel(card, text="Este software é protegido e necessita de uma chave vinculada a este computador.", font=("Segoe UI", 10), text_color="#94a3b8").pack(pady=(2, 12))
        else:
            tk.Label(card, text="🔒  SPY RiSCAN - Ativação", font=("Segoe UI", 16, "bold"), fg="#38bdf8", bg="#1e293b").pack(pady=10)

        # ID da Máquina
        mid = license_manager.get_machine_id()
        mid_box = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8) if USE_CTK else tk.Frame(card, bg="#0f172a")
        mid_box.pack(fill="x", padx=25, pady=6)

        if USE_CTK:
            ctk.CTkLabel(mid_box, text="ID deste Computador:", font=("Segoe UI", 10, "bold"), text_color="#cbd5e1").pack(anchor="w", padx=12, pady=(8, 2))
        else:
            tk.Label(mid_box, text="ID deste Computador:", fg="#cbd5e1", bg="#0f172a").pack(anchor="w", padx=12, pady=(6, 2))

        row_mid = ctk.CTkFrame(mid_box, fg_color="transparent") if USE_CTK else tk.Frame(mid_box, bg="#0f172a")
        row_mid.pack(fill="x", padx=12, pady=(0, 10))

        txt_mid = ctk.CTkEntry(row_mid, font=("Segoe UI", 12, "bold"), fg_color="#1e293b") if USE_CTK else tk.Entry(row_mid, font=("Segoe UI", 11, "bold"))
        txt_mid.insert(0, mid)
        txt_mid.configure(state="readonly")
        txt_mid.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def copy_mid():
            self.root.clipboard_clear()
            self.root.clipboard_append(mid)
            messagebox.showinfo("Copiado!", f"ID do computador copiado:\n{mid}\n\nEnvie este código para Carlos Oliveira.")

        btn_copy = ctk.CTkButton(row_mid, text="📋 Copiar ID", width=105, height=32, command=copy_mid, fg_color="#334155", hover_color="#475569") if USE_CTK else tk.Button(row_mid, text="Copiar", command=copy_mid)
        btn_copy.pack(side="right")

        msg_hint = "Envie o ID acima para Carlos Oliveira para receber sua chave."
        if USE_CTK:
            ctk.CTkLabel(card, text=f"💡 {msg_hint}", font=("Segoe UI", 10, "italic"), text_color="#38bdf8").pack(pady=(2, 8))
        else:
            tk.Label(card, text=msg_hint, fg="#38bdf8", bg="#1e293b", font=("Segoe UI", 9)).pack(pady=4)

        # Campo da Chave
        key_box = ctk.CTkFrame(card, fg_color="transparent") if USE_CTK else tk.Frame(card, bg="#1e293b")
        key_box.pack(fill="x", padx=25, pady=4)

        if USE_CTK:
            ctk.CTkLabel(key_box, text="Chave de Ativação:", font=("Segoe UI", 11, "bold"), text_color="#cbd5e1").pack(anchor="w", pady=(0, 4))
        else:
            tk.Label(key_box, text="Chave de Ativação:", fg="#cbd5e1", bg="#1e293b").pack(anchor="w")

        txt_key = ctk.CTkEntry(key_box, placeholder_text="Cole sua chave aqui (ex: KEY-7D-...)", font=("Segoe UI", 11)) if USE_CTK else tk.Entry(key_box, font=("Segoe UI", 10))
        txt_key.pack(fill="x")

        lbl_feedback = ctk.CTkLabel(card, text=initial_msg if initial_msg and "Nenhuma" not in initial_msg else "", font=("Segoe UI", 10), text_color="#f87171") if USE_CTK else tk.Label(card, text="", fg="#f87171", bg="#1e293b")
        lbl_feedback.pack(pady=4)

        def do_activate():
            entered = txt_key.get().strip()
            if not entered:
                lbl_feedback.configure(text="Digite ou cole a chave de ativação.")
                return
            ok, vmsg, lic_data = license_manager.verify_key(mid, entered)
            if ok:
                license_manager.save_license(entered)
                self.license_info = lic_data
                messagebox.showinfo("Ativação Concluída", f"✅ Software ativado com sucesso!\n\n{vmsg}")
                for child in self.root.winfo_children():
                    child.destroy()
                self.root.geometry("1140x720")
                self.root.resizable(True, True)
                self._build_ui()
            else:
                lbl_feedback.configure(text=f"❌ {vmsg}")
                messagebox.showerror("Chave Inválida", f"Não foi possível ativar:\n\n{vmsg}")

        btn_activate = ctk.CTkButton(card, text="🔓  ATIVAR SOFTWARE", font=("Segoe UI", 13, "bold"), height=42, fg_color="#059669", hover_color="#047857", command=do_activate) if USE_CTK else tk.Button(card, text="ATIVAR SOFTWARE", command=do_activate)
        btn_activate.pack(fill="x", padx=25, pady=(8, 12))

    # ────────────────────────── UI PRINCIPAL ──────────────────────────

    def _build_ui(self):
        # ═══ HEADER ═══
        header = ctk.CTkFrame(self.root, fg_color="#0f172a", corner_radius=0) if USE_CTK else tk.Frame(self.root, bg="#0f172a")
        header.pack(fill="x")

        title_box = ctk.CTkFrame(header, fg_color="transparent") if USE_CTK else tk.Frame(header, bg="#0f172a")
        title_box.pack(side="left", padx=25, pady=12)

        if USE_CTK:
            ctk.CTkLabel(title_box, text="🕵️  SPY RiSCAN", font=("Segoe UI", 22, "bold"), text_color="#38bdf8").pack(anchor="w")
        else:
            tk.Label(title_box, text="🕵️  SPY RiSCAN", font=("Segoe UI", 18, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w")

        # Subtítulo com link clicável
        sub_frame = ctk.CTkFrame(title_box, fg_color="transparent") if USE_CTK else tk.Frame(title_box, bg="#0f172a")
        sub_frame.pack(anchor="w")

        if USE_CTK:
            ctk.CTkLabel(sub_frame, text="Auditor de inventários volumétricos  |  ", font=("Segoe UI", 11), text_color="#94a3b8").pack(side="left")
        else:
            tk.Label(sub_frame, text="Auditor de inventários volumétricos  |  ", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a").pack(side="left")

        link_lbl = tk.Label(sub_frame, text="Desenvolvido por Carlos Oliveira", font=("Segoe UI", 9, "underline"), fg="#60a5fa", bg="#0f172a", cursor="hand2")
        link_lbl.pack(side="left")
        link_lbl.bind("<Button-1>", lambda e: webbrowser.open(LINKEDIN_URL))

        # Badges do Topo Direito (Status do Auditor + Badge da Licença)
        top_right = ctk.CTkFrame(header, fg_color="transparent") if USE_CTK else tk.Frame(header, bg="#0f172a")
        top_right.pack(side="right", padx=25, pady=12)

        self.status_badge = ctk.CTkLabel(
            top_right, text="  🔴  AUDITOR DESABILITADO  ",
            fg_color="#7f1d1d", text_color="#fca5a5", corner_radius=8,
            font=("Segoe UI", 12, "bold"), padx=14, pady=6
        ) if USE_CTK else tk.Label(
            top_right, text="  🔴  AUDITOR DESABILITADO  ",
            fg="#fca5a5", bg="#7f1d1d", font=("Segoe UI", 10, "bold"), padx=10, pady=4
        )
        self.status_badge.pack(side="right")

        # Badge com o tipo e validade da licença
        plan = self.license_info.get("plan", "LIFETIME")
        exp_date_str = self.license_info.get("exp_date_str", "")
        if plan == "LIFETIME":
            lic_lbl_txt = "🛡️ Vitalícia"
        else:
            try:
                exp_fmt = datetime.strptime(exp_date_str, "%Y%m%d").strftime("%d/%m/%Y")
                lic_lbl_txt = f"🛡️ {plan} (até {exp_fmt})"
            except Exception:
                lic_lbl_txt = f"🛡️ {plan}"

        self.lic_badge = ctk.CTkLabel(
            top_right, text=f"  {lic_lbl_txt}  ",
            fg_color="#064e3b", text_color="#34d399", corner_radius=8,
            font=("Segoe UI", 11, "bold"), padx=10, pady=6
        ) if USE_CTK else tk.Label(
            top_right, text=f"  {lic_lbl_txt}  ",
            fg="#34d399", bg="#064e3b", font=("Segoe UI", 9, "bold"), padx=8, pady=4
        )
        self.lic_badge.pack(side="right", padx=(0, 10))

        sep = ctk.CTkFrame(self.root, fg_color="#1e293b", height=2, corner_radius=0) if USE_CTK else tk.Frame(self.root, bg="#1e293b", height=2)
        sep.pack(fill="x")

        # ═══ CONFIGURAÇÃO ═══
        cfg = ctk.CTkFrame(self.root, fg_color="#0f172a") if USE_CTK else tk.Frame(self.root, bg="#0f172a")
        cfg.pack(fill="x", padx=25, pady=(10, 4))

        # Projeto .RiSCAN
        p_row = ctk.CTkFrame(cfg, fg_color="transparent") if USE_CTK else tk.Frame(cfg, bg="#0f172a")
        p_row.pack(fill="x", pady=3)

        if USE_CTK:
            ctk.CTkLabel(p_row, text="Projeto RiSCAN:", font=("Segoe UI", 11, "bold"), text_color="#cbd5e1", width=140).pack(side="left")
        else:
            tk.Label(p_row, text="Projeto RiSCAN:", font=("Segoe UI", 10, "bold"), fg="#cbd5e1", bg="#0f172a", width=16, anchor="w").pack(side="left")

        self.txt_project = ctk.CTkEntry(p_row, placeholder_text="Selecione a pasta do projeto .RiSCAN...", font=("Segoe UI", 11)) if USE_CTK else tk.Entry(p_row, font=("Segoe UI", 10))
        self.txt_project.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse = ctk.CTkButton(p_row, text="📂 Selecionar", width=110, command=self._browse_project, fg_color="#0284c7", hover_color="#0369a1") if USE_CTK else tk.Button(p_row, text="Selecionar", command=self._browse_project)
        btn_browse.pack(side="left")

        # Responsável Técnico
        op_row = ctk.CTkFrame(cfg, fg_color="transparent") if USE_CTK else tk.Frame(cfg, bg="#0f172a")
        op_row.pack(fill="x", pady=3)

        if USE_CTK:
            ctk.CTkLabel(op_row, text="Responsável Técnico:", font=("Segoe UI", 11, "bold"), text_color="#cbd5e1", width=140).pack(side="left")
        else:
            tk.Label(op_row, text="Responsável Técnico:", font=("Segoe UI", 10, "bold"), fg="#cbd5e1", bg="#0f172a", width=16, anchor="w").pack(side="left")

        self.txt_operator = ctk.CTkEntry(op_row, width=250, font=("Segoe UI", 11)) if USE_CTK else tk.Entry(op_row, width=30, font=("Segoe UI", 10))
        try:
            self.txt_operator.insert(0, os.getlogin())
        except Exception:
            self.txt_operator.insert(0, "Projetista")
        self.txt_operator.pack(side="left", padx=(0, 8))

        # ═══ CONTROLES ═══
        ctrl = ctk.CTkFrame(self.root, fg_color="transparent") if USE_CTK else tk.Frame(self.root, bg="#0f172a")
        ctrl.pack(fill="x", padx=25, pady=(8, 6))

        self.btn_toggle = ctk.CTkButton(
            ctrl, text="▶  INICIAR AUDITOR", width=180, height=36,
            font=("Segoe UI", 12, "bold"), fg_color="#0284c7", hover_color="#0369a1",
            command=self._toggle_auditor
        ) if USE_CTK else tk.Button(ctrl, text="INICIAR AUDITOR", font=("Segoe UI", 10, "bold"), command=self._toggle_auditor)
        self.btn_toggle.pack(side="left")

        btn_sync = ctk.CTkButton(
            ctrl, text="🔄 Sincronizar Volumes (Ctrl+S)", width=220, height=36,
            font=("Segoe UI", 11), fg_color="#1e293b", hover_color="#334155",
            command=self._sync_values_now
        ) if USE_CTK else tk.Button(ctrl, text="Sincronizar (Ctrl+S)", command=self._sync_values_now)
        btn_sync.pack(side="left", padx=(10, 0))

        btn_del_row = ctk.CTkButton(
            ctrl, text="✖ Remover Linha", width=150, height=36,
            font=("Segoe UI", 11), fg_color="#334155", hover_color="#475569",
            command=self._delete_selected_row
        ) if USE_CTK else tk.Button(ctrl, text="Remover Linha", command=self._delete_selected_row)
        btn_del_row.pack(side="left", padx=(10, 0))

        btn_clear = ctk.CTkButton(
            ctrl, text="🗑️  Limpar Tabela", width=130, height=36,
            font=("Segoe UI", 11), fg_color="#991b1b", hover_color="#b91c1c",
            command=self._clear_session
        ) if USE_CTK else tk.Button(ctrl, text="Limpar Tudo", command=self._clear_session)
        btn_clear.pack(side="right")

        # ═══ TABELA ═══
        table_frame = ctk.CTkFrame(self.root, fg_color="#1e293b", corner_radius=8) if USE_CTK else tk.Frame(self.root, bg="#1e293b")
        table_frame.pack(fill="both", expand=True, padx=25, pady=4)

        cols = ("item", "nome", "base_mesh", "primitivo", "plano", "polyline", "volume", "hora")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#0f172a", foreground="#f8fafc",
                        fieldbackground="#0f172a", rowheight=30,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#1e293b", foreground="#38bdf8",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[('selected', '#0284c7')])

        # Configuração de cor para destacar linhas duplicadas em vermelho
        self.tree.tag_configure("duplicate", background="#7f1d1d", foreground="#ffffff")
        self.tree.tag_configure("normal", background="#0f172a", foreground="#f8fafc")

        self.tree.heading("item", text="#")
        self.tree.heading("nome", text="Nome Volume")
        self.tree.heading("base_mesh", text="Base Mesh (Nuvem/Smooth)")
        self.tree.heading("primitivo", text="Primitivo (Ref. Mesh)")
        self.tree.heading("plano", text="Plano de Referência")
        self.tree.heading("polyline", text="Polilinha")
        self.tree.heading("volume", text="Volume [m³]")
        self.tree.heading("hora", text="Horário")

        self.tree.column("item", width=40, anchor="center")
        self.tree.column("nome", width=150, anchor="w")
        self.tree.column("base_mesh", width=200, anchor="w")
        self.tree.column("primitivo", width=200, anchor="w")
        self.tree.column("plano", width=120, anchor="center")
        self.tree.column("polyline", width=120, anchor="center")
        self.tree.column("volume", width=140, anchor="e")
        self.tree.column("hora", width=110, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll.pack(side="right", fill="y", pady=8)

        self.tree.bind("<Delete>", lambda e: self._delete_selected_row())
        self.tree.bind("<Double-1>", self._on_item_double_click)

        # ═══ RODAPÉ ═══
        bottom = ctk.CTkFrame(self.root, fg_color="#1e293b", corner_radius=0) if USE_CTK else tk.Frame(self.root, bg="#1e293b")
        bottom.pack(fill="x")

        summary_box = ctk.CTkFrame(bottom, fg_color="transparent") if USE_CTK else tk.Frame(bottom, bg="#1e293b")
        summary_box.pack(side="left", padx=25, pady=10)

        self.lbl_count = ctk.CTkLabel(summary_box, text="Registros: 0", font=("Segoe UI", 12, "bold"), text_color="#f8fafc") if USE_CTK else tk.Label(summary_box, text="Registros: 0", fg="#f8fafc", bg="#1e293b")
        self.lbl_count.pack(anchor="w")

        self.lbl_status = ctk.CTkLabel(summary_box, text="✅ Validador: Nenhum volume duplicado", font=("Segoe UI", 12, "bold"), text_color="#34d399") if USE_CTK else tk.Label(summary_box, text="Validador: OK", fg="#34d399", bg="#1e293b")
        self.lbl_status.pack(anchor="w", pady=(2, 0))

        btn_export = ctk.CTkButton(
            bottom, text="📄  FINALIZAR E GERAR RELATÓRIO", height=42,
            font=("Segoe UI", 12, "bold"), fg_color="#059669", hover_color="#047857",
            command=self._finalize_and_export
        ) if USE_CTK else tk.Button(bottom, text="GERAR RELATÓRIO", command=self._finalize_and_export)
        btn_export.pack(side="right", padx=25, pady=10)

    # ────────────────────────── LÓGICA ──────────────────────────

    def _browse_project(self):
        folder = filedialog.askdirectory(title="Selecione o diretório do projeto (.RiSCAN)")
        if folder:
            self.project_path = folder
            self.txt_project.delete(0, tk.END)
            self.txt_project.insert(0, folder)
            self.parser = RiSCANProjectParser(folder)

            if not self.auditor_active:
                self._toggle_auditor()
            elif self.listener:
                self.listener.set_project(folder)

    def _toggle_auditor(self):
        if not self.auditor_active:
            if not self.project_path:
                messagebox.showwarning("Projeto não selecionado", "Selecione a pasta do projeto .RiSCAN antes de iniciar o auditor.")
                return

            self.listener = RiSCANVolumeListener(
                on_calculation_callback=self._on_calc_detected,
                on_rsp_update_callback=self._on_rsp_file_updated,
                project_path=self.project_path
            )
            self.listener.start()
            self.auditor_active = True

            if USE_CTK:
                self.btn_toggle.configure(text="⏹  PARAR AUDITOR", fg_color="#b91c1c", hover_color="#991b1b")
                self.status_badge.configure(text="  🟢  AUDITOR ATIVO  ", fg_color="#065f46", text_color="#34d399")
            else:
                self.btn_toggle.configure(text="PARAR AUDITOR")
                self.status_badge.configure(text="  🟢  AUDITOR ATIVO  ", bg="#065f46", fg="#34d399")
        else:
            if self.listener:
                self.listener.stop()
                self.listener = None
            self.auditor_active = False

            if USE_CTK:
                self.btn_toggle.configure(text="▶  INICIAR AUDITOR", fg_color="#0284c7", hover_color="#0369a1")
                self.status_badge.configure(text="  🔴  AUDITOR DESABILITADO  ", fg_color="#7f1d1d", text_color="#fca5a5")
            else:
                self.btn_toggle.configure(text="INICIAR AUDITOR")
                self.status_badge.configure(text="  🔴  AUDITOR DESABILITADO  ", bg="#7f1d1d", fg="#fca5a5")

    def _on_calc_detected(self, event_data: Dict[str, Any]):
        self.root.after(50, lambda: self._process_event(event_data))

    def _on_rsp_file_updated(self):
        self.root.after(50, self._sync_values_now)

    def _sync_values_now(self):
        """Recarrega os volumes salvos no project.rsp e atualiza linhas existentes."""
        if not self.parser:
            return

        all_vals = self.parser.get_all_volume_values()
        updated = False

        for r in self.records:
            v_name = r.get("volume_name", "")
            for k, v in all_vals.items():
                if v_name.lower() in k.lower() or k.lower() in v_name.lower():
                    if r.get("volume_value") != v:
                        r["volume_value"] = v
                        updated = True
                    break

        if updated:
            self._refresh_table()

    def _process_event(self, event_data: Dict[str, Any]):
        self.records.append(event_data)
        self._sync_values_now()
        self._refresh_table()

    def _on_item_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self.records):
            return
        record = self.records[idx]

        d = ctk.CTkToplevel(self.root) if USE_CTK else tk.Toplevel(self.root)
        d.title(f"Ajustar #{idx + 1}")
        d.geometry("400x250")
        d.grab_set()

        ctk.CTkLabel(d, text=f"Editar Registro #{idx + 1}", font=("Segoe UI", 12, "bold"), text_color="#38bdf8").pack(pady=(15, 10))

        f1 = ctk.CTkFrame(d, fg_color="transparent") if USE_CTK else tk.Frame(d)
        f1.pack(fill="x", padx=25, pady=4)
        ctk.CTkLabel(f1, text="Nome:", width=100, anchor="w").pack(side="left")
        e_name = ctk.CTkEntry(f1) if USE_CTK else tk.Entry(f1)
        e_name.insert(0, record.get("volume_name", ""))
        e_name.pack(side="right", fill="x", expand=True)

        f2 = ctk.CTkFrame(d, fg_color="transparent") if USE_CTK else tk.Frame(d)
        f2.pack(fill="x", padx=25, pady=4)
        ctk.CTkLabel(f2, text="Volume [m³]:", width=100, anchor="w").pack(side="left")
        e_vol = ctk.CTkEntry(f2) if USE_CTK else tk.Entry(f2)
        cur_v = record.get("volume_value")
        e_vol.insert(0, str(cur_v) if isinstance(cur_v, (int, float)) and cur_v > 0 else "")
        e_vol.pack(side="right", fill="x", expand=True)

        def save():
            record["volume_name"] = e_name.get()
            try:
                record["volume_value"] = float(e_vol.get().replace(".", "").replace(",", "."))
            except ValueError:
                pass
            self._refresh_table()
            d.destroy()

        ctk.CTkButton(d, text="Salvar", fg_color="#0284c7", command=save).pack(pady=15)

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Mapeamento para identificar volumes com valores idênticos (duplicados)
        vol_counts = {}
        for r in self.records:
            vol = r.get("volume_value")
            if isinstance(vol, (int, float)) and vol > 0:
                rounded = round(float(vol), 2)
                vol_counts[rounded] = vol_counts.get(rounded, 0) + 1

        dup_count = 0
        for idx, r in enumerate(self.records, start=1):
            vol = r.get("volume_value")
            is_dup = False
            if isinstance(vol, (int, float)) and vol > 0:
                rounded = round(float(vol), 2)
                if vol_counts.get(rounded, 0) > 1:
                    is_dup = True
                    dup_count += 1
                vol_str = f"{vol:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                vol_str = "Aguardando Ctrl+S..."

            tag = "duplicate" if is_dup else "normal"
            item_id = f"⚠️ {idx:02d}" if is_dup else f"{idx:02d}"
            disp_vol = f"⚠️ {vol_str}" if is_dup else vol_str

            self.tree.insert("", "end", iid=str(idx - 1), values=(
                item_id,
                r.get("volume_name", ""),
                r.get("base_mesh", ""),
                r.get("reference_mesh", ""),
                r.get("reference_plane", ""),
                r.get("polyline", ""),
                disp_vol,
                r.get("timestamp", "")
            ), tags=(tag,))

        self.lbl_count.configure(text=f"Total de Registros: {len(self.records)}")
        if dup_count > 0:
            self.lbl_status.configure(
                text=f"⚠️ ATENÇÃO: {dup_count} linha(s) com volumes repetidos detectadas!",
                text_color="#f87171"
            )
        else:
            self.lbl_status.configure(
                text="✅ Validador: Nenhum volume duplicado",
                text_color="#34d399"
            )

    def _delete_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nenhum item selecionado", "Clique em uma linha da tabela para selecioná-la antes de remover.")
            return
        idx = int(sel[0])
        if idx < len(self.records):
            del self.records[idx]
            self._refresh_table()

    def _clear_session(self):
        if self.records and not messagebox.askyesno("Limpar tudo", "Deseja limpar todos os registros da sessão?"):
            return
        self.records.clear()
        self._refresh_table()

    def _reset_for_new_cycle(self):
        if self.auditor_active:
            self._toggle_auditor()

        self.records.clear()
        self._refresh_table()

        self.project_path = ""
        self.parser = None
        self.txt_project.delete(0, tk.END)

    def _finalize_and_export(self):
        if not self.records:
            messagebox.showwarning("Sem registros", "Não há cálculos registrados para gerar o relatório.")
            return

        proj_name = self.parser.project_name if self.parser else "Projeto_RiSCAN"
        op_name = self.txt_operator.get() or "Projetista"

        default_name = f"SPY_RiSCAN_{proj_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        initial_dir = self.project_path if self.project_path else self.base_dir

        save_path = filedialog.asksaveasfilename(
            title="Salvar Relatório de Auditoria",
            initialdir=initial_dir,
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[
                ("Planilha Excel (*.xlsx)", "*.xlsx"),
                ("Arquivo CSV (*.csv)", "*.csv"),
                ("Todos os Arquivos (*.*)", "*.*")
            ]
        )

        if not save_path:
            return

        gen = VolumeReportGenerator(project_name=proj_name, operator_name=op_name)

        if save_path.lower().endswith(".csv"):
            success = gen._generate_csv_fallback(self.records, save_path)
        else:
            success = gen.generate_excel_report(self.records, save_path)

        if success and os.path.exists(save_path):
            open_now = messagebox.askyesno(
                "Relatório Salvo com Sucesso!",
                f"Relatório de auditoria salvo em:\n{save_path}\n\n"
                f"Projeto: {proj_name}\n"
                f"Total de Registros: {len(self.records)}\n\n"
                f"Deseja abrir a planilha agora?"
            )
            if open_now:
                try:
                    os.startfile(save_path)
                except Exception:
                    pass
            self._reset_for_new_cycle()
        else:
            messagebox.showerror("Erro", "Não foi possível salvar o arquivo de relatório.")

    def run(self):
        self.root.mainloop()
        if self.listener:
            self.listener.stop()


if __name__ == "__main__":
    app = SpyRiSCANApp()
    app.run()
