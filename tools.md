# Tools

This document is bilingual. English content comes first, and Turkish content appears below it.

## English

The `tools/` directory is the technical layer where agents collect system data and work with controlled, low-risk actions.

Its main purpose is to separate the LLM layer from direct shell command execution.

### What the tools layer does

This directory:

- runs Linux commands in a controlled way
- normalizes command outputs into a standard format
- provides domain-based data collection functions
- defines only allowlisted low-risk actions

In short, agents know what to inspect, but the `tools/` layer defines how the system is touched safely.

### Directory structure

Under `tools/`, the project contains:

- `tools/command_utils.py`
- `tools/action_models.py`
- `tools/system_health/`
- `tools/security/`
- `tools/remediation/`

### `tools/command_utils.py`

This is the shared subprocess helper layer.

Responsibilities:

- run commands
- standardize `stdout`, `stderr`, and `exit_code`
- keep outputs JSON-safe
- centralize timeout and error handling

This prevents other tool modules from rewriting subprocess logic repeatedly.

### `tools/action_models.py`

This file defines the shared action result model.

Its purpose is to:

- use the same result shape for health and security actions
- keep action outputs consistent

### `tools/system_health/`

This directory contains system health logic.

#### `system_health_tools.py`

This module contains read-only data collection functions.

Example areas:

- disk usage
- disk I/O
- memory
- uptime
- service status
- failed services
- Docker health
- network health
- kernel error logs
- logrotate status
- nginx status and logs
- recent system logs
- inode and swap data
- size breakdowns

#### `system_health_allowlisted_actions.py`

This module defines only the allowed low-risk system health actions.

Example actions:

- `check_disk`
- `check_disk_io`
- `check_docker_health`
- `check_failed_services`
- `check_log_rotation_health`
- `check_memory`
- `check_network_health`
- `check_uptime`
- `read_kernel_errors`
- `read_nginx_logs`
- `read_system_logs`
- `inspect_var_log_sizes`
- `inspect_root_sizes`
- `status_service`

### `tools/security/`

This directory contains security and access logic.

#### `security_tools.py`

This module collects read-only security data.

Example areas:

- active sessions
- login history
- failed login attempts
- open ports
- firewall status
- SSH logs
- sudo activity
- SSH config audit
- cron security visibility
- world-writable file scanning
- user and sudo group auditing
- fail2ban status
- Docker security visibility

#### `security_allowlisted_actions.py`

This module defines only the allowed low-risk security actions.

Example actions:

- `check_open_ports`
- `check_firewall`
- `check_cron_security`
- `check_docker_security`
- `check_fail2ban_status`
- `check_user_account_audit`
- `check_world_writable_files`
- `read_ssh_logs`
- `read_ssh_config_audit`
- `read_sudo_activity`
- `list_active_sessions`
- `list_recent_logins`
- `list_failed_logins`

### `tools/remediation/`

This directory manages the remediation planning side.

#### `remediation_tools.py`

This module does not run shell commands directly. Instead, it:

- reads the `SystemHealthAgent` output
- reads the `SecurityReviewAgent` output
- uses the current low-risk action list
- extracts prioritized remediation signals
- prepares a shared planning context for the LLM

Example responsibilities:

- build priority signals
- build a safe action catalog
- combine health and security reports into one remediation context

### Why this separation matters

This structure helps because:

- agents do not invent arbitrary shell commands
- data collection logic stays reusable
- health and security responsibilities are separated at tool level
- remediation planning is handled in its own tool layer
- automation safety boundaries are defined in code

### Summary

The `tools/` directory is the most critical integration and safety layer in the project. It collects the data that agents interpret, standardizes outputs, and keeps automation boundaries under control.

## Turkce

`tools/` klasoru, bu projede agentlarin sistemden veri topladigi ve sinirli aksiyon mantigini kullandigi teknik katmandir.

Bu katmanin amaci, LLM tarafini dogrudan shell komutlarindan ayirmaktir.

### Tools Katmani Ne Yapar?

Bu klasor:

- Linux komutlarini kontrollu sekilde calistirir
- komut ciktisini standart formata donusturur
- alan bazli veri toplama fonksiyonlari sunar
- sadece izin verilen dusuk riskli aksiyonlari tanimlar

Kisacasi agentlar "neye bakacagini" bilir, ama "sisteme nasil dokunacagini" `tools/` katmani belirler.

