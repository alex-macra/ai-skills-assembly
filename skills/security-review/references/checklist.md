# Security review checklist

Per-category detail for both modes. The decision rules, severity ladder, and reporting format live in `SKILL.md`.

## Codebase review checklist

### Secrets & credentials
- Grep for: `password`, `secret`, `api_key`, `token`, `BEGIN PRIVATE KEY`, AWS access key prefixes (`AKIA`, `ASIA`).
- `.env`, `.env.*`, `config/*.yaml` - should never be committed. Check `.gitignore`.
- `git log --all -p` for historical commits that leaked secrets.
- Hardcoded JWT secrets, fallback admin passwords, default credentials are blockers.
- Logger redact arrays must cover every API key / token / password the app handles.

### Input validation
- Every external input (HTTP body/query/header/path, file upload, queue message, env var, deserialized blob) is validated at the boundary.
- Type coercion is not validation. `parseInt(req.query.id)` returns `NaN`, not an error.
- Schema-validate with `zod` / `pydantic` / `joi`. Reject unknown fields by default.
- File uploads: check MIME by content-sniffing (not extension), enforce size limits, store outside the web root, never execute uploaded files.

### Injection
- **SQL**: parameterized queries only. f-strings / template literals into SQL are blockers.
- **NoSQL**: same - `$where` with user input, Mongo operator injection.
- **Command**: `exec()` / `subprocess` with `shell=True` and user input is a blocker. Use arg arrays.
- **LDAP, XPath, XML, regex (ReDoS)**: each has its own sanitization rules.
- **Template**: SSTI - never `eval` user input through Jinja/Handlebars.
- **Prompt injection (LLM apps)**: wrap untrusted user content in delimited tags (`<user_input>...</user_input>`); instruct the system prompt to treat tagged content as data only.

### Authn / Authz
- Passwords: `argon2id`, `scrypt`, or `bcrypt` (cost >= 12). Never `md5`, `sha1`, `sha256` for passwords.
- Sessions: `httpOnly`, `secure`, `sameSite=Lax/Strict`, rotate on privilege change, expire on logout.
- JWT: verify `alg` server-side (reject `none`); verify signature before reading claims; check `exp`, `iss`, `aud`.
- OAuth: validate `state`, validate `redirect_uri` against allowlist, use PKCE for public clients.
- Authorization is per-request, not per-session. Every endpoint checks "can THIS user access THIS resource?".
- Login lockout / rate limit per account, not just per IP.

### XSS / output encoding
- Frontend: render text as text. `innerHTML` / `dangerouslySetInnerHTML` / `v-html` only with sanitized content (DOMPurify).
- Set `Content-Security-Policy` with explicit sources; no `'unsafe-inline'` for scripts in production.
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (or CSP `frame-ancestors`), `Referrer-Policy`.

### CSRF / CORS
- Mutating endpoints: SameSite cookies + CSRF token, OR custom request header (browsers don't allow cross-origin custom headers without CORS preflight).
- CORS: explicit allowlist of origins. `Access-Control-Allow-Origin: *` with credentials is a blocker.

### SSRF
- Server-side fetches: validate URL host against allowlist; block `localhost`, `127.0.0.0/8`, `169.254.169.254` (cloud metadata), `::1`, `0.0.0.0`, link-local.
- DNS-rebinding: resolve once, then use the IP.
- Re-check on every redirect hop - not just the initial URL.

### Crypto
- Use library primitives - never roll your own. `libsodium`, `cryptography` (Python), `node:crypto`.
- AES-GCM or ChaCha20-Poly1305 for authenticated encryption. Never AES-ECB.
- Random tokens: CSPRNG (`crypto.randomBytes`, `secrets.token_urlsafe`) - never `Math.random()`.
- TLS: 1.2+ only; modern cipher suites; HSTS with `includeSubDomains`.

### Deserialization
- `pickle.loads`, `yaml.load` (without `SafeLoader`), `Marshal`, Java native serialization on untrusted input mean RCE.
- JSON is safe; everything fancier needs scrutiny.

### Supply chain
- `npm audit` / `pip-audit` / `cargo audit` / `osv-scanner` on every PR.
- Lockfile committed and reviewed; pin to exact versions for direct deps in security-sensitive code.
- Watch for typosquats: `requets`, `colourama`, `rect`.
- Check `postinstall` hooks in new dependencies.

### Logging & monitoring
- Don't log: passwords, tokens, full request bodies, PII/PHI, payment data.
- Do log: auth events (success and failure), admin actions, access-control denials, integrity-relevant changes.
- Alerting on auth-failure spikes, privilege escalations, unusual outbound traffic.

### LLM-specific (when applicable)
- Sensitive data must be de-identified before any LLM API call.
- Wrap untrusted inputs in delimited tags; instruct the system prompt to treat them as data only.
- API keys live in env, never in client code or version control. Logger redact must include `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- Verify model output before acting on it; never `eval` LLM responses, never let them shape a SQL query without parameterization.

## Live target testing checklist (authorized only)

### Recon
- DNS enumeration, subdomain discovery (`amass`, `subfinder`).
- Port scanning (`nmap -sV`) - start light, escalate only with permission.
- Web fingerprinting (`whatweb`, `wappalyzer`).
- Robots, sitemap, common paths, public buckets.

### Auth surface
- Login: enumerate via timing or error-message differences, brute-force protection (lockout, rate-limit, CAPTCHA).
- Session: token entropy, rotation, fixation, expiry.
- Password reset: predictable tokens, lack of rate limits, account-takeover via host-header injection.

### Web app
- Map every input. For each: SQLi, XSS (reflected/stored/DOM), SSRF, IDOR, path traversal, command injection.
- Use `Burp Suite` / `ZAP` for interception; `sqlmap` and `ffuf` purposefully and with rate limits.
- Don't run noisy fuzzers against production without explicit approval.

### API
- Enumerate endpoints (Swagger/OpenAPI if exposed; otherwise spider).
- Authentication bypass: missing on internal endpoints, JWT issues, mass assignment.
- Authorization: try every endpoint as user A with user B's IDs.
- Rate limits per endpoint, not just per IP.

### Infra
- TLS config: `testssl.sh`, `sslyze`. Look for weak ciphers, expired certs, missing HSTS.
- Cloud metadata accessible? Try SSRF to `169.254.169.254`.
- Misconfigured S3 / GCS buckets - listable? writable?
