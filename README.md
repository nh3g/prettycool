# PrettyCool Control Center

PrettyCool é a plataforma modular da Unidade 37 para automação de atividades de reconhecimento ofensivo. Esta versão moderniza
completamente o projeto original, mantendo a estrutura de módulos independentes e adicionando uma interface web corporativa,
além de um modo console inspirado no comportamento CLI legado. Todo o armazenamento local é feito em arquivos (sem banco de
dados) e os relatórios são gerados em Markdown dentro da pasta `reports/`.

## Principais capacidades

- Interface web responsiva com tema escuro seguindo a identidade visual da Unidade 37.
- Execução individual de módulos, execução em lote ou execução completa do pipeline.
- Painel de configuração de API keys persistidas em `config/settings.json`.
- Modo console com os mesmos comandos do terminal (`run module`, `run bundle`, `run all`, `list modules`).
- Geração automática de relatórios estruturados (`reports/<timestamp>_<target>_<modo>.md`).
- CLI (`python cli.py`) para operadores que preferirem terminal puro.

## Pré-requisitos

- Python 3.10 ou superior.
- Ambiente virtual (recomendado).
- Chaves de API válidas para cada integração desejada (WhoisFreaks, Censys, Shodan, SecurityTrails, VirusTotal, Spyse, GrayHat,
etc.).

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

Crie o arquivo de configuração inicial (é gerado automaticamente na primeira execução, mas pode ser criado manualmente):

```bash
python -c "from app.config import settings_manager; print(settings_manager.settings)"
```

## Executando o servidor web

```bash
uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000/` no navegador. Insira o domínio alvo, configure as chaves e execute os módulos conforme necessário.
Os relatórios em Markdown serão gravados na pasta `reports/`.

## Utilizando a CLI

```bash
python cli.py list                # Lista módulos disponíveis
python cli.py run --target alvo.com --modules shodan censys
python cli.py run --target alvo.com --mode bundle --category Discovery
python cli.py run --target alvo.com --mode all
python cli.py console "run module shodan --target alvo.com"
```

## Estrutura dos módulos implementados

| Módulo | Categoria | Origem |
|--------|-----------|--------|
| `whoisfreaks` | Discovery | WhoisFreaks v1.0 |
| `certspotter` | Discovery | CertSpotter v1 |
| `dnsbuffer` | Discovery | BufferOver DNS |
| `securitytrails` | Discovery | SecurityTrails v1 |
| `censys` | Discovery | Censys API v2 |
| `shodan` | Discovery | Shodan REST API |
| `virustotal` | Discovery | VirusTotal v3 |
| `spyse` | Discovery | Spyse v4 |
| `grayhat` | Intelligence | GrayHat Warfare Buckets |
| `psbdmp` | Intelligence | PSBDMP (pastebin dumps) |
| `wayback` | Intelligence | Internet Archive Wayback |
| `masscan` | Active | Binary local do masscan |

> **Observação:** o módulo `masscan` exige que o binário esteja disponível no PATH do servidor. Caso contrário o módulo indicará o
erro correspondente.

## Configuração de API keys

As chaves podem ser informadas via interface web (painel “Configuração de API Keys”) ou manualmente editando `config/settings.json`.
Cada chave é opcional, porém módulos que exigem autenticação não serão executados até que a credencial esteja presente.

## Geração de relatórios

Todos os relatórios são gerados em Markdown na pasta `reports/`. O arquivo contém:

- Cabeçalho com alvo, modo de execução e data/hora UTC.
- Seção individual para cada módulo com status, resumo, registros e mensagens de erro (quando existirem).

## Implantação em produção (domínio próprio)

### Backend (API FastAPI)

1. **Servidor**: provisionar uma VM Linux (Ubuntu 22.04, por exemplo).
2. **Dependências do sistema**: `sudo apt update && sudo apt install python3.11 python3.11-venv nginx`.
3. **Aplicação**:
   - Clonar o repositório em `/opt/prettycool`.
   - Criar e ativar um ambiente virtual (`python3.11 -m venv .venv`).
   - Instalar dependências (`pip install -r requirements.txt`).
4. **Gunicorn**: criar um serviço systemd (`/etc/systemd/system/prettycool.service`):
   ```ini
   [Unit]
   Description=PrettyCool API
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/prettycool
   Environment="PATH=/opt/prettycool/.venv/bin"
   ExecStart=/opt/prettycool/.venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:9000 --workers 4
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
   - Habilitar e iniciar: `sudo systemctl enable --now prettycool`.
5. **Nginx**: configurar um host virtual (`/etc/nginx/sites-available/prettycool`):
   ```nginx
   server {
       listen 80;
       server_name prettycool.seudominio.com;

       location /static/ {
           alias /opt/prettycool/app/static/;
       }

       location / {
           proxy_pass http://127.0.0.1:9000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   - Habilitar com `sudo ln -s /etc/nginx/sites-available/prettycool /etc/nginx/sites-enabled/` e testar `sudo nginx -t`.
   - Reiniciar Nginx: `sudo systemctl reload nginx`.
6. **HTTPS**: aplicar Let's Encrypt (`sudo certbot --nginx -d prettycool.seudominio.com`).

### Front-end

A aplicação web é servida diretamente pelo FastAPI/Nginx. Basta garantir que os ativos (`app/static`) estejam disponíveis e que o
DNS do domínio aponte para a VM configurada.

### Persistência e logs

- As chaves ficam em `config/settings.json` (proteger permissões `chmod 600`).
- Os relatórios ficam em `reports/`. Configure backups ou sincronização conforme a política interna.
- Os logs do Gunicorn (`journalctl -u prettycool`) e do Nginx (`/var/log/nginx/`) devem ser monitorados.

## Notas sobre a identidade visual

- A interface utiliza as cores predominantes da marca Unidade 37 (tons de roxo escuro e grafite).
- O cabeçalho possui espaço dedicado para a logo oficial em `/static/img/logo.png`. Coloque o arquivo fornecido pela equipe de
comunicação nesse caminho para exibir a identidade corretamente.

## Contribuindo

- Novos módulos devem herdar `app.modules.base.PassiveModule` ou `ActiveModule` e registrar-se em `app/modules/__init__.py`.
- Comentários e docstrings foram adicionados ao código para facilitar manutenção futura.

## Aviso legal

O uso da plataforma deve ocorrer apenas em ambientes autorizados e controlados. A Unidade 37 não se responsabiliza por utilização
indevida.
