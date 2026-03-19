# DevOps Watchdog

AI-powered multi-agent Linux server analysis for health, security, and remediation planning.

This README is bilingual. English comes first, Turkish comes second.

## English

### Overview

`DevOps Watchdog` is an educational multi-agent project that analyzes a Linux server with three specialized AI agents:

- `SystemHealthAgent`
- `SecurityReviewAgent`
- `RemediationAdvisorAgent`

The project collects real host data through a controlled tool layer, sends structured context to the LLM, and produces both human-readable and machine-readable reports.

### What it does

- inspects system health signals such as disk, memory, services, Docker, nginx, kernel, network, and logrotate
- inspects security signals such as sessions, SSH, sudo activity, cron, fail2ban, world-writable files, user auditing, and Docker security
- builds a prioritized remediation plan from the first two agent reports
- saves outputs as Markdown and JSON under `reports/`

### Project structure

```text
.
├── main.py
├── config.py
├── llm_client.py
├── .env.example
├── agents/
├── tools/
├── tests/
└── reports/
```

### Installation

Requirements:

- Python 3.12 or newer
- Linux environment
- OpenAI API key

### Quick start

1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create your environment file

```bash
cp .env.example .env
```

4. Edit `.env` and set your real `OPENAI_API_KEY`

Example:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
AUTO_APPROVE_LOW_RISK=false
MONITORED_SERVICES=nginx,docker,ssh
DISK_USAGE_WARNING_PERCENT=85
HEALTH_LOG_LINE_COUNT=20
SECURITY_LOG_LINE_COUNT=30
LOGIN_HISTORY_COUNT=10
COMMAND_TIMEOUT_SECONDS=30
```

5. Run the project

```bash
./.venv/bin/python main.py
```

### Output

Each run generates:

- one Markdown report for operators
- one JSON report for structured integrations

Files are written under `reports/`.

### Main design idea

The LLM does not run arbitrary shell commands. A dedicated `tools/` layer collects data safely and exposes only controlled, allowlisted actions. This keeps the project safer, more modular, and easier to extend.

## Turkce

### Genel Bakis

`DevOps Watchdog`, bir Linux sunucuyu uc uzman AI agent ile analiz eden egitim odakli bir multi-agent projedir:

- `SystemHealthAgent`
- `SecurityReviewAgent`
- `RemediationAdvisorAgent`

Proje, gercek sistem verisini kontrollu bir tool katmani uzerinden toplar, bu veriyi yapilandirilmis sekilde LLM'e verir ve hem insan okunur hem de makine okunur raporlar uretir.

### Ne Yapar?

- disk, RAM, servisler, Docker, nginx, kernel, network ve logrotate gibi sistem sagligi sinyallerini inceler
- oturumlar, SSH, sudo activity, cron, fail2ban, world-writable dosyalar, kullanici denetimi ve Docker security gibi guvenlik sinyallerini inceler
- ilk iki agentin raporundan onceliklendirilmis bir remediation plani uretir
- ciktilari Markdown ve JSON olarak `reports/` klasorune kaydeder

### Proje Yapisi

```text
.
├── main.py
├── config.py
├── llm_client.py
├── .env.example
├── agents/
├── tools/
├── tests/
└── reports/
```

### Kurulum

Gereksinimler:

- Python 3.12 veya daha yeni
- Linux ortami
- OpenAI API key

### Hizli Kurulum

1. Sanal ortam olustur

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Bagimliliklari kur

```bash
pip install -r requirements.txt
```

3. Ortam dosyasini olustur

```bash
cp .env.example .env
```

4. `.env` dosyasini ac ve gercek `OPENAI_API_KEY` degerini gir

Ornek:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
AUTO_APPROVE_LOW_RISK=false
MONITORED_SERVICES=nginx,docker,ssh
DISK_USAGE_WARNING_PERCENT=85
HEALTH_LOG_LINE_COUNT=20
SECURITY_LOG_LINE_COUNT=30
LOGIN_HISTORY_COUNT=10
COMMAND_TIMEOUT_SECONDS=30
```

5. Projeyi calistir

```bash
./.venv/bin/python main.py
```

### Cikti

Her calistirmada:

- operator icin bir Markdown raporu
- entegrasyonlar icin bir JSON raporu

uretilir.

Dosyalar `reports/` altina yazilir.

### Temel Tasarim Mantigi

LLM rastgele shell komutu calistirmaz. Ayrilmis `tools/` katmani veriyi guvenli sekilde toplar ve sadece kontrollu, allowlisted aksiyonlari sunar. Bu da projeyi daha guvenli, daha moduler ve daha kolay gelistirilebilir hale getirir.
