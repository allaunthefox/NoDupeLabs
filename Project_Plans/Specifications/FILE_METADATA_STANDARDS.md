# NoDupeLabs File Metadata Standards

## Overview

This document defines the file metadata standards that NoDupeLabs must follow when creating metadata files during scanning. All file metadata must comply with industry standards for maximum compatibility and interoperability.

## Metadata Standards Compliance

### File Type Identification Standards

#### MIME Types (RFC 6838)

**Standard**: RFC 6838 - Media Type Specifications and Registration Procedures
**Reference**: https://tools.ietf.org/html/rfc6838

**Implementation Requirements**:
- Use IANA-registered MIME types
- Follow RFC 6838 for media type registration
- Use standard MIME type detection libraries

**Common MIME Types**:
- `text/plain` - Plain text files
- `application/json` - JSON files
- `image/jpeg` - JPEG images
- `image/png` - PNG images
- `video/mp4` - MP4 videos
- `audio/mpeg` - MP3 audio
- `application/pdf` - PDF documents

#### File Extensions (ISO/IEC 23001-4)

**Standard**: ISO/IEC 23001-4:2018 - Information technology — MPEG systems technologies — Part 4: Codec configuration representation
**Reference**: https://www.iso.org/standard/71041.html

**Implementation Requirements**:
- Use standard file extensions
- Map extensions to MIME types correctly
- Handle case sensitivity appropriately

### File Metadata Standards

#### Dublin Core Metadata (ISO 15836-1:2017)

**Standard**: ISO 15836-1:2017 - Dublin Core metadata element set
**Reference**: https://www.iso.org/standard/63555.html

**Required Metadata Elements**:

| Element | Description | Standard |
|---------|-------------|----------|
| `title` | Name of the resource | DCMI |
| `creator` | Entity responsible for creation | DCMI |
| `subject` | Topic of the resource | DCMI |
| `description` | Resource description | DCMI |
| `publisher` | Entity responsible for making available | DCMI |
| `contributor` | Entity contributing to creation | DCMI |
| `date` | Date associated with resource | DCMI (ISO 8601) |
| `type` | Nature or genre of resource | DCMI |
| `format` | Physical or digital manifestation | DCMI |
| `identifier` | Unambiguous reference | DCMI |
| `source` | Related resource | DCMI |
| `language` | Language of content | DCMI (ISO 639) |
| `relation` | Related resource | DCMI |
| `coverage` | Extent or scope | DCMI |
| `rights` | Rights management | DCMI |

#### EXIF Metadata (ISO 12234-1)

**Standard**: ISO 12234-1:2021 - Electronic still-picture imaging — Removable memory — Part 1: Basic removable memory model
**Reference**: https://www.iso.org/standard/75354.html

**Image Metadata Requirements**:

| Property | Description | Standard |
|----------|-------------|----------|
| `ImageWidth` | Image width in pixels | EXIF |
| `ImageHeight` | Image height in pixels | EXIF |
| `BitsPerSample` | Number of bits per component | EXIF |
| `Compression` | Compression scheme | EXIF |
| `PhotometricInterpretation` | Pixel composition | EXIF |
| `Orientation` | Image orientation | EXIF |
| `SamplesPerPixel` | Number of components per pixel | EXIF |
| `XResolution` | Horizontal resolution | EXIF |
| `YResolution` | Vertical resolution | EXIF |
| `ResolutionUnit` | Resolution unit | EXIF |
| `DateTime` | File change date/time | EXIF (ISO 8601) |
| `Artist` | Image creator | EXIF |
| `Copyright` | Copyright information | EXIF |
| `Make` | Camera manufacturer | EXIF |
| `Model` | Camera model | EXIF |
| `Software` | Software used | EXIF |
| `ExifVersion` | EXIF version | EXIF |
| `Flash` | Flash status | EXIF |
| `FocalLength` | Focal length | EXIF |
| `ExposureTime` | Exposure time | EXIF |
| `FNumber` | F-number | EXIF |
| `ISOSpeedRatings` | ISO speed | EXIF |
| `DateTimeOriginal` | Original date/time | EXIF (ISO 8601) |
| `DateTimeDigitized` | Digitization date/time | EXIF (ISO 8601) |

#### Audio Metadata (ID3v2)

**Standard**: ID3v2 - Audio metadata tagging
**Reference**: https://id3.org/id3v2.4.0-structure

**Audio Metadata Requirements**:

