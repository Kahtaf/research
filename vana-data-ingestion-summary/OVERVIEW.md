# Vana Data Ingestion Research: High-Level Summary

## Objective

Standardize data ingestion across multiple source types (web apps, native apps, IoT, streaming video) with cryptographic data provenance using zkTLS. The goal is to replace Reclaim Protocol with a custom solution optimized for Vana's specific requirements.

**Success Criteria**: Deliver a data ingestion pipeline that:
- Handles all required data sources comprehensively
- Provides exceptional user experience that discourages network participants from building competing solutions
- Maintains cryptographic proof of data authenticity

Our data ingestion pipeline consists of two core components:

1. **Data Capture**: Intercepting or extracting data from its source silo
2. **Data Provenance**: Cryptographically proving data authenticity and source attribution

---

## Data Source Requirements

The following table outlines the various data source types and their associated challenges:

| Source Type | Example | Key Challenge |
|-------------|---------|---------------|
| **Web Apps and APIs** | Uber, Spotify, Wells Fargo | Scraping scripts break when applications change |
| **Native Apps** | Snapchat, M-Pesa, Paytm | HTTPS interception, certificate pinning, OS-level restrictions |
| **Streaming Data** | Kafka, MQTT, WebSockets | Real-time capture, continuous data flow vs. request/response |
| **File Uploads** | Dashcam SD card footage | Difficult to establish reliable provenance |

---

# Data Ingestion

The following sections detail research findings on data capture and provenance approaches for the ingestion pipeline.

## Data Capture

Data capture involves intercepting, copying, or otherwise accessing data to extract it from its silo. Techniques vary by source type and include web scraping, MITM proxies for HTTPS traffic inspection, data sink provisioning for streaming sources, and other specialized methods.

### Web Apps

**Current Approach**: Reclaim Protocol captures web app data but provides suboptimal user experience.

**Proposed Solution**: Leverage Vana's native app to open target websites in a WebView with custom JavaScript injection for data extraction. This approach enables:
- Scraping of rendered web content
- Interception of XHR traffic to capture API requests/responses
- Custom navigation and authentication flows

**Proof of Concept**:
- Source code (Flutter): [flutter-webview-scraper](https://github.com/vana-com/flutter-webview-scraper)
- Demo: [Loom video](https://www.loom.com/share/23120c0f1d344320b0f6564f4e01a465)

The PoC adapts JavaScript from existing Reclaim Providers by removing Reclaim dependencies and routing captured data to the Flutter application.

**Future Enhancement**: Enable open-source contribution of data scrapers compatible with the app. AI-powered tools could automate testing and implement self-healing capabilities when source website changes break existing scripts.

---

### Native Apps

Some services are exclusively available through iOS or Android applications without web equivalents. Accurate data capture from these apps requires intercepting HTTPS traffic between the app and backend server.

**Technical Challenges**:
- MITM proxy setup requires custom root certificate installation
- Certificate installation involves multiple steps and triggers OS security warnings
- Certificate pinning prevents interception even with installed certificates—apps validate against hardcoded certificates that cannot be modified without device or application modification
  - Additional details: [Certificate Pinning Documentation](https://github.com/Kahtaf/research/blob/main/native-app-traffic-capture/certificate-pinning.md)

**Research**: Comprehensive approach comparison available in [Native App Traffic Capture Report](https://github.com/Kahtaf/research/blob/main/native-app-traffic-capture/README.md)

**Recommended Approach**: Deploy Android device emulation on cloud VMs with pre-installed root certificates, enabling MITM proxy traffic capture. Stream the emulated device to the user's browser for authentication and interaction.

**Work in Progress**: [Android MITM MVP](https://github.com/Kahtaf/research/tree/main/native-app-traffic-capture/android-mitm-mvp)

---

### Streaming Data

*Research in progress*

---

### File Uploads

File uploads serve as a fallback mechanism for data that cannot be captured at its source—either because it has already left the origin system or the origin is inaccessible. Example use case: dashcam footage stored on SD cards.

**Limitation**: Establishing data provenance is extremely challenging for file uploads, making this approach suitable only as a last resort.

---

## Data Provenance

Data provenance establishes cryptographic proof that captured data originated from a specific source and remains unmodified through upload to Vana.

**Ongoing Research**: [zkTLS Investigation](https://github.com/Kahtaf/research/tree/main/zk-tls)

---

# Recommendations

*To be completed following zkTLS research conclusion*
