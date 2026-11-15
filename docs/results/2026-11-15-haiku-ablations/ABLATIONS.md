# Ablation results (Claude Haiku agents, 5 NDAs, oracle rules: see README.md)

## RQ1 ablations

Base: `full`, 5 NDAs, paired bootstrap, Holm-corrected over the ablations.

| Ablation | P | R | F1 | ΔF1 (95% CI) | p (Holm) | Omission R | FA/NDA | Tokens/NDA | Expected effect |
|---|---|---|---|---|---|---|---|---|---|
| full | 0.8205 | 0.6038 | 0.6957 | — | — | 0.6 | 1.4 | 38996.0 |  |
| b2 | 0.2778 | 0.0943 | 0.1408 | -0.555 [-0.588, -0.517] | <0.001 (raw) | 0.0 | 2.6 | 28872.0 |  |
| b2_checklist | 0.3924 | 0.5849 | 0.4697 | -0.226 [-0.286, -0.176] | <0.001 (raw) | 0.4571 | 9.6 | 122665.0 |  |
| b3 | 1.0 | 0.1698 | 0.2903 | -0.405 [-0.570, -0.269] | <0.001 (raw) | 0.0286 | 0.0 | 35494.8 |  |
| fixed_pipeline | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 38607.0 | tokens per NDA up |
| no_filter | 0.5246 | 0.6038 | 0.5614 | -0.134 [-0.192, -0.085] | <0.001 | 0.6 | 5.8 | 66623.0 | false alarms per NDA up |
| no_frames | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 37771.2 | violation recall (field rules) down |
| no_memory | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 40093.4 | escalations per NDA up |
| no_reverse | 0.6875 | 0.2075 | 0.3188 | -0.377 [-0.435, -0.333] | <0.001 | 0.0 | 1.0 | 21254.2 | omission recall down |
| no_tool_agent | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 32991.0 | hand-off precision down |
| no_verifier | 0.8293 | 0.6415 | 0.7234 | +0.028 [+0.000, +0.063] | 1.000 | 0.6 | 1.4 | 34808.2 | precision down |
| no_xref | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 38830.0 | approval-needed recall down |
| reviewer:exhaustive_filtered | 0.7381 | 0.5849 | 0.6526 | -0.043 [-0.078, -0.018] | 0.001 (raw) | 0.4571 | 2.2 | 56550.2 |  |
| reviewer:full | 0.8095 | 0.6415 | 0.7158 | +0.020 [-0.017, +0.063] | 0.357 (raw) | 0.6 | 1.6 | 26879.4 |  |
| tool_errors | 0.8205 | 0.6038 | 0.6957 | +0.000 [+0.000, +0.000] | 1.000 | 0.6 | 1.4 | 38996.0 | recovery rate / F1 down |