| Frame ID | Description | Standard |
|----------|-------------|----------|
| `TIT2` | Title/songname/content description | ID3v2 |
| `TPE1` | Lead performer(s)/Soloist(s) | ID3v2 |
| `TALB` | Album/Movie/Show title | ID3v2 |
| `TRCK` | Track number/Position in set | ID3v2 |
| `TYER` | Year | ID3v2 |
| `TDRC` | Recording time | ID3v2 (ISO 8601) |
| `TCON` | Content type | ID3v2 |
| `TCOM` | Composer | ID3v2 |
| `TCOP` | Copyright message | ID3v2 |
| `TPUB` | Publisher | ID3v2 |
| `TENC` | Encoded by | ID3v2 |
| `TSSO` | Software/Hardware and settings used for encoding | ID3v2 |
| `TLEN` | Length | ID3v2 |
| `TMED` | Media type | ID3v2 |
| `TFLT` | File type | ID3v2 |
| `TXXX` | User defined text information | ID3v2 |

#### Video Metadata (ISO/IEC 14496-12)

**Standard**: ISO/IEC 14496-12:2015 - Information technology — Coding of audio-visual objects — Part 12: ISO base media file format
**Reference**: https://www.iso.org/standard/68566.html

**Video Metadata Requirements**:

| Property | Description | Standard |
|----------|-------------|----------|
| `major_brand` | Major brand identifier | ISO BMFF |
| `minor_version` | Minor version | ISO BMFF |
| `compatible_brands` | Compatible brands | ISO BMFF |
| `creation_time` | Creation time | ISO BMFF (ISO 8601) |
| `modification_time` | Modification time | ISO BMFF (ISO 8601) |
| `duration` | Duration | ISO BMFF |
| `timescale` | Timescale | ISO BMFF |
| `language` | Language | ISO BMFF (ISO 639) |
| `width` | Video width | ISO BMFF |
| `height` | Video height | ISO BMFF |
| `codec` | Video codec | ISO BMFF |
| `bitrate` | Bit rate | ISO BMFF |
| `framerate` | Frame rate | ISO BMFF |

### File Hashing Standards

#### Cryptographic Hash Functions (FIPS 180-4)

**Standard**: FIPS 180-4 - Secure Hash Standard (SHS)
**Reference**: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf

**Supported Hash Algorithms**:

| Algorithm | Output Size | Standard |
|-----------|-------------|----------|
| `MD5` | 128 bits | RFC 1321 |
| `SHA-1` | 160 bits | FIPS 180-4 |
| `SHA-256` | 256 bits | FIPS 180-4 |
| `SHA-512` | 512 bits | FIPS 180-4 |
| `SHA-3-256` | 256 bits | FIPS 202 |
| `SHA-3-512` | 512 bits | FIPS 202 |

**Implementation Requirements**:
- Use FIPS 180-4 approved algorithms
- Follow NIST guidelines for cryptographic hashing
- Provide algorithm selection based on security requirements

### File System Metadata

#### POSIX File Attributes

**Standard**: IEEE 1003.1 (POSIX) - Portable Operating System Interface
**Reference**: https://pubs.opengroup.org/onlinepubs/9699919799/

**File System Metadata Requirements**:

| Attribute | Description | Standard |
|-----------|-------------|----------|
| `st_dev` | ID of device containing file | POSIX |
| `st_ino` | Inode number | POSIX |
| `st_mode` | File type and mode | POSIX |
| `st_nlink` | Number of hard links | POSIX |
| `st_uid` | User ID of owner | POSIX |
| `st_gid` | Group ID of owner | POSIX |
| `st_rdev` | Device ID (if special file) | POSIX |
| `st_size` | Total size in bytes | POSIX |
| `st_blksize` | Block size for filesystem I/O | POSIX |
| `st_blocks` | Number of 512B blocks allocated | POSIX |
| `st_atime` | Time of last access | POSIX (ISO 8601) |
| `st_mtime` | Time of last modification | POSIX (ISO 8601) |
| `st_ctime` | Time of last status change | POSIX (ISO 8601) |
| `st_birthtime` | Time of file creation | POSIX (ISO 8601) |

### Metadata Implementation Requirements

#### File Scanning Process

1. **File Identification**:
   - Detect MIME type using RFC 6838 standards
   - Verify file extension against ISO/IEC 23001-4
   - Use magic number detection for file format validation

2. **Metadata Extraction**:
   - Extract standard metadata based on file type
   - Follow domain-specific standards (EXIF, ID3, ISO BMFF)
   - Validate metadata against relevant standards

3. **Metadata Storage**:
   - Store metadata in standardized format
   - Use JSON Schema Draft 7 for validation
   - Support both JSON and JSON-L formats

4. **Metadata Validation**:
   - Validate against relevant ISO standards
   - Ensure compliance with domain-specific requirements
   - Provide validation reports

### Metadata Format Specification

#### JSON Metadata Format

