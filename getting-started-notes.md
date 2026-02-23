# Getting Started — Eten

Setup guides for all three development domains.

---

## 1. Web App Setup

### Prerequisites
- Node.js (LTS)
- npm
- Git
- Access to `it-awesomeree` GitHub org

### Clone & Install
```bash
git clone https://github.com/it-awesomeree/awesomeree-webapp.git
cd awesomeree-webapp
npm install
```

### Environment
```bash
cp .env.example .env.local
# Fill in: DB credentials, Firebase config, API keys
```

### Run Dev Server
```bash
npm run dev
# Opens at http://localhost:3000
```

### Project Structure (Next.js 15 App Router)
```
app/
  layout.tsx          # Root layout
  page.tsx            # Home page
  api/                # API routes
  (routes)/           # Page routes
components/           # Shared UI components
lib/                  # Utilities, DB connections
public/               # Static assets
```

### Branch Workflow
1. Create feature branch from `test`: `git checkout -b feature/AW-XXX-description test`
2. Develop and commit
3. PR to `test` branch (never directly to `main`)
4. After review approval, `test` → `main` promotion

---

## 2. n8n Workflow Setup

### Access
- **URL**: `https://n8n.barndoguru.com`
- **Login**: Ask Agnes for credentials
- **MCP**: n8n MCP server available for CLI operations

### Key Concepts
- **Workflows**: Chains of nodes that process data
- **Triggers**: Webhook, Form, Schedule, Manual
- **Credentials**: Stored in n8n (Gemini, OpenAI, MySQL, GCS)
- **Execution modes**: Production (live) vs Test (webhook-test URL)

### Working with Workflows
1. Open n8n UI → find your workflow
2. Use **Test URL** for development (not production webhook)
3. Test with sample data before activating
4. Validate with `n8n_validate_workflow` MCP tool
5. When ready, activate the workflow

### Variation Generator — Testing
```bash
# Test webhook (use webhook-test URL when workflow is open in editor)
curl -X POST https://n8n.barndoguru.com/webhook-test/generate-variation-description \
  -H "Content-Type: application/json" \
  -d '{"product_id": 12345, "shop_name": "test-shop", ...}'
```

---

## 3. VM Bot Scripts Setup

### Access
- **VPN**: Install Tailscale, join the network
- **Gateway**: 100.86.32.62
- **Protocol**: WinRM (different ports per VM)
- **All VMs**: Windows OS

### Connecting to a VM
```powershell
# Via WinRM (from gateway/host PC)
Enter-PSSession -ComputerName 192.168.144.XXX -Port XXXXX -Credential (Get-Credential)
```

### Via MCP Tools (Recommended)
```
vm_status vm_name="VM CBMY"          # Check VM health
vm_processes vm_name="VM CBMY"       # List running bots
vm_read_file vm_name="VM CBMY" path="C:\\Bots\\config.json"  # Read config
vm_task_control vm_name="VM CBMY" action="restart" bot="hiranai-ai"  # Restart bot
```

### Bot Script Structure (on VMs)
```
C:\Bots\
  hiranai-ai\
    index.js          # Main bot entry point
    config.json       # Bot configuration
    package.json      # Dependencies
  murahya-ai\
    ...
C:\Scripts\
  scheduled-tasks\
    ...
```

### Source Code
- **Repo**: `it-awesomeree/bot-scripts`
- **Key directory**: `chatbot-middleware/` — Node.js/Puppeteer middleware scripts
- Changes to bot scripts need to be deployed to the correct VM after testing

---

## Common Tools Across All Domains

| Tool | Purpose | Setup |
|------|---------|-------|
| Claude Code | AI development assistant | Already installed |
| Jira | Ticket management | `awesomeree.atlassian.net` |
| GitHub | Version control | `it-awesomeree` org |
| Google Cloud | Infrastructure | GCP console / `gcloud` CLI |
| Tailscale | VPN for VM access | Install + join network |
