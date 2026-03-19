# DevOps Watchdog

This document is bilingual. English content comes first, and Turkish content appears below it.

## English

`DevOps Watchdog` is an educational multi-agent analysis project for Linux servers.

Its main goal is to inspect the same server with three specialized AI agents and combine their outputs into a single operational report.

### What the project does

When the system runs, it:

1. loads environment settings
2. initializes the OpenAI client
3. runs the system health agent
4. runs the security review agent
5. runs the remediation advisor agent
6. combines the outputs of all three agents
7. saves the result as Markdown and JSON under `reports/`

### Core objectives

- demonstrate multi-agent design in an educational way
- collect real data from a Linux server
- turn that data into meaningful reports with an LLM
- keep automation controlled and low-risk
- use a readable and modular project structure
- inspect health and security with deeper sub-checks

### Main components

- `main.py`: orchestration layer
- `config.py`: environment settings and runtime configuration
- `llm_client.py`: shared OpenAI client wrapper
- `.env.example`: sample environment variable template
- `agents/`: specialized agent modules
- `tools/`: data collection and allowlisted action layer
- `reports/`: generated outputs

### Architectural approach

The agents do not talk to each other directly. Each agent works in its own domain, and `main.py` orchestrates the full flow.

`SystemHealthAgent` collects operational signals such as disk, services, nginx, Docker, kernel, network, and logrotate. `SecurityReviewAgent` focuses on sessions, SSH, sudo activity, cron, fail2ban, world-writable files, user auditing, and Docker security. `RemediationAdvisorAgent` reads the first two reports and turns them into a prioritized action plan.

This design makes the system:

- easier to read
- clearer in terms of responsibility separation
- easier to extend with new agents
- stronger at separating findings from remediation planning

### Output format

The project generates two output formats:

- Markdown report: readable summary for operators
- JSON report: structured output for integrations and automation

### Installation

Requirements:

- Python 3.12 or newer
- Linux environment
- OpenAI API key

### Environment setup

New users should copy `.env.example` to `.env` and fill in at least the OpenAI API key.

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

### Summary

`DevOps Watchdog` is a practical prototype that approaches AI agents not only as prompt-driven assistants, but as part of a full architecture including data collection, safety boundaries, reporting, and decision support.

## Turkce

`DevOps Watchdog`, Linux sunucular icin gelistirilmis egitim odakli bir multi-agent analiz projesidir.

Projenin temel amaci, ayni sunucuyu uc farkli uzman AI agent ile inceleyip tek bir operasyonel raporda birlestirmektir.

### Proje Ne Yapar?

Sistem calistiginda:

1. ortam ayarlarini yukler
2. OpenAI istemcisini hazirlar
3. sistem sagligi agentini calistirir
4. guvenlik agentini calistirir
5. remediation advisor agentini calistirir
6. uc agentin sonucunu birlestirir
7. sonucu Markdown ve JSON olarak `reports/` klasorune kaydeder

### Temel Hedefler

- multi-agent mantigini egitim odakli gostermek
- Linux sunucudan gercek veri toplamak
- LLM ile bu verileri anlamli rapora donusturmek
- guvenli ve sinirli otomasyon mantigi kurmak
- okunabilir ve moduler bir klasor yapisi kullanmak
- sistem sagligi ve guvenlik alanlarini daha derin alt kontrollerle incelemek

### Temel Bilesenler

- `main.py`: orkestrasyon katmani
- `config.py`: ortam ayarlari ve konfigurasyon
- `llm_client.py`: OpenAI istemci sarmalayicisi
- `.env.example`: ortam degiskenleri icin ornek sablon
- `agents/`: uzman agent modulleri
- `tools/`: veri toplama ve allowlisted aksiyon katmani
- `reports/`: uretilen ciktilar

### Mimari Yaklasim

Bu projede agentlar birbiriyle konusmaz. Her agent kendi alaninda calisir ve `main.py` tum sureci yonetir.

`SystemHealthAgent` tarafi disk, servis, nginx, Docker, kernel, network ve logrotate gibi operasyonel sinyalleri toplar. `SecurityReviewAgent` tarafi ise oturumlar, SSH, sudo activity, cron, fail2ban, world-writable dosyalar, kullanici denetimi ve Docker security gibi guvenlik sinyallerine bakar. `RemediationAdvisorAgent` ise ilk iki agentin ciktilarini okuyup onceliklendirilmis aksiyon plani uretir.

Bu tercih:

- yapinin daha sade olmasini
- sorumluluklarin daha net ayrilmasini
- kodun daha kolay okunmasini
- yeni agent eklenmesini kolaylastiran bir mimari kurulmasini
- tespit ile aksiyon plani arasina ayri bir karar katmani eklenmesini

saglar.

### Cikti Formati

Proje iki farkli cikti uretir:

- Markdown rapor: insan tarafinda kolay okunabilir ozet
- JSON rapor: sistemler ve entegrasyonlar icin yapilandirilmis veri

### Kurulum

Gereksinimler:

- Python 3.12 veya daha yeni
- Linux ortami
- OpenAI API key

### Ortam Kurulumu

Projeyi yeni kuran kisi `.env.example` dosyasini `.env` olarak kopyalamali ve en azindan OpenAI API key degerini doldurmalidir.

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

### Ozet

`DevOps Watchdog`, AI agent kavramini sadece prompt tarafinda degil; mimari, guvenlik, veri toplama ve raporlama katmanlariyla birlikte ele alan pratik bir prototiptir.
