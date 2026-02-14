# OpenAPI Specification Documentation

This document describes the NoDupeLabs API specification compliance with **OpenAPI Specification 3.1.2** (September 2025).

## Overview

NoDupeLabs implements the OpenAPI Specification 3.1.2 for documenting its CLI commands and plugin system. While NoDupeLabs is primarily a library/CLI tool (not an HTTP API), the OpenAPI spec provides a machine-readable format for:

- CLI command documentation
- Plugin metadata schemas
- Error response standardization
- Future HTTP API compatibility

## Specification Location

- **Primary**: `docs/openapi.yaml`
- **Version**: OpenAPI 3.1.2
- **Format**: YAML

## Compliance Level

This implementation follows OpenAPI 3.1.2 strictly:

### Required Fields (OAS 3.1.2 §4.8.1)

| Field | Status | Implementation |
|-------|--------|----------------|
| `openapi` | ✅ | `3.1.2` |
| `info` | ✅ | Title, version, description, license |
| `paths` | ✅ | CLI command paths |
| `components` | ✅ | Schemas, security schemes |

### Optional Fields

| Field | Status | Implementation |
|-------|--------|----------------|
| `servers` | ✅ | Local CLI server placeholder |
| `tags` | ✅ | Core, Plugin, Config |
| `webhooks` | N/A | Not applicable |
| `externalDocs` | ✅ | Referenced in info |

## API Structure

### Paths

| Path | Method | Operation | Description |
|------|--------|-----------|-------------|
| `/version` | GET | `getVersion` | Show version info |
| `/plugin` | GET | `listPlugins` | List loaded plugins |

### Schemas

#### VersionInfo
```yaml
type: object
required: [version]
properties:
  version: string    # Semantic version
  platform: string   # Drive type (ssd/hdd)
  cores: integer    # CPU cores
  ram_gb: integer  # RAM in GB
```

#### PluginInfo
```yaml
type: object
required: [name]
properties:
  name: string
  version: string
  type: enum[similarity, storage, command, time_sync]
```

#### Error
```yaml
type: object
required: [message]
properties:
  code: integer
  message: string
```

## Usage

### Viewing the Specification

```bash
# View raw YAML
cat docs/openapi.yaml

# Validate with Redocly
npx redocly lint docs/openapi.yaml

# View with Swagger UI
npx swagger-ui-static -o docs/openapi.yaml
```

### Generating Documentation

```bash
# Install OpenAPI tools
pip install openapi-spec-validator

# Validate spec
python -c "import openapi_spec_validator; openapi_spec_validator.validate_spec_file('docs/openapi.yaml')"
```

### CI Integration

The OpenAPI spec is validated in CI via:

```bash
# Validate YAML syntax
python tools/core/enforce_yaml_spec.py --check docs/openapi.yaml
```

## Extensions

NoDupeLabs-specific extensions use the `x-nodupelabs` prefix:

```yaml
x-nodupelabs:
  stability: stable  # STABLE, BETA, EXPERIMENTAL
  since: 1.0.0     # Version when added
```

## Security Schemes

| Scheme | Type | Usage |
|--------|------|-------|
| `API_KEY_REMOVED` | API Key | Header-based authentication |

## References

- [OpenAPI Specification 3.1.2](https://spec.openapis.org/oas/v3.1.2.html)
- [OpenAPI Initiative](https://www.openapis.org/)
- [JSON Schema Draft 2020-12](https://json-schema.org/specification-links.html#2020-12)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-14 | Initial OpenAPI 3.1.2 spec |
