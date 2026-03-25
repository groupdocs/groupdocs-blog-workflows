---
title: "GroupDocs.Viewer for Java 26.3 – March 2026 Release Highlights"
seoTitle: "GroupDocs.Viewer for Java 26.3 – March 2026 Release"
description: "GroupDocs.Viewer for Java 26.3 fixes critical rendering bugs, improves performance, and adds new slide placeholder options—now available via Maven."
date: Wed, 25 Mar 2026 00:00:00 +0000
draft: true
url: /viewer/groupdocs-viewer-for-java-26-3/
author: "GroupDocs Team"
summary: "GroupDocs.Viewer for Java 26.3 delivers key bug fixes across PDF, Word, Excel, PowerPoint, and image conversions, plus a new rendering option for slide placeholders."
tags: ['GroupDocs.Viewer', 'Java', 'Releases', 'Bug Fixes', 'PDF', 'HTML']
categories: ['GroupDocs.Viewer Releases']
showToc: true
tocOpen: true
cover:
    image: /viewer/groupdocs-viewer-for-java-26-3/images/groupdocs-viewer-for-java-26-3.png
    alt: "GroupDocs.Viewer for Java 26.3 – March 2026 Release"
    caption: "GroupDocs.Viewer for Java 26.3 – March 2026 Release"
    hidden: false
---

GroupDocs.Viewer for Java 26.3 is now available. This minor update introduces a new rendering option for slide placeholders and resolves a wide range of bugs affecting PDF, PowerPoint, Excel, Word, and image conversions.

## What's new in this release
* **GroupDocs.Viewer for Java 26.3** (25.12 → 26.3)

### Fixes
| Issue | Product | Description |
|-------|---------|-------------|
| VIEWERNET-5550 | GroupDocs.Viewer for Java | Fixed a regression where content added to PowerPoint footers was not visible in any output format. The fix restores proper rendering of footer elements across PDF, PNG, and HTML outputs. |
| VIEWERNET-5530 | GroupDocs.Viewer for Java | Corrected incorrect rendering of Arabic fonts when converting DOCX files to PDF. The issue was caused by improper Unicode handling and is now resolved. |
| VIEWERNET-5408 | GroupDocs.Viewer for Java | Addressed slow rendering performance when converting PDF to HTML. Optimizations in the HTML generation pipeline reduce processing time significantly. |
| VIEWERNET-4964 | GroupDocs.Viewer for Java | Fixed malformed text that appeared when saving PDF to HTML while a custom `DefaultFontName` was set. The font substitution logic now respects the custom default without corrupting the output. |
| VIEWERNET-4941 | GroupDocs.Viewer for Java | Resolved intermittent character rendering errors observed on Windows Server 2019. The fix stabilizes glyph mapping under the server’s font configuration. |
| VIEWERNET-5024 | GroupDocs.Viewer for Java | Corrected text conversion errors during PDF‑to‑HTML rendering. Text blocks now retain their original content and layout. |
| VIEWERNET-5514 | GroupDocs.Viewer for Java | Fixed incorrect processing of explicit page numbering in consecutive calls for Spreadsheet formats. Page numbers are now applied consistently across multiple renderings. |
| VIEWERNET-5513 | GroupDocs.Viewer for Java | Resolved an issue where WordProcessing document generation in trial mode failed when the specified page number exceeded the trial limit. The viewer now gracefully handles out‑of‑range page requests. |
| VIEWERNET-5480 | GroupDocs.Viewer for Java | Repaired a complete breakage of PDF rendering that could result in empty output. The rendering engine now correctly parses and displays PDF content. |
| VIEWERNET-5515 | GroupDocs.Viewer for Java | Fixed an exception thrown while rendering TIFF images with the cross‑platform viewer on Linux. The TIFF decoder now works reliably in containerized environments. |
| VIEWERNET-4540 | GroupDocs.Viewer for Java | Addressed visual distortions where letters were altered and lines shifted in PDF output. The layout engine now preserves original typography. |
| VIEWERNET-5516 | GroupDocs.Viewer for Java | Corrected invalid WordProcessing‑to‑PDF view generation in licensed mode when a page number greater than the document’s total pages was supplied. The viewer now returns a proper error instead of corrupt output. |
| VIEWERNET-5241 | GroupDocs.Viewer for Java | Fixed broken formatting of numbers, dates, times, and monetary values when converting PDF to HTML. Locale‑aware formatting is now applied correctly. |
| VIEWERNET-4709 | GroupDocs.Viewer for Java | Resolved an issue where the entire PDF‑to‑HTML result became a single hyperlink. Link detection logic now respects original document structure. |
| VIEWERNET-5568 | GroupDocs.Viewer for Java | Made hyperlinks in email bodies clickable again. The HTML renderer now preserves anchor tags during conversion. |
| VIEWERJAVA-4048 | GroupDocs.Viewer for Java | Fixed missing autofit for row numbers in XLSX‑to‑HTML conversion. Row heights are now automatically adjusted to fit content. |
| VIEWERJAVA-4058 | GroupDocs.Viewer for Java | Fixed a `NullPointerException` in font resolution on Docker containers caused by an absent `LOCALAPPDATA` variable. The viewer now falls back to a safe default path. |
| VIEWERNET-5577 | GroupDocs.Viewer for Java | Implemented detection and automatic wrapping of raw URIs in email message bodies. This improves readability and ensures proper hyperlink rendering. |

## How to get the update
### Maven
Add the following dependency to your `pom.xml` (or the equivalent entry in Gradle) to use version 26.3:

```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-viewer-java</artifactId>
    <version>26.3</version>
</dependency>
```

### Direct download
*Download the JAR files for GroupDocs.Viewer 26.3 from the official GroupDocs releases page.*  
(Exact URL is provided on the GroupDocs website.)

## Resources
* [SpreadsheetOptions documentation](https://reference.groupdocs.com/viewer/java/com.groupdocs.viewer.options/spreadsheetoptions/)  

---
