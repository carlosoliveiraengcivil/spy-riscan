"""
SPY RiSCAN - Módulo de Gestão de Licenças e Proteção por Hardware ID (HWID)
Desenvolvido por Carlos Oliveira
"""

import os
import sys
import winreg
import hmac
import hashlib
from datetime import datetime, date
from typing import Tuple, Dict, Any, Optional

# Chave secreta mestra (criptografia de mão única)
SECRET_KEY = b"SPY_RISCAN_CARLOS_OLIVEIRA_2026_MASTER_SECRET_KEY_#$99"


def get_appdata_dir() -> str:
    """Retorna o diretório seguro em AppData para armazenar a licença."""
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    target = os.path.join(appdata, "SPY_RiSCAN")
    os.makedirs(target, exist_ok=True)
    return target


def get_license_file_path() -> str:
    return os.path.join(get_appdata_dir(), "license.lic")


def get_machine_id() -> str:
    """
    Gera um identificador único de hardware (HWID) baseado no MachineGuid do Windows.
    É imutável para a máquina e não depende de rede/IP.
    """
    guid = ""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
    except Exception:
        pass

    if not guid:
        # Fallback para nome do computador + processador
        guid = f"{os.environ.get('COMPUTERNAME', 'PC')}-{os.environ.get('PROCESSOR_IDENTIFIER', 'CPU')}"

    h = hashlib.sha256(guid.encode("utf-8")).hexdigest().upper()
    return f"SPY-{h[:4]}-{h[4:8]}-{h[8:12]}"


def generate_key(machine_id: str, plan: str, exp_date_str: str) -> str:
    """Gera a chave de ativação assinada criptograficamente."""
    payload = f"{machine_id.strip()}:{plan.strip()}:{exp_date_str.strip()}".encode("utf-8")
    sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest().upper()[:16]
    formatted_sig = f"{sig[:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"
    return f"KEY-{plan}-{exp_date_str}-{formatted_sig}"


def verify_key(machine_id: str, key_str: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verifica se a chave é matematicamente válida para este computador e se não está expirada.
    Retorna: (valida: bool, mensagem: str, dados_licenca: dict)
    """
    try:
        parts = key_str.strip().split("-")
        # Formato: KEY-PLANO-DATA-S1-S2-S3-S4 (7 partes)
        if len(parts) != 7 or parts[0] != "KEY":
            return False, "Formato de chave inválido.", {}

        plan = parts[1]
        exp_date_str = parts[2]
        sig_provided = "".join(parts[3:7])

        payload = f"{machine_id.strip()}:{plan}:{exp_date_str}".encode("utf-8")
        sig_expected = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest().upper()[:16]

        if sig_provided != sig_expected:
            return False, "Chave inválida para este computador.", {}

        # Verificação de expiração
        if plan != "LIFETIME":
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y%m%d").date()
                if date.today() > exp_date:
                    return False, f"Licença expirada em {exp_date.strftime('%d/%m/%Y')}.", {}
                days_left = (exp_date - date.today()).days
                msg = f"Licença válida ({plan}) até {exp_date.strftime('%d/%m/%Y')} ({days_left} dias restantes)."
            except Exception:
                return False, "Data de expiração corrompida.", {}
        else:
            msg = "Licença Vitalícia ativa!"

        return True, msg, {
            "plan": plan,
            "exp_date_str": exp_date_str,
            "key": key_str.strip()
        }
    except Exception as e:
        return False, f"Erro na validação: {e}", {}


def save_license(key_str: str) -> bool:
    """Salva a chave no arquivo local em AppData."""
    try:
        path = get_license_file_path()
        with open(path, "w", encoding="utf-8") as f:
            f.write(key_str.strip())
        return True
    except Exception:
        return False


def load_license() -> Tuple[bool, str, Dict[str, Any]]:
    """Carrega e valida a licença salva localmente."""
    path = get_license_file_path()
    if not os.path.exists(path):
        return False, "Nenhuma licença encontrada.", {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            key_str = f.read().strip()
        mid = get_machine_id()
        return verify_key(mid, key_str)
    except Exception as e:
        return False, f"Erro ao ler licença: {e}", {}


def revoke_license() -> bool:
    """Remove a licença salva localmente."""
    try:
        path = get_license_file_path()
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False
