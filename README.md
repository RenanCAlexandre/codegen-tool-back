
# CodegenTool — Captura e Conversão de Códigos HTML/CSS

O **CodegenTool** é uma ferramenta que permite **capturar elementos de qualquer página web** (exceto do próprio domínio da aplicação), extrair seu **HTML**, **estilos CSS** e contexto do DOM, e convertê-los automaticamente para três formatos:

- **Código base (HTML + CSS)**
- **Versão com Bootstrap**
- **Versão com Tailwind CSS**

A captura é feita via **extensão do Google Chrome (Manifest V3)** que se comunica com o **backend Python** através de uma API REST.

---

## 📌 Objetivo

O projeto foi criado para ajudar desenvolvedores front-end a:

- Analisar rapidamente elementos de páginas.
- Obter código limpo e pronto para uso.
- Converter entre diferentes padrões de estilização.
- Estudar e prototipar componentes visualmente.

---

## 🏗 Estrutura do Projeto

```

codegen-tool/
├── app/
│   ├── converters/              # Conversores de código
│   │   ├── base\_generator.py
│   │   ├── bootstrap\_generator.py
│   │   ├── tailwind\_generator.py
│   ├── static/                  # Arquivos estáticos (JS/CSS)
│   │   └── js/
│   │       └── detector.js
│   ├── templates/               # Templates HTML (Frontend da aplicação)
│   │   └── index.html
│   ├── main.py                   # Backend Flask
├── requirements.txt              # Dependências Python
├── README.md

```

A **extensão do Chrome** fica em um diretório separado, [https://gitlab.com/valcedir2/codegen-tool-chrome-extension](https://github.com/RenanCAlexandre/codegen-tool-extension)

---

## 🔌 Funcionamento

1. **Usuário liga a captura no popup da extensão.**
2. Ao clicar em qualquer elemento da página (fora do domínio do CodegenTool):
   - O **content script** coleta:
     - `outerHTML` do elemento
     - Estilos CSS aplicados
     - Seletor CSS único
   - Os dados são enviados para o backend Python via API `/api/convert`.
3. O backend:
   - Processa o HTML/CSS capturado.
   - Gera a versão base, versão Bootstrap e versão Tailwind.
   - Armazena em memória.
4. O frontend do CodegenTool (`index.html`):
   - Consulta periodicamente `/api/latest-code`.
   - Atualiza a interface com os três blocos de código, prontos para copiar.

---

## 📦 Instalação

### 1. Clonar o repositório
```bash
git clone URL_DO_REPOSITORIO
cd codegen-tool
````

### 2. Criar ambiente virtual e instalar dependências

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

---

## 🚀 Executando o Backend

```bash
python main.py
```

O backend iniciará (por padrão) em:

```
http://127.0.0.1:5000
```

---

## 🌐 Configurando a Extensão do Chrome

1. Abra o **Google Chrome** e vá em:
   `chrome://extensions/`
2. Ative o **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação**.
4. Selecione a pasta `chrome-extension/` do projeto.
5. No popup da extensão:

   * Configure a **URL do backend** (ex.: `http://127.0.0.1:5000`).
   * Ative a captura.

---

## 💻 Usando a Ferramenta

1. Inicie o backend Python.
2. Carregue a extensão no Chrome.
3. Ative a captura e clique em qualquer elemento de uma página web (não no CodegenTool).
4. Abra a página do **CodegenTool** (`http://127.0.0.1:5000`) para visualizar:

   * Código base (HTML + CSS)
   * Código com Bootstrap
   * Código com Tailwind
5. Use o botão **"Copiar"** para copiar qualquer versão do código.

---

## 🛠 Tecnologias Utilizadas

* **Backend:** Python + Flask
* **Frontend:** HTML + Tailwind CSS + highlight.js
* **Extensão:** Google Chrome (Manifest V3)
* **Comunicação:** API REST (JSON) via `fetch`

---

## 📄 Licença

Este projeto é de uso livre para fins educacionais e prototipagem.
