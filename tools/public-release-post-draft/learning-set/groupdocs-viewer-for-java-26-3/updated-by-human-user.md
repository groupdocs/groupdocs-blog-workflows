---
title: "GroupDocs.Viewer for Java 26.3 – March 2026 Release Highlights"
seoTitle: "GroupDocs.Viewer for Java 26.3 – March 2026 Release"
description: "GroupDocs.Viewer for Java 26.3 fixes critical rendering bugs, improves performance, and adds new slide placeholder options—now available via Maven."
date: Wed, 25 Mar 2026 00:00:00 +0000
draft: false
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

| Key | Category | Summary |
| --- | --- | --- |
|VIEWERNET&#8209;5551|New feature|Add option to render placeholders in headers and footers of slide|
|VIEWERNET&#8209;5550|Bug|Content added to PowerPoint footer is not visible when rendering to all output formats|
|VIEWERNET&#8209;5530|Bug|Incorrect rendering of arabic fonts when converting DOCX to PDF|
|VIEWERNET&#8209;5408|Bug|Slow rendering speed PDF to HTML|
|VIEWERNET&#8209;4964|Bug|Malformed text during saving PDF to HTML when custom DefaultFontName is applied|
|VIEWERNET&#8209;4941|Bug|Intermittent Character rendering Errors on Windows Server 2019|
|VIEWERNET&#8209;5024|Bug|PDF to HTML: Text not converted correctly|
|VIEWERNET&#8209;5514|Bug|Incorrect processing of explicit page numbering during consecutive calls for Spreadsheet formats family|
|VIEWERNET&#8209;5513|Bug|Invalid WordProcessing document generation in trial mode with explicitly specified page number is out of trial limit|
|VIEWERNET&#8209;5480|Bug|PDF rendering is completely broken|
|VIEWERNET&#8209;5515|Bug|TIFF rendering throws exception with Cross-platform Viewer on Linux|
|VIEWERNET&#8209;4540|Bug|PDF file displayed incorrectly, with letters changed and lines shifted|
|VIEWERNET&#8209;5516|Bug|Invalid WordProcessing to PDF view generation in licensed mode when passed a page number greater than the total number of pages in the document|
|VIEWERNET&#8209;5577|Improvement|Implement detection and wrapping of raw URIs in mail message body|
|VIEWERNET&#8209;5550|Bug|Content added to PowerPoint footer is not visible when rendering to all output formats (reopened from v25.11)|
|VIEWERNET&#8209;5241|Bug|Formatting of numbers, datetimes and money values is broken when converting PDF to HTML|
|VIEWERNET&#8209;4709|Bug|PDF to HTML: Whole resultant file become link|
|VIEWERNET&#8209;5568|Bug|Hyperlinks in email body are not clickable|
|VIEWERJAVA&#8209;4048|Bug|XLSX to HTML: Autofit is not applied for row number|
|VIEWERJAVA&#8209;4058|Bug|NullPointerException in font resolution on Docker due to missing LOCALAPPDATA|
|VIEWERJAVA&#8209;4060|Enhancement|Excel rendering produces low-resolution text compared to PDF when converting to JPG ( or PNG)|

## Public API changes

**Added**

`com.groupdocs.viewer.options.PresentationOptions.isRenderHeaderFooterPlaceholders()` boolean property (VIEWERNET&#8209;5551)

**Removed**

None


## New Features

- Added `HorizontalResolution` and `VerticalResolution` properties to the [SpreadsheetOptions](https://reference.groupdocs.com/viewer/java/com.groupdocs.viewer.options/spreadsheetoptions/) class, allowing users to control the output image resolution (in DPI) when rendering spreadsheets to PNG and JPEG formats.

## Code Example

```java
Path pageFilePathFormat = Paths.get("page_{0}.png");

PngViewOptions viewOptions = new PngViewOptions(pageFilePathFormat);
viewOptions.getSpreadsheetOptions().setHorizontalResolution(300);
viewOptions.getSpreadsheetOptions().setVerticalResolution(300);
try (Viewer viewer = new Viewer("sample.xlsx")) {
    viewer.view(viewOptions);
}
```

## How to get the update

Add the following dependency to your `pom.xml` (or the equivalent entry in Gradle) to use version 26.3:

```xml
<dependency>
    <groupId>com.groupdocs</groupId>
    <artifactId>groupdocs-viewer</artifactId>
    <version>26.3</version>
</dependency>
```

### Direct download
Alternatively, download the compiled JARs from the official release page:  
https://releases.groupdocs.com/viewer/java/

---
