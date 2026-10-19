# Mobile spacing baseline

Use only as a starting hypothesis and verify the current mobile density and token values.

| Relationship | Preferred token | Typical default |
| --- | --- | ---: |
| Page horizontal padding | `padding` | 16px |
| Page top padding | `padding` | 16px |
| Page bottom padding | `paddingLG` | 24px |
| Section gap | `marginLG` | 24px |
| Module gap | `margin` | 16px |
| Module content gap | `marginSM` | 12px |
| Element gap | `marginXS` | 8px |
| Micro gap | `marginXXS` | 4px |

Keep PC and H5 on the same Ant token system while allowing different layout density. Avoid splitting components solely for tiny spacing differences. Ordinary pages must not calculate safe area independently; delegate it to shared mobile layout infrastructure.
