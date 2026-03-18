# Chapter 3: Security, Compliance, and Open Banking

## Introduction

As enterprises connect critical applications and expose APIs externally—especially in highly regulated industries like Financial Services and Open Banking—security transitions from an afterthought to a foundational pillar. Modern API Gateways act as the primary enforcement point for Zero-Trust principles, Authentication, and Data Protection.

This chapter provides comprehensive recipes for implementing robust security controls in Kong. We will cover identity verification (JWT, OIDC), Zero-Trust access mechanisms (mTLS, IP restrictions), and fintech compliance essentials, including keyring encryption and policies tailored for Open Banking standards.

---

## Recipe 3.1: Implementing JWT and Key Authentication

### Problem
You need to secure a public-facing API to ensure that only registered clients or authenticated users can access the endpoints. 

### Solution
Implement Key Authentication for machine-to-machine traffic and JSON Web Token (JWT) verification for user-centric sessions.

**Part A: Key Authentication (API Keys)**
```yaml
_format_version: "3.0"
services:
  - name: partner-api
    url: http://partner.internal:8080
    plugins:
      - name: key-auth
        config:
          key_names: ["x-api-key"]
          hide_credentials: true
    routes:
      - name: partner-route
        paths:
          - /partners
```

**Part B: JWT Verification**
```yaml
_format_version: "3.0"
services:
  - name: user-profile-api
    url: http://profile.internal:8080
    plugins:
      - name: jwt
        config:
          uri_param_names: ["jwt"]
          header_names: ["authorization"]
          claims_to_verify: ["exp"]
    routes:
      - name: profile-route
        paths:
          - /profile
```

### Discussion
The `key-auth` plugin is perfect for simple B2B integrations, verifying a static key sent in the `x-api-key` header. `hide_credentials: true` ensures the backend service doesn't receive the raw API key.
The `jwt` plugin is suited for frontend applications. Kong intercepts the token, verifies the cryptographic signature (using a consumer's registered public key or secret), and ensures the token hasn't expired (`exp` claim). If valid, Kong proxies the request; if invalid, it immediately returns a `401 Unauthorized`.

---

## Recipe 3.2: Integrating OpenID Connect (OIDC) for Enterprise SSO

### Problem
You need to authenticate users against an existing Corporate Identity Provider (IdP) like Okta, Auth0, or Azure AD without implementing complex OAuth2 flows in every backend microservice.

### Solution
Use Kong's `openid-connect` plugin to handle the entire authentication lifecycle at the gateway level.

```yaml
_format_version: "3.0"
services:
  - name: internal-dashboard
    url: http://dashboard.internal:8080
    plugins:
      - name: openid-connect
        config:
          issuer: "https://your-tenant.auth0.com/.well-known/openid-configuration"
          client_id: ["<your-client-id>"]
          client_secret: ["<your-client-secret>"]
          auth_methods: ["authorization_code"]
          session_secret: "a-very-long-and-secure-random-string"
          redirect_uri: ["https://gateway.example.com/callback"]
    routes:
      - name: dashboard-route
        paths:
          - /dashboard
```

### Discussion
The `openid-connect` plugin turns Kong into an OAuth2 Relying Party. When an unauthenticated user accesses `/dashboard`, Kong redirects them to the IdP. After a successful login, the user is redirected back to Kong with an authorization code. Kong securely exchanges this code for an ID and Access Token, creates a local session cookie (encrypted via `session_secret`), and proxies the request to the dashboard. The backend application receives the authenticated user's identity via HTTP headers (like `X-Userinfo`) without writing a single line of auth code.

---

## Recipe 3.3: Enforcing Strict mTLS Between Internal Microservices

### Problem
In a Zero-Trust architecture, you must guarantee that traffic between internal microservices is encrypted and strictly authenticated, protecting against internal bad actors or network breaches.

### Solution
Implement mutual TLS (mTLS) using the `mtls-auth` plugin, requiring clients to present a valid X.509 certificate signed by a trusted Certificate Authority (CA).

```yaml
_format_version: "3.0"
services:
  - name: financial-ledger-api
    url: http://ledger.internal:8080
    plugins:
      - name: mtls-auth
        config:
          ca_certificates: ["ca-cert-id-12345"] # ID of the CA cert uploaded to Kong
          skip_consumer_lookup: false
          cache_ttl: 60
    routes:
      - name: ledger-route
        paths:
          - /ledger
```

### Discussion
When the `mtls-auth` plugin is enabled, Kong inspects the client certificate presented during the TLS handshake. It verifies the certificate against the specified `ca_certificates`. By setting `skip_consumer_lookup: false`, Kong will also map the certificate's Subject Alternative Name (SAN) or Common Name (CN) to a specific Kong Consumer entity. This means you can authenticate the service and apply further authorization or rate-limiting rules specific to that internal consumer.

---

## Recipe 3.4: Configuring IP Restriction Lists and Bot Detection

### Problem
Your API is under reconnaissance scans or experiencing traffic from known malicious IP ranges. You need a lightweight first line of defense at the gateway.

### Solution
Combine the `ip-restriction` and `bot-detection` plugins to drop malicious traffic before it reaches your routing logic.

```yaml
_format_version: "3.0"
plugins:
  # Apply globally across all services
  - name: bot-detection
    config:
      allow: []
      deny:
        - "curl"
        - "PostmanRuntime"
        - "python-requests"
  
  - name: ip-restriction
    config:
      deny:
        - "192.168.10.0/24" # Malicious subnet
        - "10.50.0.5"       # Specific bad actor IP
      status: 403
      message: "Access Denied by Security Policy"
```

### Discussion
Applying these plugins globally ensures a uniform security posture. The `bot-detection` plugin inspects the `User-Agent` header. While easily spoofed by sophisticated attackers, it eliminates a massive amount of "script kiddie" noise and automated vulnerability scanners. The `ip-restriction` plugin acts as a lightweight firewall, immediately returning a `403 Forbidden` for any request originating from the defined CIDR blocks or IPs.

---

## Recipe 3.5: Managing At-Rest Keyring Encryption for Open Banking

### Problem
Open Banking regulations (like PSD2 or CDR) mandate that all sensitive data, including API keys, tokens, and gateway configurations, must be encrypted at rest in the database.

### Solution
Enable Kong's Keyring feature to automatically encrypt sensitive fields within its PostgreSQL database.

1. Generate a secure Data Encryption Key (DEK):
```bash
openssl rand -base64 32
```

2. Configure Kong's environment variables to enable the keyring:
```bash
export KONG_ENFORCE_RBAC=on
export KONG_KEYRING_ENABLED=on
export KONG_KEYRING='[{"strategy":"pbkdf2","cipher":"aes-256-gcm","key":"<YOUR_BASE64_KEY>","iterations":10000}]'
```

3. Restart Kong.

### Discussion
When the Keyring is enabled, Kong uses the provided key to seamlessly encrypt sensitive fields (like consumer credentials, plugin configurations containing secrets, etc.) before writing them to the database, and decrypts them in memory when needed. This ensures that even if an attacker gains raw access to your PostgreSQL database or its backups, they cannot extract plain-text API keys or OIDC secrets, fulfilling stringent compliance auditing requirements for financial institutions.
