+++
title = "FLIM Playground"
date = 2024-12-06
lastmod = 2026-08-16
draft = false
interactionId = "flim-playground"
tags = ["data visualization", "FLIM", "research", "biomedical imaging"]
projectStatus = "current"
+++

![](logo.png)

We hope this project will be useful in providing a rigorous yet frictionless experience, with a tinge of fun, for biologists when they are trying to extract insights from raw microscopy data including FLIM (fluorescence lifetime imaging microscopy) and other microscopy modalities (e.g. brightfield, QPI, etc.).

The idea and vision behind is illustrated in the journel cover and its legend. ([Cell Reports Methods Volume 6, Issue 8](https://www.cell.com/cell-reports-methods/issue?pii=S2667-2375(25)X0009-6))

{{< side-by-side src="flim_pg_cover.jpg" alt="FLIM Playground hopscotch court overview" >}}
A hopscotch court chalked on pavement maps FLIM Playground end-to-end. From square 1, the player hops through each step the software unifies: identifying fields of view; calibrating unprocessed photon decays; extracting single-cell fit, phasor, morphology, and texture features; merging datasets into a unified table; tagging each cell; and analyzing them through interactive widgets—iterative, frictionless, exploratory, and intuitive. A once-fragmented, code-heavy trek becomes one court, hopped back and forth as each biological question suggests the next. Chalk, inexpensive and open to all, echoes *Zhao et al*.’s paper’s advance: an open-source, code-free platform everyone can play on.
{{< /side-by-side >}}


Conceptually, it is divided into two 
integrated yet independent sections: 
- **Data Extraction** that extracts multichannel, multimodal, single-region-of-interest (e.g. single-cell) features, and 
- **Data Analysis** that provides interactive visualization and statistical modeling across these features or on *any* tabular datasets. 

To learn more, here are some useful links: 

- [Open-source code and cross-platform releases](https://github.com/skalalab/flim_playground)
- [Documentation](https://skalalab.github.io/flim_playground_doc/)
- [Paper](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(26)00184-0)
