---
description: VM infrastructure - All 17 VMs, 29 bots, role classifications, and bot-to-VM mapping
argument-hint: [VM name, bot name, or what you're checking]
---

# VM Infrastructure Inventory

**Total VMs**: 17 (16 active, 1 offline)
**Total Bots/Services**: 29
**Gateway**: 100.86.32.62 (Tailscale VPN — all VMs accessed via different WinRM ports)
**OS**: All Windows (DESKTOP-* hostnames)
**Environment**: All production

---

## VM Inventory

| VM Name | NAT IP | WinRM Port | Role | Bots |
|---------|--------|------------|------|------|
| **VM CBMY** | 192.168.144.128 | 65506 | chatbot | hiranai-ai, murahya-ai, chatbot-script |
| **VM CBC3** | 192.168.144.147 | 65507 | chatbot | ai-chatbot |
| **VM CBSG** | 192.168.144.130 | 65508 | chatbot | sg-auto-clicker |
| **VM-8** | 192.168.144.143 | 15985 | parcel-claim | parcel-claim-sg, parcel-claim-kinata |
| **VM 9** | 192.168.144.144 | 65510 | parcel-claim | parcel-claim-sg-status, parcel-claim-my-status |
| **VM3** | 192.168.144.131 | 65500 | automation | costing-stock, parcel-claim, parcel-claim-my, shopee-auto-approve, shopee-comp-my |
| **VM1** | 192.168.144.141 | 45985 | order-management | order-management |
| **VM OD** | 192.168.144.136 | 65505 | order-dispatch | order-dispatch, owr, manual-run |
| **nisv** | 192.168.144.137 | 35985 | scheduler | scheduled-tasks |
| **VM2** | 192.168.144.134 | 55985 | scheduler | scheduler, sto-schedule |
| **VM5** | 192.168.144.146 | 65502 | scheduler | account-health, schedule |
| **VM TT** | 192.168.144.135 | 65504 | scheduler | tiktok-schedule |
| **VM4** | 192.168.144.129 | 65501 | scraper | category-combined-loop |
| **VM6** | 192.168.144.132 | 65503 | scraper | failed-delivery-scrape, tt-comp |
| **VM10** | 192.168.144.145 | 65511 | scraper | om-ni-co-in, sku-shop |
| **Kaushal SQL Machine** | 192.168.144.138 | 25985 | database | *(none -- central DB server)* |
| **VM AdsPower** | 192.168.144.142 | 65509 | adspower | *(offline -- not in use)* |

---

## VMs by Role

### Chatbot VMs (Shopee & TikTok AI Chat)
| VM | Bots | What it does |
|----|------|--------------|
| **VM CBMY** | hiranai-ai, murahya-ai, chatbot-script | Malaysia Shopee chatbots (Hiranai + MurahYa stores) |
| **VM CBC3** | ai-chatbot | Additional chatbot instance |
| **VM CBSG** | sg-auto-clicker | Singapore Shopee chat auto-clicker |

### Parcel Claim VMs
| VM | Bots | What it does |
|----|------|--------------|
| **VM-8** | parcel-claim-sg, parcel-claim-kinata | Files SG + Kinata logistics claims |
| **VM3** | parcel-claim, parcel-claim-my | Files generic + MY claims |
| **VM 9** | parcel-claim-sg-status, parcel-claim-my-status | Tracks claim outcomes for SG + MY |

### Order VMs
| VM | Bots | What it does |
|----|------|--------------|
| **VM1** | order-management | Core order management automation |
| **VM OD** | order-dispatch, owr, manual-run | Order dispatch, warehouse/returns, manual runs |

### Scheduler VMs
| VM | Bots | What it does |
|----|------|--------------|
| **nisv** | scheduled-tasks | General scheduled tasks |
| **VM2** | scheduler, sto-schedule | General + STO scheduling |
| **VM5** | account-health, schedule | Health monitoring + scheduled tasks |
| **VM TT** | tiktok-schedule | TikTok-specific scheduled ops |

### Scraper VMs
| VM | Bots | What it does |
|----|------|--------------|
| **VM4** | category-combined-loop | Product category scraping |
| **VM6** | failed-delivery-scrape, tt-comp | Failed delivery + TikTok competitor scraping |
| **VM10** | om-ni-co-in, sku-shop | Omni-channel + SKU/shop data scraping |

### Multi-Purpose
| VM | What it does |
|----|--------------|
| **VM3** | Most loaded VM -- runs 5 bots: costing-stock, parcel claims (MY), shopee-auto-approve, shopee-comp-my |
| **Kaushal SQL Machine** | Central database server (no bots) -- if this goes down, most VMs are affected |

---

## Bot-to-VM Quick Lookup

| Bot/Service | VM |
|-------------|-----|
| account-health | VM5 |
| ai-chatbot | VM CBC3 |
| category-combined-loop | VM4 |
| chatbot-script | VM CBMY |
| costing-stock | VM3 |
| failed-delivery-scrape | VM6 |
| hiranai-ai | VM CBMY |
| manual-run | VM OD |
| murahya-ai | VM CBMY |
| om-ni-co-in | VM10 |
| order-dispatch | VM OD |
| order-management | VM1 |
| owr | VM OD |
| parcel-claim | VM3 |
| parcel-claim-kinata | VM-8 |
| parcel-claim-my | VM3 |
| parcel-claim-my-status | VM 9 |
| parcel-claim-sg | VM-8 |
| parcel-claim-sg-status | VM 9 |
| schedule | VM5 |
| scheduled-tasks | nisv |
| scheduler | VM2 |
| sg-auto-clicker | VM CBSG |
| shopee-auto-approve | VM3 |
| shopee-comp-my | VM3 |
| sku-shop | VM10 |
| sto-schedule | VM2 |
| tiktok-schedule | VM TT |
| tt-comp | VM6 |

---

## VM MCP Tool Reference

| Tool | Purpose | Example |
|------|---------|---------|
| `vm_inventory` | List all VMs or filter by role/env | `role: "chatbot"` |
| `vm_status` | CPU, memory, uptime, running processes | `vm_name: "VM CBMY"` |
| `vm_processes` | Detailed node/python processes with resource usage | `vm_name: "VM3"` |
| `vm_configs` | Read JSON configs from C:\Bots, C:\Scripts, Desktop | `vm_name: "VM OD"` |
| `vm_schedules` | Active scheduled tasks with next/last run times | `vm_name: "VM TT"` |
| `vm_versions` | Node.js, Python, pip, OS versions | `vm_name: "VM1"` |
| `vm_list_files` | List files at a path | `vm_name: "VM-8", path: "C:\\Bots"` |
| `vm_read_file` | Read a file from a VM | `vm_name: "VM CBMY", path: "C:\\Bots\\config.json"` |
| `vm_execute` | Run a command on a VM | `vm_name: "VM1", command: "tasklist"` |
| `vm_task_control` | Start/stop/restart bot processes | `vm_name: "VM CBMY", action: "restart", bot: "hiranai-ai"` |
| `vm_multi_status` | Bulk health check across VMs | `query: "status", role: "chatbot"` |
| `vm_multi_execute` | Run command on multiple VMs | `query: "command", role: "scheduler"` |

### Common Operations

**Check if a bot is running**: `vm_processes` with the VM name from the lookup table above.

**Restart a bot**: `vm_task_control` with `action: "restart"` and the bot name.

**Full fleet health check**: `vm_multi_status` with `query: "status"`.

**Check schedules for TikTok**: `vm_schedules` with `vm_name: "VM TT"`.

---

## Key Observations

1. **VM3 is the most loaded** -- 5 bots across different functions. Single point of failure risk.
2. **Kaushal SQL Machine** is the central DB -- critical dependency for all other VMs.
3. **Parcel claims span 3 VMs** -- VM-8 (SG filing), VM3 (MY filing), VM 9 (status tracking).
4. **Chatbots on 3 dedicated VMs** -- isolated from other workloads.
5. **VM AdsPower is offline** -- can be repurposed or decommissioned.
6. **All VMs are production** -- no staging/dev VMs visible.
