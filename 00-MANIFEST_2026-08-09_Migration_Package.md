# 00-MANIFEST_2026-08-09 — بيان جرد حزمة الترحيل

| الحقل | البيان |
| :--- | :--- |
| **الغرض** | ترحيل قاعدة المعرفة إلى مشروع جديد |
| **حالة الاعتماد** | مشتق — جرد آلي · لا يضيف مفهوماً ولا يعدّل خط الأساس |
| **آخر قرار مختوم** | `DEC-248` · التالي `DEC-249` |
| **آخر تغيير** | `CHG-066` |
| **عدد الملفات** | **247** |
| **السند في الإسقاط** | `CHG-054` · `00-MANIFEST_2026-08-05` §3 |

---

# §1 سجلّ الإسقاط — ثلاثة ملفات · **غيابها مقصود لا عَرَضي**

| الملف | العلّة | السند | التحقق |
| :--- | :--- | :--- | :--- |
| `packs.js` | **مولَّد** بـ`build_packs.py` | `CHG-054` | ✅ غائب |
| `Kashaf.html` | تعيش في المحادثة | `CHG-054` | ✅ غائب |
| `golden_k3_PRE-DEC-215.json` | حالات ذهبية **سابقة لـ`DEC-215`** — أُسقطت بأمر المالك 2026-08-09 | `CHG-054` | ✅ غائب |

> **لا يُعاد رفع أيٍّ منها.** وجود أيٍّ منها في قاعدة معرفة لاحقة ⇒ خرق `CHG-054` ⇒ توقّف وأبلغ.

---

# §2 التوزيع حسب الطبقة

| الامتداد | العدد |
| :--- | ---: |
| `.md` | 190 |
| `.py` | 28 |
| `.json` | 20 |
| `.js` | 8 |
| `.css` | 1 |

---

# §3 بوابة التحقق بعد الرفع — تُجتاز قبل أي بناء

| # | الفحص | معيار النجاح |
| :--- | :--- | :--- |
| 1 | عدّ الملفات | **247** |
| 2 | مطابقة بصمات §4 | 247/247 |
| 3 | سجلّ الإسقاط §1 | ثلاثة غائبة |
| 4 | بوابة الاستئناف | `00-HANDOVER_2026-08-05` §1 — **7/7** |
| 5 | الأدوات الستّ عشرة | 16/16 · البصمات الثلاث حرفياً |

**البصمات الثلاث:** `2711c24d8155819b` · `36ae94bfd5a8b60f` · `6b324f996856eac3`

---

# §4 جدول البصمات — SHA-256

