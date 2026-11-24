# M3 contour evidence — November 24, 2026

Exact source Git blobs: full `84bba8beaba9ec557d05f5426e958233f00d3605`, monogram `8c8b9cad7ad96ffae49f778b78d09f7ce29b82cb`. Both fetched read-only and decoded at native resolution. Alpha >=128; isolated four-connected components below 32 pixels discarded; material classified per whole component using majority warmth. Expected 2/1/6/16 glyph groups enforced. Contours follow pixel edges and are simplified at 0.65 px. Rasterized contours compared to cleaned mask (not raw antialiased coverage or original vector). These metrics are not human creative approval.

```json
{
  "version": 1,
  "width": 1536,
  "height": 934,
  "monogramAgreement": 1,
  "discardedSmallPixels": 651,
  "groups": [
    {
      "id": 1,
      "count": 63164,
      "bbox": [
        277,
        108,
        1209,
        479
      ],
      "tiny": 4,
      "iou": 0.998829336201987,
      "fp": 48,
      "fn": 26,
      "vertices": 1210,
      "outer": 2,
      "holes": 1,
      "name": "silver-monogram",
      "components": 2
    },
    {
      "id": 2,
      "count": 25995,
      "bbox": [
        631,
        115,
        999,
        529
      ],
      "tiny": 0,
      "iou": 0.9991156907224422,
      "fp": 14,
      "fn": 9,
      "vertices": 640,
      "outer": 1,
      "holes": 0,
      "name": "gold-r",
      "components": 1
    },
    {
      "id": 3,
      "count": 18684,
      "bbox": [
        243,
        587,
        1239,
        688
      ],
      "tiny": 3,
      "iou": 0.9963667450309895,
      "fp": 32,
      "fn": 36,
      "vertices": 996,
      "outer": 6,
      "holes": 1,
      "name": "silver-wordmark",
      "components": 6
    },
    {
      "id": 4,
      "count": 22748,
      "bbox": [
        219,
        739,
        1269,
        799
      ],
      "tiny": 1,
      "iou": 0.9967070600632244,
      "fp": 28,
      "fn": 47,
      "vertices": 1782,
      "outer": 16,
      "holes": 8,
      "name": "gold-descriptor",
      "components": 16
    }
  ]
}
```

Actual committed pure tracing functions exercised against both original PNGs in a JS runtime using a test DEFLATE decoder. CLI uses built-in Node zlib; filesystem entry point not executed here. Original PNGs and derived geometry remain private; no artwork bytes or coordinates committed. Native Blender mesh/render and human review still pending.