```json
{
  "file": {
    "path": "/path/to/file.ext",
    "name": "file.ext",
    "extension": "ext",
    "size": 1024,
    "mime_type": "application/octet-stream",
    "hashes": {
      "md5": "d41d8cd98f00b204e9800998ecf8427e",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "attributes": {
      "created": "2023-01-01T00:00:00Z",
      "modified": "2023-01-01T00:00:00Z",
      "accessed": "2023-01-01T00:00:00Z",
      "permissions": "0644",
      "owner": "user",
      "group": "group"
    },
    "metadata": {
      "dublin_core": {
        "title": "File Title",
        "creator": "Author Name",
        "subject": "Subject",
        "description": "Description",
        "date": "2023-01-01",
        "type": "Document",
        "format": "application/octet-stream",
        "identifier": "unique-id",
        "language": "en"
      },
      "exif": {
        "ImageWidth": 1920,
        "ImageHeight": 1080,
        "DateTimeOriginal": "2023-01-01T00:00:00Z",
        "Make": "Camera Make",
        "Model": "Camera Model"
      },
      "id3": {
        "TIT2": "Song Title",
        "TPE1": "Artist",
        "TALB": "Album",
        "TRCK": "1/10",
        "TYER": "2023"
      },
      "iso_bmff": {
        "major_brand": "iso5",
        "minor_version": 512,
        "creation_time": "2023-01-01T00:00:00Z",
        "duration": 60000,
        "width": 1920,
        "height": 1080
      }
    }
  }
}
```

#### JSON-L Metadata Format

```json
{"file": {"path": "/path/to/file.ext", "name": "file.ext", "extension": "ext", "size": 1024, "mime_type": "application/octet-stream"}}
{"hashes": {"md5": "d41d8cd98f00b204e9800998ecf8427e", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}}
{"attributes": {"created": "2023-01-01T00:00:00Z", "modified": "2023-01-01T00:00:00Z", "permissions": "0644"}}
{"metadata": {"dublin_core": {"title": "File Title", "creator": "Author Name"}}}
{"metadata": {"exif": {"ImageWidth": 1920, "ImageHeight": 1080}}}
```

### Implementation Guidelines

#### Metadata Extraction Libraries

1. **Python**:
   - `python-magic` for MIME type detection
   - `Pillow` for EXIF metadata
   - `mutagen` for audio metadata
   - `hachoir` for video metadata

2. **JavaScript**:
   - `file-type` for MIME type detection
   - `exifr` for EXIF metadata
   - `music-metadata` for audio metadata
   - `strtok3` for video metadata

3. **Validation**:
   - Use JSON Schema Draft 7 for validation
   - Implement standard-specific validation
   - Provide detailed error reporting

### Compliance Verification

#### Validation Process

1. **Standard Compliance Check**:
   - Verify MIME types against IANA registry
   - Validate metadata against relevant ISO standards
   - Ensure hash algorithms follow FIPS standards

2. **Format Validation**:
   - Validate JSON/JSON-L format compliance
   - Check schema compliance using JSON Schema
   - Verify timestamp formats (ISO 8601)

3. **Domain-Specific Validation**:
   - Validate EXIF metadata structure
   - Check ID3 tag format compliance
   - Verify ISO BMFF container format

### Tabular Data Standards

#### CSV Format (RFC 4180)

**Standard**: RFC 4180 - Common Format and MIME Type for Comma-Separated Values (CSV) Files
**Reference**: https://tools.ietf.org/html/rfc4180

**Implementation Requirements**:
- Use comma as field separator
- Use double quotes for fields containing special characters
- Support CR+LF line endings
- Handle embedded commas and quotes properly
- Support header row for column names

**CSV Format Specification**:
```
column1,column2,column3
"value1","value2","value3"
"value with ""quotes""","value with, comma","value3"
```

#### TSV Format (ISO/IEC 27032)

**Standard**: ISO/IEC 27032:2012 - Information technology — Security techniques — Guidelines for cybersecurity
**Reference**: https://www.iso.org/standard/56627.html

**Implementation Requirements**:
- Use tab character (U+0009) as field separator
- No special quoting required for basic values
- Support CR+LF or LF line endings
- Handle embedded tabs and newlines
- Support header row for column names

**TSV Format Specification**:
```
column1	column2	column3
value1	value2	value3
value with	tab	value3
```

### Future Standards Integration

1. **Additional Metadata Standards**:
   - ISO 19115 for geospatial metadata
   - PREMIS for digital preservation metadata
   - METS for digital library metadata

2. **Extended Format Support**:
   - XML metadata formats
   - RDF metadata formats
   - Linked Data formats
   - CSV format (RFC 4180)
   - TSV format (ISO/IEC 27032)

3. **Automated Compliance**:
   - Automated metadata validation
   - Standard compliance reporting
   - Metadata quality metrics
   - Tabular data format validation

This file metadata standards specification ensures that all metadata created by NoDupeLabs during file scanning follows industry standards, providing maximum compatibility and interoperability with other systems and tools.
