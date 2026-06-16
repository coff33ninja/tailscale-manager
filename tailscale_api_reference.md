# Tailscale API v2 Reference

Base URL: `https://api.tailscale.com/api/v2`

> Status: **→ Used** = already implemented in `api_client.py`

## Devices

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/tailnet/{tailnet}/devices` | → Used (`list_devices`) |
| GET | `/device/{deviceId}` | → Used (`get_device`) |
| DELETE | `/device/{deviceId}` | |
| POST | `/device/{deviceId}/expire` | Expire node key |
| GET | `/device/{deviceId}/routes` | List advertised/enabled subnet routes |
| POST | `/device/{deviceId}/routes` | Set enabled subnet routes |
| POST | `/device/{deviceId}/authorized` | Approve/deauthorize device |
| POST | `/device/{deviceId}/name` | Rename device |
| POST | `/device/{deviceId}/tags` | Update device tags |
| POST | `/device/{deviceId}/key` | Disable/enable key expiry |
| POST | `/device/{deviceId}/ip` | Assign specific IPv4 |
| GET | `/device/{deviceId}/attributes` | Read posture attributes |
| POST | `/device/{deviceId}/attributes/{key}` | Set custom posture attribute |
| DELETE | `/device/{deviceId}/attributes/{key}` | Delete custom posture attribute |

## DNS

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/tailnet/{tailnet}/dns/nameservers` | → Used (`list_dns_nameservers`) |
| POST | `/tailnet/{tailnet}/dns/nameservers` | Set nameservers |
| GET | `/tailnet/{tailnet}/dns/preferences` | Get MagicDNS/split-DNS prefs |
| POST | `/tailnet/{tailnet}/dns/preferences` | Set DNS preferences |
| GET | `/tailnet/{tailnet}/dns/searchpaths` | Get search paths |
| POST | `/tailnet/{tailnet}/dns/searchpaths` | Set search paths |
| GET | `/tailnet/{tailnet}/dns/split-dns` | Get per-domain nameservers |
| PUT | `/tailnet/{tailnet}/dns/split-dns` | Set split DNS |
| DELETE | `/tailnet/{tailnet}/dns/split-dns/{domain}` | Remove split DNS domain |

## ACL / Policy File

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/tailnet/{tailnet}/acl` | → Used (`get_acl`) |
| POST | `/tailnet/{tailnet}/acl` | → Used (`set_acl`) |
| POST | `/tailnet/{tailnet}/acl/preview` | Preview rule matches |
| POST | `/tailnet/{tailnet}/acl/validate` | → Used (`validate_acl`) |

## Auth Keys & API Tokens

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/tailnet/{tailnet}/keys` | → Used (`get_keys`) |
| POST | `/tailnet/{tailnet}/keys` | Create auth key |
| GET | `/tailnet/{tailnet}/keys/{keyId}` | Get key details |
| DELETE | `/tailnet/{tailnet}/keys/{keyId}` | Delete key |

## Users

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/users` |
| GET | `/users/{userId}` |
| POST | `/users/{userId}/role` | Change role |
| POST | `/users/{userId}/approve` | Approve user |
| POST | `/users/{userId}/suspend` | Suspend user |
| POST | `/users/{userId}/restore` | Restore user |
| POST | `/users/{userId}/delete` | Delete user |

## Logging

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/logging/configuration` | Export audit logs |
| GET | `/tailnet/{tailnet}/logging/network` | Export network flow logs |
| GET | `/tailnet/{tailnet}/logging/{logType}/stream` | Get log streaming config |
| PUT | `/tailnet/{tailnet}/logging/{logType}/stream` | Set log streaming config |
| GET | `/tailnet/{tailnet}/logging/{logType}/stream/status` | Stream status |

## Contacts

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/tailnet/{tailnet}/contacts` | → Used (`get_contacts`) |
| PATCH | `/tailnet/{tailnet}/contacts/{contactType}` | Update security/billing contact |
| POST | `/tailnet/{tailnet}/contacts/{contactType}/resend-verification-email` | |

## Webhooks

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/webhooks` | List webhooks |
| POST | `/tailnet/{tailnet}/webhooks` | Create webhook |
| GET | `/webhooks/{endpointId}` | Get webhook |
| PUT | `/webhooks/{endpointId}` | Update webhook |
| DELETE | `/webhooks/{endpointId}` | Delete webhook |
| POST | `/webhooks/{endpointId}/test` | Send test event |
| POST | `/webhooks/{endpointId}/rotate` | Rotate secret |

## Device Posture

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/posture/integrations` | List posture integrations |
| POST | `/tailnet/{tailnet}/posture/integrations` | Create integration |
| GET | `/posture/integrations/{id}` | Get integration |
| PUT | `/posture/integrations/{id}` | Update integration |
| DELETE | `/posture/integrations/{id}` | Delete integration |
| PATCH | `/tailnet/{tailnet}/device-attributes` | Batch update custom posture attributes |

## Invites

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/user-invites` | List user invites |
| POST | `/tailnet/{tailnet}/user-invites` | Create user invites |
| GET | `/user-invites/{userInviteId}` | Get user invite |
| DELETE | `/user-invites/{userInviteId}` | Delete user invite |
| POST | `/user-invites/{userInviteId}/resend` | Resend user invite |
| GET | `/device/{deviceId}/device-invites` | List device share invites |
| POST | `/device/{deviceId}/device-invites` | Create device share invites |
| GET | `/device-invites/{deviceInviteId}` | Get device invite |
| DELETE | `/device-invites/{deviceInviteId}` | Delete device invite |
| POST | `/device-invites/{deviceInviteId}/resend` | Resend device invite |
| POST | `/device-invites/-/accept` | Accept device invite |

## Tailnet Settings & Services

| Method | Endpoint |
|--------|----------|
| GET | `/tailnet/{tailnet}/settings` | Get tailnet settings |
| PATCH | `/tailnet/{tailnet}/settings` | Update tailnet settings |
| GET | `/tailnet/{tailnet}/services` | List Tailscale Services |
| GET | `/tailnet/{tailnet}/services/{serviceName}` | Get service |
| GET | `/tailnet/{tailnet}/services/{serviceName}/devices` | List service devices |
| GET | `/tailnet/{tailnet}/services/{serviceName}/device/{deviceId}/approved` | Check device approval |
| POST | `/tailnet/{tailnet}/services/{serviceName}/device/{deviceId}/approved` | Approve device for service |
| DELETE | `/tailnet/{tailnet}/services/{serviceName}/device/{deviceId}/approved` | Revoke device approval |

## AWS

| Method | Endpoint |
|--------|----------|
| POST | `/tailnet/{tailnet}/aws-external-id` | Create AWS external ID |
| GET | `/tailnet/{tailnet}/aws-external-id/{id}/validate-aws-trust-policy` | Validate trust policy |

## Other

| Method | Endpoint |
|--------|----------|
| GET | `/api/v2/whoami` | → Used (`whoami`) |