### Klasor Yapisi

`tools/` altinda su dosya ve klasorler bulunur:

- `tools/command_utils.py`
- `tools/action_models.py`
- `tools/system_health/`
- `tools/security/`
- `tools/remediation/`

### `tools/command_utils.py`

Bu dosya ortak subprocess yardimci katmanidir.

Gorevi:

- komut calistirmak
- `stdout`, `stderr` ve `exit_code` degerlerini standartlastirmak
- JSON guvenli cikti saglamak
- timeout ve hata durumlarini tek yerde yonetmek

Bu sayede diger tool dosyalari her seferinde `subprocess` mantigini tekrar yazmaz.

### `tools/action_models.py`

Bu dosya ortak action sonuc modelini tanimlar.

Buradaki amac:

- health ve security tarafinda ayni sonuc yapisini kullanmak
- aksiyonlarin tutarli veri dondurmesini saglamak

### `tools/system_health/`

Bu klasor sistem sagligi ile ilgili mantigi icerir.

#### `system_health_tools.py`

Read-only veri toplama fonksiyonlari burada bulunur.

Ornek alanlar:

- disk kullanimi
- disk I/O
- RAM
- uptime
- servis durumu
- failed service listesi
- Docker health
- network health
- kernel error loglari
- logrotate durumu
- nginx servis durumu ve loglari
- son sistem loglari
- inode ve swap bilgileri
- boyut kirilimlari

#### `system_health_allowlisted_actions.py`

Sadece izin verilen dusuk riskli sistem sagligi aksiyonlari burada tanimlanir.

Ornek aksiyonlar:

- `check_disk`
- `check_disk_io`
- `check_docker_health`
- `check_failed_services`
- `check_log_rotation_health`
- `check_memory`
- `check_network_health`
- `check_uptime`
- `read_kernel_errors`
- `read_nginx_logs`
- `read_system_logs`
- `inspect_var_log_sizes`
- `inspect_root_sizes`
- `status_service`

### `tools/security/`

Bu klasor guvenlik ve erisim tarafini yonetir.

#### `security_tools.py`

Read-only guvenlik verisi toplar.

Ornek alanlar:

- aktif oturumlar
- login gecmisi
- failed login denemeleri
- acik portlar
- firewall durumu
- SSH loglari
- sudo activity
- SSH config audit
- cron guvenlik gorunumu
- world-writable dosya taramasi
- kullanici ve sudo grup denetimi
- fail2ban durumu
- Docker security gorunumu

#### `security_allowlisted_actions.py`

Sadece izin verilen dusuk riskli guvenlik aksiyonlarini tanimlar.

Ornek aksiyonlar:

- `check_open_ports`
- `check_firewall`
- `check_cron_security`
- `check_docker_security`
- `check_fail2ban_status`
- `check_user_account_audit`
- `check_world_writable_files`
- `read_ssh_logs`
- `read_ssh_config_audit`
- `read_sudo_activity`
- `list_active_sessions`
- `list_recent_logins`
- `list_failed_logins`

### `tools/remediation/`

Bu klasor remediation planning tarafini yonetir.

#### `remediation_tools.py`

Bu modul dogrudan shell komutu calistirmaz. Bunun yerine:

- `SystemHealthAgent` ciktisini okur
- `SecurityReviewAgent` ciktisini okur
- mevcut low-risk action listesini kullanir
- oncelikli remediation sinyalleri cikarir
- LLM'e gidecek ortak planning context'ini hazirlar

Ornek gorevler:

- oncelik sinyali cikarmak
- safe action katalogu olusturmak
- health ve security raporlarini tek remediation baglaminda birlestirmek

### Neden Bu Ayrim Onemli?

Bu yapi sayesinde:

- agentlar rastgele shell komutu uydurmaz
- veri toplama mantigi tekrar kullanilabilir olur
- sistem sagligi ve guvenlik rolleri tool seviyesinde de ayrilir
- remediation planning de ayri bir tool katmani ile yonetilir
- guvenli otomasyon sinirlari kod ile belirlenir

### Ozet

`tools/` klasoru, bu projenin en kritik guvenlik ve entegrasyon katmanidir. Agentlarin yorum yaptigi veriyi toplar, ciktiyi standartlastirir ve otomasyon sinirlarini kontrol altinda tutar.
