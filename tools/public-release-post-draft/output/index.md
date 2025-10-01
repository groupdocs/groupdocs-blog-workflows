---
title: "GroupDocs.Total for .NET 25.8 – September 2025 Release Highlights"
seoTitle: "GroupDocs.Total for .NET 25.8 – Latest Updates and Fixes (September 2025)"
description: "Explore what’s new in GroupDocs.Total for .NET 25.8. Available now on NuGet and GroupDocs website."
date: Wed, 01 Oct 2025 00:00:00 +0000
draft: false
url: /total/groupdocs-total-for-net-25-8/
author: "GroupDocs Team"
summary: "GroupDocs.Total for .NET 25.8 is here."
tags: ['GroupDocs.Total', '.NET', 'Releases']
categories: ['GroupDocs.Total Releases']
showToc: true
tocOpen: true
cover:
    image: /total/groupdocs-total-for-net-25-8/images/groupdocs-total-for-net-25-8.png
    alt: "GroupDocs.Total for .NET 25.8 – September 2025 Release Highlights"
    caption: "GroupDocs.Total for .NET 25.8 – September 2025 Release Highlights"
    hidden: false
---

We’re happy to announce the **GroupDocs.Total for .NET 25.8** release, available as of **September 2025**. This update brings a few critical bug fixes, an important packaging change, and the usual version upgrades of the individual libraries that compose the Total suite.

## Important notice

> Starting with this version **GroupDocs.Classification** is no longer shipped inside the **GroupDocs.Total** package.  
> The classification library adds large machine‑learning model files, which increased the overall package size and affected performance for users who do not need classification capabilities.  
> If you rely on classification, add the library separately (see the **GroupDocs.Classification** NuGet package or its own release notes).

## Fixes

| Issue | Product | Description |
|-------|-----------|-------------|
| **TOTALNET‑204** | Conversion | Fixed incorrect table formatting when converting HTML → PDF. |
| **TOTALNET‑287** | Annotation | Resolved missing localized string error: “CONSTRUCTOR.WITH.PARAMETERS.STARTED” key does not exist. |
| **TOTALNET‑298** | Viewer | Fixed a null‑reference exception that occurred on diagram rendering. |

No new public‑API features or enhancements were introduced in this release.

## How to get the update

- **NuGet** – Upgrade the **GroupDocs.Total** package (or the .NET Framework‑specific package) to the latest version:  

  * [.NET 6 / .NET Standard 2.0]([https://www.nuget.org/packages/GroupDocs.Total](https://www.nuget.org/packages/GroupDocs.Total))  
  * [.NET Framework 4.6.2 +]([https://www.nuget.org/packages/GroupDocs.Total.NETFramework](https://www.nuget.org/packages/GroupDocs.Total.NETFramework))

- **Direct download** – Grab the compiled assemblies for both .NET 6 and .NET Framework from the **[GroupDocs.Total for .NET 25.8 download page]**(https://releases.groupdocs.com/total/net/#direct-download).

## Learn more

- **Full release notes** – Detailed change log for each library in the suite:  

  * [GroupDocs.Conversion 25.8]([https://releases.groupdocs.com/conversion/net/release-notes/2025/groupdocs-conversion-for-net-25-8-release-notes/])  
  * [GroupDocs.Viewer 25.8]([https://releases.groupdocs.com/viewer/net/release-notes/2025/groupdocs-viewer-for-net-25-8-release-notes/])  
  * [GroupDocs.Comparison 25.8]([https://releases.groupdocs.com/comparison/net/release-notes/2025/groupdocs-comparison-for-net-25-8-release-notes/])  
  * …and the other components listed in the release notes table.

- **Documentation** – Comprehensive API reference and usage guides: <https://docs.groupdocs.com/total/net/>

- **Support** – Post questions, report issues, or share feedback on the **[GroupDocs.Total Free Support Forum]**(https://forum.groupdocs.com/c/total/8).

---
