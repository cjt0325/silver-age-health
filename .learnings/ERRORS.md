## [ERR-20260906-TLS] direct_docx_download

**Logged**: 2026-09-06T00:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
PowerShell could reach the official Hefei University page but failed to download its linked DOCX attachments because of a Windows TLS credential error.

### Error
```
Authentication failed, see inner exception.
```

### Context
- Attempted to download four official DOCX attachments linked from the 2026 Anhui AI Large Model Innovation Application Competition pre-notice.
- The web research tool could read the HTML page, but its DOCX fetch also reported unsupported content type.

### Suggested Fix
Treat official-page reachability and local Schannel/TLS download capability as separate checks; use the published HTML and corroborating university notices unless the user explicitly asks for attachment extraction and authorizes TLS troubleshooting.

### Metadata
- Reproducible: unknown
- Related Files: none
- Tags: windows, schannel, tls, docx, hfuu

---
