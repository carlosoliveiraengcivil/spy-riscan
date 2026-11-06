# 🛡️ SPY RiSCAN — Auditor de Inventários Volumétricos

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com)
[![RiSCAN PRO](https://img.shields.io/badge/Target-RIEGL%20RiSCAN%20PRO-FF6B00?style=for-the-badge)](http://www.riegl.com/)
[![UI](https://img.shields.io/badge/Interface-CustomTkinter%20(Dark%20Mode)-0284C7?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)]()

> **Auditor autônomo em tempo real para cálculos volumétricos no RIEGL RiSCAN PRO**, garantindo integridade técnica, eliminação de erros humanos, rastreabilidade de parâmetros e exportação executiva em planilhas Excel.

Desenvolvido por **Carlos Oliveira**.

---

## 📌 Visão Geral

Em operações de mineração, terraplenagem, infraestrutura e topografia industrial, a conferência de volumes de pilhas e cavas através do **RIEGL RiSCAN PRO** é um processo crítico. No fluxo tradicional:
- O operador calcula dezenas de pilhas em lote;
- Parâmetros vitais (malha base, primitivo de referência, plano e polilinha) muitas vezes precisam ser conferidos ou anotados manualmente;
- Cálculos repetidos ou executados sobre a mesma polilinha podem gerar distorções severas no balanço de massa e inventário da empresa.

O **SPY RiSCAN** atua em segundo plano como uma "caixa-preta técnica": acompanha silenciosamente cada cálculo executado no RiSCAN PRO, intercepta os parâmetros exatos da janela, extrai o volume calculado ($m^3$) no arquivo do projeto, valida se há volumes repetidos e gera um relatório executivo pronto para auditoria técnica.

---

## ✨ Principais Funcionalidades

### 🎧 1. Interceptação em Segundo Plano (UI Automation)
- Monitora os eventos do Windows e detecta a abertura da janela `Calculate volume & surface area...` do RiSCAN PRO.
- Captura automaticamente:
  - **Nome do Volume** (ex: `PILHA_01_Fill`, `PILHA_01_Cut`)
  - **Malha Base** (*Base Mesh*, ex: `SMOOTH_01`)
  - **Malha Primitiva** (*Reference Mesh*, ex: `PRIMITIVO_SETEMBRO`)
  - **Plano de Referência** (*Reference Plane*, ex: `PlaneXY002`)
  - **Polilinha Delimitadora** (ex: `POLI_PILHA_01`)
  - **Data e Horário Exato** de cada cálculo.

### 🔍 2. Validador Inteligente de Duplicidades (Linha Vermelha)
- Detecta automaticamente se dois ou mais cálculos resultaram no **mesmo volume exato**.
- **Destaque Visual Instantâneo:** Toda linha duplicada fica com **fundo vermelho vibrante** (`#7f1d1d`) e ícone de alerta `⚠️`.
- **Status Dinâmico no Rodapé:**
  - `✅ Validador: Nenhum volume duplicado` (verde)
  - `⚠️ ATENÇÃO: X linha(s) com volumes repetidos detectadas!` (vermelho).
- Evita que medições repetidas ou duplicadas por distração passem desapercebidas para o relatório final.

### 📊 3. Exportação Executiva para Excel (`.xlsx`)
- Gera planilhas profissionais formatadas com paleta corporativa moderna.
- Metadados completos do projeto, operador e data de emissão.
- As duplicidades detectadas também são exportadas em destaque com preenchimento em vermelho suave e tipografia em destaque.
- Remoção de totalizadores genéricos para focar na rastreabilidade individual de cada medição.
- Modo de contingência automático: gera `.csv` formatado caso a máquina não possua a biblioteca Excel.

### 🔒 4. Blindagem Criptográfica por Hardware (HWID)
- Identificador exclusivo de hardware gerado a partir do `MachineGuid` criptografado da máquina.
- Validação por assinatura digital HMAC-SHA256 com chave mestra privada.
- Suporte a licenças temporárias (7 dias trial, 30 dias, 1 ano) e vitalícia.
- Armazenamento persistente no sistema operacional (`%APPDATA%\SPY_RiSCAN\license.lic`), permitindo atualizações do `.exe` sem perda de ativação.

### ⚡ 5. Standalone Portátil (.EXE)
- Empacotado em executável único com ícone 3D customizado.
- **Zero instalação:** não exige Python ou ferramentas externas na máquina do usuário final.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python 3.10+** | Linguagem central da aplicação |
| **CustomTkinter** | Interface gráfica moderna com suporte nativo a Dark Mode |
| **UIAutomation** | Interceptação e escuta de eventos da janela do RIEGL RiSCAN PRO |
| **OpenPyXL** | Criação e estilização corporativa de relatórios em Excel (`.xlsx`) |
| **HMAC & SHA-256** | Algoritmo criptográfico de mão única para validação de licenças |
| **PyInstaller** | Compilação em executável único e portátil para Windows |

---

## 🚀 Como Executar Localmente (Código-Fonte)

### Pré-requisitos
- Windows 10 ou 11
- Python 3.10 ou superior instalado e adicionado ao `PATH`

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/spy-riscan.git
cd spy-riscan
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Iniciar a aplicação
```bash
python main.py
```

---

## 📦 Como Compilar o Executável (.EXE)

Para compilar um novo executável portátil e autônomo:

Basta dar dois cliques no script:
```text
gerar_executavel.bat
```
Ou executar via terminal:
```bash
pyinstaller --noconfirm --onefile --windowed --name "SPY RiSCAN" --icon="app_icon.ico" --add-data="app_icon.ico;." --collect-all customtkinter --clean main.py
```
O executável final `SPY RiSCAN.exe` será gerado automaticamente na raiz da pasta.

---

## 📁 Estrutura do Repositório

```text
├── app_gui.py           # Interface Gráfica moderna (Dark Mode) e validação de duplicidades
├── riscan_listener.py   # Motor de captura e UI Automation do RIEGL RiSCAN PRO
├── project_parser.py    # Leitor e parser XML do arquivo project.rsp do RiSCAN
├── report_generator.py  # Gerador de relatórios executivos em Excel (.xlsx) e CSV
├── license_manager.py   # Gerenciador de licenças criptografadas e identificação por HWID
├── main.py              # Ponto de entrada da aplicação
├── requirements.txt     # Dependências do projeto Python
├── app_icon.ico         # Ícone 3D de alta definição
├── gerar_executavel.bat # Script de automação para compilação PyInstaller
├── README.md            # Documentação técnica completa
└── .gitignore           # Filtro de arquivos ignorados pelo Git
```

---

## 📋 Fluxo de Trabalho Recomendado

1. **Abra o RiSCAN PRO** com o seu projeto de escaneamento aberto.
2. **Abra o SPY RiSCAN**:
   - O aplicativo confirmará a escuta ativa (*"Aguardando cálculo no RiSCAN PRO..."*).
3. No RiSCAN PRO, execute normalmente os cálculos de volume de cada pilha/cava.
4. Ao clicar em **OK** no RiSCAN e salvar o projeto (`Ctrl + S`), o SPY RiSCAN captura automaticamente:
   - Malha base, primitivo, plano, polilinha e volume cúbico ($m^3$).
5. Se algum volume calculado for idêntico a outro já registrado, a linha ficará vermelha na hora com alerta visual.
6. Ao finalizar a área, clique em **📄 FINALIZAR E GERAR RELATÓRIO**.
7. Selecione onde deseja salvar e a planilha Excel será gerada e aberta imediatamente.

---

## 👤 Autor

Desenvolvido por **Carlos Oliveira**  
- **LinkedIn:** [linkedin.com/in/carlos-oliveira](https://www.linkedin.com)  
- **Foco:** Automação BIM, Engenharia de Infraestrutura, Rastreabilidade Técnica & Desenvolvimento de Ferramentas de Alta Performance.

---

## 📄 Licença

Este software é proprietário. Todos os direitos reservados. Para obter chaves de ativação ou autorização de uso comercial, entre em contato diretamente com o autor.