| # | الملف | الحجم (بايت) | SHA-256 |
| :--- | :--- | ---: | :--- |
| 1 | `00-CROSSMAP_K1_Code_Equivalence_Table.md` | 5131 | `3060002296a7bc10657cd45a015e45ab1c55be470a4a3ec49a07a8edf725264d` |
| 2 | `00-HANDOVER_2026-08-05_Resume_Directive.md` | 8961 | `e767f7d51cca3af2d0c3351940e5e75ed5406c22e05cfe1c9e7625f602c320db` |
| 3 | `00-INDEX_Master_Knowledge_Base_Index.md` | 39208 | `779317a7acf3030c257f54b7efd7dafe7d9be3cf02d2f469a7686923a5f2f05b` |
| 4 | `00-MANIFEST_2026-08-05_Upload_List.md` | 3523 | `f356eba9b1709975ab444c858cab64145b5f397409d3ad1c050900efe449e636` |
| 5 | `00-MANIFEST_2026-08-09_Migration_Package.md` | 2645 | `90b0e1b4bfe25a1f5fd1ba6adff8e45adb198444d2c144374253c8634197601d` |
| 6 | `00-MANIFEST_Upload_And_Sync_Checklist.md` | 22421 | `bd3a3019c8141064d9407cf2af7200bff1c0835d283db3f203395433024969e8` |
| 7 | `00-PATCHPACK_2026-07-21_Baseline_Sync.md` | 15492 | `4a29a4b1a3c5e3f576d588945515adcc79368ae2e367096689f322b2d031dca8` |
| 8 | `00-PATCH_Blueprint_Archival.md` | 4272 | `3ee83d51db25be47acf1e80768ec4b72d0e1b438dd096ff88563c217d79d0d88` |
| 9 | `00-PATCH_CRITIQUE-GATE_Check-10_Title_Content_Match.md` | 9173 | `86213cf7582fd3a9ab12a11510292c07ee4c5d21863719b37f93b8f58ff955cf` |
| 10 | `00-PATCH_DEC-191-192_Rebase_And_Regression_Sync.md` | 6443 | `f626ea5d21b951fea049734e17d62a7338f4cdf201e6748bafe433513b391536` |
| 11 | `00-PATCH_ENGINE-APPENDIX-A_Closed_List_Expansion.md` | 6671 | `00e2fe8d09f9a638f6e00ae15793031a5aadc4dc9af1eb25c3ecaaad60a25bea` |
| 12 | `00-PATCH_K2-NEUTRALIZATION_2026-07-28_Ready_To_Paste.md` | 11971 | `672e7dc280b3f48e079bb5f32106dfee27d87c456a31b617ff19517975990e31` |
| 13 | `00-PATCH_M3-06_Compensation_Ban_Text.md` | 3113 | `8a5c3c48e7f6124e89a09bfedf5b701f736b67e713f8b8311df5fb90d9688fa0` |
| 14 | `00-PROTOCOL_Self_Critique_Gate.md` | 15686 | `b757e8f8a72cfc66280b4f4925f188135c8a3238bb4cf76ec447fce803232700` |
| 15 | `00-SESSION-CLOSE_2026-07-07_Final_Changelog.md` | 9188 | `d003a0d2932f5569a27dbfc82a4a7b5a5ed4623a48fa7e2f03bdf5e4737a5b23` |
| 16 | `00-SESSION-CLOSE_2026-07-18_K3_Build_Handover.md` | 7308 | `fc14c9c7dfaef4d07c5e53f950b7b1c40c3f1ad085844d18fff581f368aaf4ab` |
| 17 | `00-SESSION-CLOSE_2026-07-21_Step5_Closure_And_Handover.md` | 8858 | `3c84594fae6d89ee975ef661ba632edeecac92a7191d19b795a483df94533ae5` |
| 18 | `00-SESSION-CLOSE_2026-07-27_ContentPack_And_First_Report.md` | 9968 | `a0126d6e94f44ddcfec000faca4bfaa524d9ec0b5189ef64cddca58c76db3292` |
| 19 | `00-SESSION-CLOSE_2026-08-02_Build_Mode_Closure.md` | 8703 | `97c95f7f43885dcc49ec56962057db658ed17db3e8a65a2c453ae2abde4dc97f` |
| 20 | `00-SESSION-CLOSE_2026-08-03_Final.md` | 9654 | `6784e1e2f54a16eac78f8e028db81007564e44544010ec9439a1ddbc306703d2` |
| 21 | `00-SESSION-K3_Sync_Package_And_Decision_Log.md` | 29729 | `82d8113d4a91476ebf72e95f5914575a7b68ed19f84374ddd1689eb25bf36da0` |
| 22 | `00-SESSION-UPDATE_2026-07-21_Coupling_Layer_Sync_Package.md` | 21160 | `42de3ae8e30548ef0c3d32ebc3439631b22fca34ee8fd7c2a09532f559c5217c` |
| 23 | `00-SESSION-UPDATE_2026-07-28_Composition_Layer_8of8_Sync.md` | 9160 | `c1a58b267d2d4a50f4197817379132706792e83e73d132547bab7a7b3e9fb323` |
| 24 | `00-SESSION-UPDATE_2026-07-28b_K2_Pipeline_Codification.md` | 6315 | `6135ad438103aeefc9fb1c083df654eacf1c719076ed93b578b6e77719d5121b` |
| 25 | `00-SESSION-UPDATE_2026-08-01_Retrieval_Layer_Closure.md` | 7070 | `516bbdac99be10df72fa7e95253e5506c0a4c9958d195f6356dc984318912f7f` |
| 26 | `00-SESSION-UPDATE_Baseline_Registry_And_Changelog.md` | 17156 | `37b02b3aa9f00832dbc5efc168560a7521e4113f5ebd45d47ba1fef604753eb8` |
| 27 | `00-VERTICAL-MAP-APPENDIX_K3xK4_Boundary_Resolution_Proposal.md` | 8905 | `b1dd0cacf1f71c082ae17a6aba11ddc4f9b0a31a5e51df0712d40b244a4da492` |
| 28 | `00-VERTICAL-MAP_Cross-Circle_Sequential_Flow.md` | 9399 | `e9ded72190968b956415aecbca839e67e697a55a86d1d85609ab8cbbb7ca1293` |
| 29 | `01-MASTER-Governance_Foundations_And_Decisions.md` | 166471 | `941fd941472df64fc65b6a35292ac26d5da6db0c93774f949595974ec24d77d4` |
| 30 | `02-MASTER-Tracking_And_Risks.md` | 132878 | `33cb411bcca77d72b351944dda658c17f4ce702a9d504bbdf1e1aedfc806035d` |
| 31 | `10-CORE-Rawahil_Core_Theory_And_Manifesto.md` | 33416 | `d5a387405bfd94deccfae28c0bfd6ef5973765ed4b9e1a062cb72dfca0394c5c` |
| 32 | `100-AUDIT-REGEN_Regeneration_Contract.md` | 7469 | `b5d4619ea102195ab977c1ba5df070c9f6b2edfc780cac244c9470d033779c8a` |
| 33 | `101-DEBT-LEN_Length_Debt_Review.md` | 10072 | `43bfbd33c90eef4e3a27859b210e2aa628a03d0b455a3c95217d3004c3bf99e2` |
| 34 | `102-LIMITS_Derived_Limits_Ratification.md` | 8461 | `d8f7cd9b8fb02233ad91a626f8f58c85af1fd26475e11696e9fe58a0590f6e58` |
| 35 | `103-LOCKGAP_Lock_Field_Mitigation.md` | 5819 | `1a62e4d5cd7d5e414a700af80c768a30fc7451b270a3b32c322421558f378142` |
| 36 | `104-GUARD-SP_H4_Implementation.md` | 6947 | `c7fe137cd13cf90a21ce33c401fae81bb3508f2928afa940f95327863bed051e` |
| 37 | `105-BUILD_DEC-231-232-233.md` | 7705 | `8babfaf6f19c9009411707b2ea47a03fd1fcf9aa3ac29dd7c9a75323c98e32c7` |
| 38 | `106-SUPERVISOR-HTML_DEC-234.md` | 6947 | `93bee023bbb34f71b73d31f2bcaa8bb89878a11fedf583a949019850be5edc98` |
| 39 | `107-MSG-UNIFY_DEC-235.md` | 6582 | `6cf5ec527b69d1a59c78c75b71ee440c50fcb648ddc35ffe6b56e6d36738c721` |
| 40 | `108-ISO-REVIVE_DEC-236.md` | 5750 | `ccc4488a1bc7f6300710c08507647fed6632e270618aadc76b778b83905f6b04` |
| 41 | `109-SURFACE-SWEEP_DEC-237.md` | 6882 | `68fce86ac4af36bc8e574df80e8cd062c326d602222974ff5b44c8ec938546de` |
| 42 | `110-DEFECTS-CLOSE_DEC-238.md` | 5785 | `40d51b5efd1dd0427b7e13e36ea43194e9b90e0dc44d767fa584e758094ebee2` |
| 43 | `111-EXPLICIT-RENDER_DEC-239.md` | 6950 | `33560974e124faf7aaa3a88bcd5dcc3531a307a787cc1235ecdb52986c9235d7` |
| 44 | `112-STRICT-K3_DEC-240.md` | 5299 | `85b88972b298653eed05fd28433f832be16c9daf2bf4817b52321e0377f658c3` |
| 45 | `113-LOCK-DRIFT_DEC-241.md` | 5405 | `a0aa615eadd34662fe01760b2dafb75b00022922f663f964a097499a39cc6056` |
| 46 | `114-BALANCE-MEASURE_DEC-242.md` | 6317 | `e7a4aaf25ebb8ceb3ea91e7927afb6042bdc803f5941f43801ede7cf32e46dd4` |
| 47 | `115-BALANCE-CLOSE_DEC-243.md` | 4745 | `e02d1d0a26a1d6c32eca5a50c6158186f14e04281b07f3bc01b273fe2ece5fdd` |
| 48 | `116-RETEST_Temporal_Reading_Charter.md` | 11277 | `9bef84eba9992bf54259484be2f5811663326aeca5c84bef53596d5a001090eb` |
| 49 | `117-AUDIT-SYMMETRY_DEC-245.md` | 4665 | `e8f778473036da791b7dfb749e63c36d3d328973f6efadedd2da4c65d493335b` |
| 50 | `118-VALIDITY_Reading_Validity_Charter.md` | 10361 | `eb9446e48e4383b41f943b84cb8f9669ca2d92ff9994cfd749054638f19d4e7a` |
| 51 | `119-CONTENT-REVIEW_K2_Item_Audit.md` | 14844 | `e9e975f3744ee154ebae6680c045dfb61541f09dfdfc4177dbc6f1c6458d2742` |
| 52 | `12-CORE-K1_Foundational_Constitution.md` | 23186 | `712a0afdeaa5dfd035e1feeec71eaf3f70916be86a06f167a721e86d4bc56fc5` |
| 53 | `120-VALID-STEPS_DEC-248.md` | 6260 | `55581d623e41606233eca3ff7035b889e3c5b4dfd61ee785fe11bc219de2eaa0` |
| 54 | `13-CORE-K3-AMENDMENT_Monotonic_Redefinition.md` | 7329 | `af0418632a47ecf1ea6dada9dd2fa6c727e55c134aec2faa06023cca521ef611` |
| 55 | `13-CORE-K3_Emotional_Regulation_Constitution.md` | 12458 | `591b71096184afad35416cf23461da3ba5ef21e92dc41b3cd866a444e75afff3` |
| 56 | `14-CORE-K4_Achievement_Circle_Constitution.md` | 12436 | `d3b46077f5a1c704872a61dde9c5403e0fadcd466758e0463780d80689570932` |
| 57 | `19-SEED-K4_Report_Test_Seeds.md` | 5055 | `ea913ac85bfd6ed8d69a6382566871ee4eecb2cba05f0000ca02032316578687` |
| 58 | `20-THINK-Architecture_Review.md` | 11878 | `60599ea3d1f06e2668325c9477284c886fc26ebdb3fd9a6c15b58a2594a050ef` |
| 59 | `21-THINK-CSLIM_Master_Matrix.md` | 64310 | `32189c519a69d5b980c9434dd24720f87f6455635fadfc4ca8bbb9a568ca6612` |
| 60 | `22-THINK-CSLIM.md` | 101744 | `c6560903259ab3c5a09d707e8474eff591d8384239533c5f6631d15a66afd75d` |
| 61 | `23-THINK-Positive_Matrix.md` | 90550 | `5fe2b2a3539ccd035d311f19dd511267f1df7748638638ad19c5bdbde35c4a2d` |
| 62 | `30-CORE-K2_Measurement_Operational_Map.md` | 33936 | `fc3bc95cb4000f5d89342ed1e8707dacfacf40a0180806d799afa44c41b255d7` |
| 63 | `40-MEASURE_Questionnaire_v5.md` | 34743 | `f0b4332f8999e36e158ffaa2b06c781d450bb18cd2794b0ad3edfc514cb32590` |
| 64 | `41-MEASURE-CONFLICT_K3_Bipolar_Instrument_Report.md` | 10806 | `27f168e72bf51166a896f365399f3ad7abe9838b75eb357530469dc90f53980e` |
| 65 | `41-Raw_Measure_v4_2.md` | 26903 | `51af2705a1b072b2f7eac791248a5e91a15d9292f2c61e0431fa756b61f9df6a` |
| 66 | `50-DEPTH-K2-A_Analytical_Dimension-1.md` | 32247 | `995ca253ed14ca609b7a6b96371a6b96fb4085d6acaa0ffcc89940c04375d2e0` |
| 67 | `50-DEPTH-K2-C_Conservative_Dimension.md` | 38628 | `ebb9da2f71596219a43da537fe9af292541852302bbdcb0ef40a3e0791e2b04e` |
| 68 | `50-DEPTH-K2-E_Empathic_Dimension.md` | 41122 | `ba7bd2755f926fa1f7c6a135ef168ea5eb07c9079695251e68bf053b06a2f629` |
| 69 | `50-DEPTH-K2-H_Conceptual_Dimension.md` | 45321 | `41ae4ef3223fd852f41b9e56126850b5a4a1cb27fbf2aec92ec24ede1a71d7c3` |
| 70 | `50-DEPTH-K2-O_Organized_Dimension.md` | 37604 | `09f220d6eb06b7e2bade4705a42d65353028336230263f20716e42515716b62f` |
| 71 | `50-DEPTH-K2-R_Realistic_Dimension.md` | 34921 | `eb744933379a5085e8bd7c798e441da2778e9aab5880033c8ba361e9987bfde0` |
| 72 | `50-DEPTH-K2-S_Social_Dimension.md` | 39760 | `70cb1d51f52835523aef56740abc4ece7ddadefcea3504ef9ab15fc0292f56e9` |
| 73 | `50-DEPTH-K2-St_Strategic_Dimension.md` | 41365 | `8a2f05428c68ba76fd2bc54bc0c458dcb47de50418825d828624cab7ff7e46af` |
| 74 | `50-DEPTH-K3-BI_Behavioral_Inhibition_Dimension.md` | 16948 | `d07354d76bbf4a3159e74c60266d996de4ec2c497b09c8800177c644b2b6b427` |
| 75 | `50-DEPTH-K3-CF_Emotional_Flexibility_Dimension.md` | 16009 | `75144f4819f9335ae6dad02cd34cc400ff7184f3e6afc239fb773217c864f836` |
| 76 | `50-DEPTH-K3-EP_Emotional_Perception_Dimension.md` | 25210 | `9b6a4dfb8572e6886812c6c6aae9bfaa4c647d57c440a15f9d96c60d1c8a18ca` |
| 77 | `50-DEPTH-K3-IR_Internal_Regulation_Dimension.md` | 19339 | `11be9d3cb94758bb72fb2caebcf04f1b7a21899a8e22e44df45cf52c6c6ee6ec` |
| 78 | `50-DEPTH-K3-ST_Stress_Tolerance_Dimension.md` | 18951 | `d2286b3dfff946d10a7ac403737dbae828ea62a1b3f1fd7733b4b90608bf0906` |
| 79 | `51-MATRIX-00_Charter_and_Registry.md` | 12818 | `380db66d68e7293ca0cc617e4d23f1d3a357a77f97032f1e24705adf830fedf0` |
| 80 | `51-MATRIX-01_Full_Dyadic.md` | 15025 | `022639d7a35d8626751bee3b52c6d1be26670dc2da8493dfd4232fbb75c6d259` |
| 81 | `51-MATRIX-02_Polar_Pairs.md` | 14952 | `d82078b2c3e2b1e5000bd86feaa8fcc69802aeb9e2b570670478c15ae8f32a78` |
| 82 | `51-MATRIX-03_Fallback_Map.md` | 12378 | `d3b3f0a61effadb90fb5f64e3f7d60a7fec9032f1db0dda0dd26e5da861d2d66` |
| 83 | `51-MATRIX-04_Shared_Blindspots.md` | 13241 | `4c04faf14371563f541ab1db4d6424da47515c1578e438a2fde4abf83cd43033` |
| 84 | `51-MATRIX-05_Lookalike_Discriminator.md` | 9953 | `2894d9d9353a2b246065c956f48f247c6918b50d01d4d44a555c2154b7500086` |
| 85 | `51-MATRIX-06_Retrieval_Index.md` | 17583 | `b0567472555210af5412ee0390c58f52bdb0b70e591073e1716714f37274b9a3` |
| 86 | `52-MATRIX-K3-00_Charter_and_Registry.md` | 16021 | `abdc978d04971d34cd7ae36f58affc951998d7d375269d61feeac305afcc8006` |
| 87 | `52-MATRIX-K3-01_Hub_Interaction_Map.md` | 9259 | `0eb423e677d654364d16376a1d264da43b7b98095b8f1dc3837af91a4f54518a` |
| 88 | `52-MATRIX-K3-03_Cascade_Failure_Patterns.md` | 8304 | `58a5a433fee43530ff11b9f7490cbd1473918ab19b579a5f620156e2b8a20f55` |
| 89 | `52-MATRIX-K3-04_Containment_and_Amplification_Map_v1-1.md` | 18587 | `f718c186ef214da3195d44ed7b7c960fb64c4a3674a6377d7d4a89dd822a05a7` |
| 90 | `52-MATRIX-K3-05_Lookalike_Discriminator.md` | 14295 | `dccf143101c9b6618cf2aa7437ad0c75c20834fb61facf3c21d7abefb1e2c4d6` |
| 91 | `52-MATRIX-K3-06_Retrieval_Index.md` | 16664 | `4eee4e1ddd7ba20b05d7394480c9d02fef260827ec44d07eb97cf445df1c527d` |
| 92 | `52-MATRIX-K3-07_False_Reading_Register.md` | 16146 | `229a7eadf41e6c86c56df5fad5be11608678e17731cfa8acd3f81c6008d4d8e6` |
| 93 | `52-MATRIX-K3-FREEZE_Normalization_Debt_And_Layer_Split.md` | 11454 | `2ed5c9ce1507506b3de4e714010a210ff0bb7d072fc2b1c0c8d876bdb0c0ea3f` |
| 94 | `55-USER-INT8-Batch1_ROCS_Intensity_Upgrade.md` | 12754 | `4444eab2c7649a61a7b66f38a1461b025c3c9a2c7694d9766832171bcb4a270c` |
| 95 | `55-USER-INT8-Batch2_EStH_Intensity_Upgrade.md` | 10672 | `d866e785bc87209100522001458d3c29813c9a9bcf4e5ef385371705d6e7ccd6` |
| 96 | `55-USER-K2-A-INT8_Analytical_Intensity_Upgrade-1.md` | 14829 | `7548f04a6def83e0b8f0ac85502acb0ab80e1068045165e9c5f3a171c2b305c1` |
| 97 | `55-USER-K2-A_Analytical_User_Layer.md` | 30012 | `25b03cdfc862011795e78d7e57675a2b52aef517760c46011a367c9bdac31026` |
| 98 | `55-USER-K2-C_Conservative_User_Layer.md` | 31930 | `77b76e0fbcc1575027e24309776c77f69c9b0ff551458175b9e3ae9558257eb1` |
| 99 | `55-USER-K2-E_Empathic_User_Layer.md` | 36861 | `02662992f2396b1cd323bf17c51f5558bb629042e80466c1e87fc14c06f3f5bc` |
| 100 | `55-USER-K2-H_Conceptual_User_Layer.md` | 34578 | `66777227fef0b18778e3b8523e3e09576dc38a89b208b4d1b9db5110bc706e5b` |
| 101 | `55-USER-K2-O_Organized_User_Layer.md` | 31291 | `6236e0b4957673e8a1702accc05b9a0f9a4976be692eb5bc8f265db4956a9ee4` |
| 102 | `55-USER-K2-R_Realistic_User_Layer.md` | 29395 | `5b877a6feea2acb4e0a93dd89a73f4a4c4e3943cf8ac04a00574458d030181f8` |
| 103 | `55-USER-K2-S_Social_User_Layer.md` | 33752 | `28155eb68baa9d699db52e496a2d0de246bbc91beba2b101e456f2f8564f00d7` |
| 104 | `55-USER-K2-St_Strategic_User_Layer.md` | 33165 | `785c770e176a1a50c54b61e07601a70d1f02e2e4b6b179b0b8c93ba85a9e6d82` |
| 105 | `55-USER-K3-BI_Behavioral_Inhibition_User_Layer.md` | 23506 | `ac15333decaeb918c2abeb89fe9261387f84da86863c8c1a18e44612860b09d6` |
| 106 | `55-USER-K3-CF_Emotional_Flexibility_User_Layer.md` | 21750 | `212dd76416653f29ba607408b5a336420b775d760cd3ea2c3b227a7351e60e2d` |
| 107 | `55-USER-K3-CMP_Composed_Reading_User_Layer.md` | 14675 | `af6783707336e791fa61153896edbbdf7263a4ee7fcd2582beef5788c19fc665` |
| 108 | `55-USER-K3-EP_Emotional_Perception_User_Layer.md` | 24258 | `aa3b581d3c29a8135fde35d33fcfca4438d73d852d192b2c081cd825aa34de00` |
| 109 | `55-USER-K3-IR_Internal_Regulation_User_Layer.md` | 23069 | `8e9606584da453cfb8b77d8ca153cab243d4b5a225a47a3f4baf5a856849f873` |
| 110 | `55-USER-K3-REFLECT_Self_Verification_Toolkit.md` | 11202 | `6505f9037f9d16009dabac24aee16b4d2912a5b70b9d1eed8bc73ebebba9b45f` |
| 111 | `55-USER-K3-ST_Stress_Tolerance_User_Layer.md` | 24200 | `a9cb1c53c20cfd53d3d2a99f792dbf9e4ff340a49597ef05ca2d8cfc05e3b7f8` |
| 112 | `56-GOLDEN-P001_Regression_Reference_Case.md` | 6235 | `8f3d308242cd919d1458e709c391feb9413746ae22237d588de112ab87be3111` |
| 113 | `56-GOLDEN-P002_Synthetic_OUT_Coverage_Case.md` | 6699 | `104a4566645dbe44f787d3b6e081f3fa795480aea8cec5dac60f2c621cdb09e6` |
| 114 | `56-K3-URS_Unified_Regulatory_Signature_Charter.md` | 22612 | `b46d1d2d420009ef896ba7a86b354f3cb6cbb3fd98c3ffc02e94d3ffe4a9a685` |
| 115 | `56-PILOT-01_Intake_and_Protocol.md` | 4602 | `40dd7ddd3eeeb3f1d1ce30545b0788036847d5a52fbd19d46041bef8a14f95d8` |
| 116 | `56-PILOT-P001-LEADER_Individual_Report.md` | 11763 | `fdb94695a312fb5c7d9c412ea5c0df6b4fe57a85321509e0940d48deedc3d7fa` |
| 117 | `56-PILOT-P001_Individual_Report.md` | 10263 | `663a5ad96a45f559f4e199c58e97131c110c55013aaff5034917d2ef78252d84` |
| 118 | `56-REPORT-ENGINE-APPENDIX-B_Leader_Mode_Conversion_Rule.md` | 8540 | `3b4d2ce94a725d1697556ce6cbd57c24cd496b5b9751ad3cef5c7abfe4aac7e0` |
| 119 | `56-REPORT-ENGINE_Operational_Specification.md` | 36918 | `68843e48f0355f9813597974236bf664356bfca4284e836408be6a9918ee28b4` |
| 120 | `56-TEAM-00_Team_Composition_Protocol_Charter.md` | 8391 | `c587a3485854d9834ec302e64c640d68c4baede7fef92cc76b35c1aa62905d03` |
| 121 | `56-TEAM-P001_Synthetic_Dry_Run.md` | 8584 | `f6eb8e09be848f1c7d9e25a9a5bbff7c8e41489790a2b79d63f00c6715178efd` |
| 122 | `56-TEAM-P002_Synthetic_Scaling_Test.md` | 4446 | `a4d1db3b4630ca6ffa7a349920dd5fcc0e1fa1718ead33597053229845e0169c` |
| 123 | `56-TEST-01_DryRun_Alpha.md` | 10049 | `19e61a28ed299bb961e21aa0fd6575fcb0376207de3f8406c28050f857f5ee35` |
| 124 | `56-TEST-02_DryRun_Beta-1.md` | 9417 | `3bfb494d210f29ceb0f00a41ee9aa64f2d751a789d0ba590d43aea1deb8f06e1` |
| 125 | `57-K3-ENGINE_Blueprint.md` | 17441 | `826d68591a8577a6a539fcaf98ccd41314216e947d63b70134ba932df96991eb` |
| 126 | `57-K3-ENGINE_Operational_Specification.md` | 21721 | `97ad7753520840ce0f3bd9278d8414ea56b080b0c2a5b8cab5af60ee22004226` |
| 127 | `57-K3-ENGINE_Reconciliation_41v42_40v5.md` | 7443 | `68e819fb55a8313b97998ec335f4abd574882c485d1e1b0bdf7bfd4e0e7ca781` |
| 128 | `58-K3-VISION_Dynamic_Interaction_Charter.md` | 9691 | `60bae7067e1000a9796c25964570b4520b5ee851dec774d7f0b6ad069fc3520d` |
| 129 | `59-K3-IMPACT_Comprehensive_Assessment.md` | 9027 | `8a8610ace87dc312841046e0eecc70d6f5355521db97b6ef7d22fe78fe9f8b73` |
| 130 | `60-K3-TOPOLOGY_IR_Hub_Blueprint.md` | 19890 | `da6c45479168498f0a9ac9d80a4690f70992daafa41b142db00316f9333d4881` |
| 131 | `61-K3-COUPLING_Methodology_Blueprint.md` | 11389 | `60870c82c46b5c93329e7e4cd8b15b6c0b733cff2a1b6d43e1a71033db757610` |
| 132 | `62-K3-COUPLING-REGISTER-B_Lateral_and_Load.md` | 27326 | `1f9d72b16900464056547096919805464c8d8205cbdbb483f6901f05c572b2e9` |
| 133 | `62-K3-COUPLING-REGISTER-C_Perception_Feed.md` | 15971 | `8dcc23f8c68902f91501e74da066983483dbfb4fd5328885773883194c589744` |
| 134 | `62-K3-COUPLING-REGISTER_PhaseA_Hub_Family.md` | 25679 | `0b2cb83d7a468a0b8c2534de01091bd70446dd35397c1519115f939fcc848cf8` |
| 135 | `63-K3-URS-REFRAME_Directive_For_Step4.md` | 11244 | `6109e159166baf0fa4db5ca035d6202430e0c6116343e5229291f6ddcf775713` |
| 136 | `64-K3-COMPOSITION_Layer_Methodology.md` | 12119 | `110cf17a56c178810bda55372007e2505c905a7bed6109e44cc272ca8bd8e2e8` |
| 137 | `65-K3-PATTERN_Recognition_Sublayer.md` | 12531 | `95a9a2521cc3d6ad14f3d5c49f0bbb64a9412922d0b5cd8e975d8e7d1c608c5b` |
| 138 | `66-K3-STEP4_Resolution_Dossier.md` | 29631 | `11913904c524e7b4a75c0407a4fe429674b3e67cff24c9a14a48dd823c5e642d` |
| 139 | `67-K3-ROOT_Conditional_Attribution_Protocol.md` | 9896 | `587ef792c1521465528173977e94efc25a542c63b2b164455554458b16070cf2` |
| 140 | `68-K3-ROOT-QBANK_Verification_Question_Bank.md` | 15357 | `14d184fa4f0d0c0864fe2a45ed4a8e53c372c762298805b500ce0928269f33e8` |
| 141 | `69-K3-TRACK-B_Instrument_Expansion_Charter.md` | 10550 | `df3b642dee1ece6c126f2f232d8aa67fc9944e3ed4a4c0e27f8922296056322b` |
| 142 | `70-K3-STEP5_Engine_Binding_Scope.md` | 12712 | `28b3fecaeecf63d820468567ce98f44297bd96d8496eb7c7ea00e19db4f9406d` |
| 143 | `71-K3-CMP-PHRASEBANK_Composed_Reading_Phrase_Bank.md` | 12410 | `6136119d7c097b41612888ed97443eaa507a0b523fbd1e6d28638f0d16a8727d` |
| 144 | `72-K3-ENG01_Retrieval_Index_Assessment.md` | 6798 | `02968823fbda8e3fb0287de5d9f48523f1a62ff0d6d84cc0f619b57ac98224bb` |
| 145 | `73-K3-DRYRUN-01_Synthetic_Full_Pipeline_Test.md` | 14939 | `84d19b66f46f1dfc060bdcfb4e1911171c7a3eb274fa37bc046848b090b10ad3` |
| 146 | `74-K3-DRYRUN-02_Five_Edge_Cases.md` | 9901 | `6cd9100c3903e4034f7a52fe42234a103b67a04a4ec7e9209c01ab9dfb4dfd80` |
| 147 | `75-GOLDEN-K3_Regression_Suite.md` | 7800 | `d73b5d25eb9071412b6f81773cdf193ee1150c84a67b95a2fe3837ef2dbe20b2` |
| 148 | `76-K3-SETTLEMENT_Debt_and_Gap_Register.md` | 11881 | `b4511ed5a133105c8e6a54c8784a0bae4e74e031f88b75f7eded0973091da120` |
| 149 | `77-METHOD-TRANSFER_Cross-Circle_Adaptation_Principle.md` | 10051 | `09299e9be6f6b2b12cb9cc1fd4aef46059d414bde886d11b07ee8a4812d6938b` |
| 150 | `78-K3-CONTENTPACK_Extraction_And_Gap_Report.md` | 6904 | `6006338c506e1721e6b09d9586f5342781688d0c2e89750539fb7d16499d61f1` |
| 151 | `79-K3-USERMAP_Section0B_Rewrite_Proposal.md` | 10192 | `5efc3943c2914cad1c58f752c0a19db8a515fa316d014f3f17c649b6fac9cf55` |
| 152 | `80-K3-TEXTS_Three_Missing_Content_Keys.md` | 9662 | `f545442774ba752e29c862d61d0d0a61387ade87e75fc94781aceae6ac38b0a2` |
| 153 | `81-K3-REPORT-SYN01_First_Full_Report.md` | 21699 | `cba8fbc4b94d91f112c3bbc65df716b66ec4bb18558ed049af3d4c9423f22444` |
| 154 | `82-K3-RPT-HEADINGS_Nine_Section_Titles_Proposal.md` | 6556 | `b5fd6b6b5b8b599eb5dda21b940da6d9b9cdf96eb03c68be7f897ac2da834b6a` |
| 155 | `83-K2-RPT-COMPARE_Structure_Reconciliation.md` | 13787 | `7118674630455caea526f8dff4a0895b1b0c3f71b66ed9d16c33ac293d2cc53c` |
| 156 | `84-K2-DEFECT_DEF-K2-01.md` | 12725 | `c6ea5f82e85c2bb95197c07a2ab42a82984109c572972ebca9b8e87535f814be` |
| 157 | `85-K3-GUARD_Integrity_Guard_And_DEF-K3-01.md` | 8381 | `2c4e5e32b9c1199c02c60c71249fc0c630eebf0986c137edd507a9918eb2045d` |
| 158 | `86-K3-FIX_DEC-195-196_And_TC-K3-02.md` | 8294 | `ea14c12cc807bb1b23249c2cac0499d9a33711f7ef5eb9b99e08a82af20b17e1` |
| 159 | `87-PARITY_Cross_Implementation_Specification.md` | 12354 | `60f0f55d206d5c256ed6a89839da4ab857d932d50c30fe9100d97ec858557f70` |
| 160 | `88-PORT-01_JS_Engine_Port_And_First_Parity_Run.md` | 10602 | `63c357854fe8018e1150c6c2806fab945a4a931f6cc435dc4ae8c3ad18dc1df0` |
| 161 | `89-PACKS-02_Content_Pack_Embedding.md` | 5998 | `84fd94ee2b536b5c5d5e16912e0a875151a05fcefa2a7b734bc7e700f6893de2` |
| 162 | `90-REPORTS-03_Report_Layer_Port.md` | 7212 | `04afb3aa6d245a83dfd5032dd9b5636f86bb12abdeec0cd646ed02b9ea00cade` |
| 163 | `91-COMPOSE-04a_K3_Nine_Section_Completion.md` | 6015 | `3fcd103bf1214c21980812c91e2889314a766d0f0d1557f3d022f5e56dad65e1` |
| 164 | `92-INTEGRATE-04b_Tool_Integration.md` | 7056 | `9b678e5657305f5a6fdcba69123e715facd201ea7b0092d1809539a0e8caf777` |
| 165 | `93-K2-LINES_Closed_List_Resolution.md` | 7648 | `9192f5e8d46312cf76223987e5a575fbd649458d3c40ca3530f7f51e2ed01a2d` |
| 166 | `94-TC-K2-01_Center_Catalog_Resolution.md` | 7631 | `8bcc6b2e617fe1059b8a8cdf91baae76a4702d718f97df281d5e193fefefd8f5` |
| 167 | `95-K2-NINE_Functional_Distribution.md` | 6329 | `bd6675d643f5bc9e1d3543307e0c0852b0b6d1a0f0dc74e793f0c29c6567bd6e` |
| 168 | `96-GAP-RPT-K2-02_R9_Purification_Gate.md` | 7937 | `fb8e248d2b72d4d828a9c17efc763e80d72206060dc6408190898c1d7e5090f0` |
| 169 | `97-R9-NAMES_Gate_And_Skill_Names.md` | 6951 | `dd4aee3e18aaf2b1c09365f5551ff186cb1935c8adf345da4f73d49bad8866d8` |
| 170 | `98-R1-INTENSITY_Blocks_And_Lock_Exclusion.md` | 6692 | `bd26ced72431570c33b7ba50612505958cf5c8a3691776746aea8f981371831e` |
| 171 | `99-R11-TIEBREAK_Dual_Display_And_Determinism.md` | 6371 | `529c0ca0ddfca96a31a1bdcef7fe03b8f21be3e6900d68d82ef74fc1ce8d6828` |
| 172 | `COMPOSE-A_Analytical_Composition.md` | 18991 | `f6b4a8bcbbc1e497b0b80bb5f4e9c2a7ff1e9a385c4c4c9b181f35a3f2d46676` |
| 173 | `COMPOSE-C_Conservative_Composition.md` | 19007 | `03738bd90cb0bb27093a1bce2a2f8b3fb2355b8354907bc4169ed161f78c0ad5` |
| 174 | `COMPOSE-E_Empathic_Composition.md` | 11658 | `60fdfecd0352353defe86d5087ccd6a60f3ec9b4f9bd0321cc6a7273afb0bd53` |
| 175 | `COMPOSE-H_Conceptual_Composition.md` | 11979 | `a21c96058ccdf18b0eb5047d69380d9b8f636b98e48e0811784a7ff99348191e` |
| 176 | `COMPOSE-O_Organized_Composition.md` | 19287 | `409c4964e16343d078841eb6f1aec389cc31cda5309aa300414c563ce502ae9b` |
| 177 | `COMPOSE-R_Realistic_Composition.md` | 17869 | `b2363f68eb66e54a88d95191d82f9d04e85ccc8cb18321be0428a1982e41973a` |
| 178 | `COMPOSE-S_Social_Composition.md` | 18392 | `c1c267f8dfeace0b6effd5826e42878877c05de1cc5cc50ecb700bbbd14748ed` |
| 179 | `COMPOSE-St_Strategic_Composition.md` | 18446 | `a85178d0df2fe3bc21cb8ffffa313b673f4aabb02d77e4b0603c69ce536a40e0` |
| 180 | `GAP-Q-02_Resolution_Dossier.md` | 14779 | `6c6ca4a182e4536727a0d7ad05a48334e29d0689baa597521624a60e4f73f02e` |
| 181 | `REPORT_P-001_Full.md` | 44436 | `698955dc406e0a8335ec2f6af566cde0523af42296caebcbad970d4e96124b8f` |
| 182 | `REPORT_P-001_Full_Brief.md` | 22354 | `3deae8a5e76ad5035214b811141eb85ddb691f6b2abcba1efd4c59e5000d18cb` |
| 183 | `REPORT_P-005_Full.md` | 39687 | `a4ef61b09538155845393ca588508ec86ff400d0a1132a46e6adeef97685c761` |
| 184 | `REPORT_P-005_Full_Brief.md` | 20303 | `eb080633325c82c8627534d3e01dcbc669e155a84da958abaa005b42358b8bc4` |
| 185 | `REPORT_P-006_Full.md` | 50919 | `ad77cc4df0c7cd1bd19cb02cb3eb2abe86003248fd65d4bbfc025271fdbca44b` |
| 186 | `REPORT_P-006_Full_Brief.md` | 23849 | `1e6134641fcba733d6465d066ca61576510a28f8e69676aa49e52b54ff141e92` |
| 187 | `REPORT_P-007_Full.md` | 40102 | `8fe8b05d80c1a0628c96fafa68359544e36fcdda5c12e1497175f4ffdd414b11` |
| 188 | `REPORT_P-007_Full_Brief.md` | 21397 | `37080595354d6a10e92c013292c094d6cb74785363aa6ae20463854ea5087d46` |
| 189 | `VERIFY-COMPOSE-01_Live_Pass_Eight_Lexicons.md` | 8225 | `2afe469f243a12942c9cb8a818ee566328fa2b4f122044107bad990fb8a69b01` |
| 190 | `VERIFY-COMPOSE-02_Live_Real_Run_Center-A.md` | 7645 | `8e00f66e939e5a889c7f2a092297f5f49af39fd3486de56416892d6516805de5` |
| 191 | `VERIFY-COMPOSE-03_Live_Real_Run_Center-C.md` | 7032 | `7aa817458f009e1557743e0591dd055963c0eca45c237c36c074d5797301eac5` |
| 192 | `bridge.js` | 3720 | `f987ed5a744252793f6ef8ad5aef6a95021fbd2be0728a34cfca3d1f9547c592` |
| 193 | `build_packs.py` | 8472 | `6ff75ecddae61324e790fbcdc3234c5be2e81011f883376bfcb32ca77afa022a` |
| 194 | `build_supervisor_html.py` | 15696 | `368a7380b4377bee4e9f97cb8d76035d4733d17cd86138e5dc9961de7c631166` |
| 195 | `circle_map_by_skill.json` | 6519 | `3181004cb419070c11178cf52271aaf6443810dcb43e9da6b682585ce18d5f46` |
| 196 | `circle_map_v2.json` | 3177 | `e560f3363bf9e3d940143eed155b804539c80cb85f8ef1867575aea3a510d0e8` |
| 197 | `dualreport.js` | 15064 | `324d24759b41619291100ca7a85818bae5128c29a662ff6c01b0e7b7d348322d` |
| 198 | `engines.js` | 25984 | `f3e7484e910f6b06843d83503a9a11b92e9ff844047ae468b5e929ce34dde0a3` |
| 199 | `golden_k2.json` | 23964 | `1a89cdcf5ef89f35e5e4dae973f112a6f3877f79f7026577324b767fb4e6d1b1` |
| 200 | `golden_k3.json` | 2672 | `d6549e3e2ba71c0bf04c2b62c7e35f1163f2bb7364de36395d3600c51464403c` |
| 201 | `guard_interp.py` | 5064 | `256ef49c9b5a4a8ace614aedf6f4fcf62b44cde5347d46bc316754c010c9c87b` |
| 202 | `interp_registry.json` | 5037 | `2d003676cc9487a222118dccbc84772a255bc0b69ff27e13786e6b9b53598d59` |
| 203 | `k2_content.py` | 6515 | `9b0087dc70cabf7257e0cab58ddafcf3516b746493a114ee61b2029be174ad14` |
| 204 | `k2_contentpack.json` | 90701 | `504cc24aab47ed01167ea2eab41ad785156cdf0dc9bbeb2a71086ad62eacc1e8` |
| 205 | `k2_engine.py` | 14660 | `da37dfa98720f16c122507f26ff48531b7b56c65fc84a1de8cfb86be7fd4fe07` |
| 206 | `k2_framing.py` | 2304 | `d90c362d6b04eaec83cc07de04062b257d1ec616fa84c1a9d4db45d92888a332` |
| 207 | `k2_intensity.json` | 30084 | `09d3fa9e824b32302dfa1874d066268f26f565bb0e8b64d5594e8678f38b64af` |
| 208 | `k2_lock_registry.json` | 1033 | `56999e9076824df2fd445a8e09975e57456481db91c03c7f5a7b35b5ee190d30` |
| 209 | `k2_lookalike.json` | 3702 | `21b6b741c5f95553614fcda5dcd5b635dfd51e49417df440841a3bb059ec1452` |
| 210 | `k2_pur.json` | 20104 | `ec2f2dc4bb97496bbb9a67653dcb02affa6a3a322055cf2a97dd50e4d55bc45a` |
| 211 | `k2_report.py` | 25309 | `05147b83423c26fbd7a166e1108effc9b19158bce8c91964152603fcfd79c7f3` |
| 212 | `k2_userlayer_pack.json` | 108316 | `ab8406cf00eb9ddc4a9c7fb3fd966f370f5446c3882a600824aafef42c7068f7` |
| 213 | `k3_banner.json` | 189 | `90eab01c21192daa9805e9c61ee886a943df622dae5c0450a70add855404b650` |
| 214 | `k3_content.py` | 11926 | `409034693b006a0024388bc42d25b1ba382e3bd5c4dae70bdd5684c9e3b9f68d` |
| 215 | `k3_contentpack_FIXED_DEC-195.py` | 8573 | `725df5cb93054be4d89767022d7f9d7e2aa126a82cb15a8643ef20b77b870ea4` |
| 216 | `k3_engine.py` | 18971 | `af409b22d425540bd9278999608119632385d1a8e0df64396c4ab68154c69ad3` |
| 217 | `k3_functional_terms.json` | 342 | `8dd840354534cee347177e4108eb327589231725db61c6b60de186a23583675b` |
| 218 | `k3_g5.json` | 788 | `6a6098b1900d315230dc358804586a824f16ad3e843525046d88a1834ae93427` |
| 219 | `k3_guard.py` | 7325 | `e92631f9953ed6771b2edff176d4dbc61517420bd821b1ccac7316fbad736495` |
| 220 | `k3_report.py` | 6537 | `593b0c50947cafc9710d297e17f9b334ae7145b5046bd3d42a07c39db4e0bcee` |
| 221 | `k3_textlayer.json` | 12302 | `c5a9ca927353ff8d54a0a38f8a6b57cf9db9bf8efdd08f51317bf787a23ebab2` |
| 222 | `packs_manifest.json` | 1774 | `fbac784699b2732a1875c2a55c6411a148ecaafc77efdb895ee135d2649afde4` |
| 223 | `parity_cases.json` | 8092 | `6a1dcd4c2598914888d0bd680e42cabf8d1afccc0ffcc01fe6507fb4603e997a` |
| 224 | `parity_frozen.json` | 2 | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` |
| 225 | `parity_isolation.py` | 6152 | `9ffa957a47b43e03c1f059423e9264504928e3505e8d893e9525f1941cb74db1` |
| 226 | `parity_js.js` | 5026 | `d2e7f57346ff873aaa6416a6c5c606f811ddea00525afbed0c94f43ec598bbd5` |
| 227 | `parity_messages.py` | 6688 | `290c8d1cf944b65da6355334aa390539bea29b74f434887fafd1eab608be8dc2` |
| 228 | `parity_py.py` | 8996 | `710fa2e59013e3509e15961a4d9f5d882c76da157397afe3deb682cd6c61520c` |
| 229 | `parity_reports.py` | 4118 | `a727acda9a188f35194752d90ca1394b375a84a2166a62747dbeed6bb0a46208` |
| 230 | `parity_reports_js.js` | 450 | `13399e38db9e6b0cc3976d78dba6565c44de1cc1d78c567f93083313dd456308` |
| 231 | `parity_supervisor.py` | 6823 | `2a630e3d2dafe3234f28b3a081ea4e1a965ba4e77e50295a2650c27f6b298223` |
| 232 | `parity_surface.py` | 11513 | `a781c46b10223b6997472b95ccb65d20aa76a3e2339fffb4545f828d015964c0` |
| 233 | `reports.js` | 29977 | `2b432010c04afb94c47df0d36a8d95c2ee28bec3448353fa3c79dc52e73f9144` |
| 234 | `skill_sections.json` | 9920 | `83089c7486e222353921ffdb8863761f9659a2d18192939ce525e08daa98bb41` |
| 235 | `sp_gate.js` | 3556 | `56ecc803f43442b7b67eb5635d39650cfd77116532263145209a70a38d76d852` |
| 236 | `sp_gate.py` | 5183 | `5eb12a0738707361b80a9321f844fe7b2ad85c97b5e4ccb4a54934acfb00f724` |
| 237 | `styles.css` | 2672 | `ebadfb0374e66e516163afd873f26b077085b132e14ee7ccbdf19df50702bc72` |
| 238 | `supervisor.py` | 11700 | `e80c75e9576740d44e9079bef2e5bc67df3cd0b76a37624c6da877e7f5b7e280` |
| 239 | `supervisor_core.js` | 7831 | `7fb769158609cd661f706097f8fa0c3fc241fc02b33cdc63ab6bb7b301573fbf` |
| 240 | `test_golden_k2.py` | 5120 | `a138ce9b62100d567616820e63bcae1b3cc250387e5f4c4a9ebc8a299a2b6622` |
| 241 | `test_golden_k3.py` | 4069 | `043581b7b435df02ba2c5b20a3b504e31de0a91c09a7ccbec168a8ce1e580c7f` |
| 242 | `test_guard_lock.py` | 5668 | `44212beda20bfcded9718a1cd1bdd264ce30e7edf446870b8f3fa0cac74c491c` |
| 243 | `test_guard_sp.py` | 10470 | `211868ea7b11211e0d7ee7da0c000eb7d739cf05f09a983d386c40f1db5a5295` |
| 244 | `test_packs.py` | 4738 | `05bde6b35b0b1730a206d10ed16472a8ff365d402e4b1e1192021e247ab9219c` |
| 245 | `test_report_k2.py` | 4562 | `9334ad74b54054c24c883f6dccf94881e776e99e4c40f7b2a40dfeeba1134c53` |
| 246 | `test_report_k3.py` | 7030 | `b0536a8bc69b43ebd75e58ac30180171366a7281b59571108a1436f3517883e1` |
| 247 | `three_texts.json` | 3864 | `22fd87e2ee6311ad439fc79a0eb12c0535f17c85015a210117d25f7f7b33efe4` |
| 248 | `verify_regen.py` | 4682 | `d903f52a25ce87db1bc17597ddad846dff89b089b203b684dbb52b197376c6fb` |

**[نهاية `00-MANIFEST_2026-08-09` — 247 ملفاً · `DEC-248` · التالي `DEC-249`]**
