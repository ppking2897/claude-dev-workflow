---
name: feature-doc
description: 在 .claude/docs/ 產出混合格式 feature 文檔骨架（7 section + inline ADDED markers），並從對話 context 填入已討論的 Requirement / 技術設計 / 實作計畫 / 待辦。設計討論結束後使用，非 propose-first。不寫 Verified footer（那是 verify-feature 在 merge + 解衝突後核對過才加的）。
when_to_use: "設計討論收斂、要把功能規格落成 doc 時。觸發詞：建文檔、寫 feature doc、新增功能文檔、整理進規格、落 doc、寫進文檔、規格文檔、產生 doc、文檔骨架"
---

# feature-doc

把跟使用者剛討論完的功能設計，**落地成混合格式 doc**：7 section + inline ADDED markers（**不**寫 footer，footer 由 verify-feature 在 merge + 解衝突後核對過才加）。

## Step 0 — 讀專案配置（每次跑 skill 必先做）

跑此 skill 前，先讀**當前專案根目錄**的 `CLAUDE.md`，從 `## Skill 配置` section 抽：

| 變數 | Fallback |
|---|---|
| `{DOC_DIR}`（doc 落地位置） | `.claude/docs/` |

下面流程中 `.claude/docs/{Feature}.md` 用 `{DOC_DIR}/{Feature}.md` 替換。

> 詳細的 Skill 配置格式參考 verify-feature/SKILL.md 的 Step 0 範例。

## 何時使用

- 跟使用者討論完一個新功能的設計（不論是不是 Plan Mode）
- 使用者說「寫 doc」「建文檔」「落進規格」「整理進文件」
- 已達成共識要寫進 `.claude/docs/{Feature}.md`

## 何時**不**使用

- ❌ 設計還沒收斂（先繼續討論，別急著落 doc）
- ❌ 只是改 code，不是新功能（這種寫 commit message 就夠）
- ❌ 改舊 doc 的部分內容（直接 Edit doc，不用走這個 skill）

## 輸入

- Feature 名稱（必要）：用於檔名 `.claude/docs/{Feature}.md`
- 從對話 context 自動抽取：
  - 「目的」（1-2 句）
  - Requirement / Scenario（行為承諾）
  - 技術設計（API、平台 specifics、加密參數等）
  - 實作計畫（slice 切分 + 每個 slice 對應的 Scenario）
  - 待辦（外部對齊事項）

## 混合格式定義

每份 doc 一定有以下 7 個 section（**無 footer**，footer 由 verify-feature 加）：

```markdown
# {功能名稱}

> **目的**：{1-2 句說明這個 feature 做什麼、解什麼問題}

---

## 行為規格

> 用 Requirement / Scenario 寫法。Keyword 用英文（RFC 2119 / Gherkin 慣例），內容用中文。
> 情境寫使用者看得到的結果（「送出按鈕不可按」「進入首頁」），程式名稱（State 欄位、Event、Route）放技術設計。

### Requirement: {一句中文描述系統承諾} <!-- ADDED YYYY-MM-DD -->

{Requirement 的 1-2 段中文描述，用 SHALL / MUST / MAY 表達強制度}

#### Scenario: {具體情境標題}
- GIVEN {前置狀態}（可選）
- WHEN {觸發條件}
- THEN {結果}
- AND {補充結果}

#### Scenario: {另一個情境}
- ...

### Requirement: {下一條} <!-- ADDED YYYY-MM-DD -->
...

---

## 技術設計

### {子段：API / 加密 / 平台 / DI / 安全紀律 / Fake-First 等視內容需要}

{技術細節：JSON 範例、程式碼片段、設定參數、interface 定義}

---

## 涵蓋範圍

> 給 /verify-feature 反查用。列本 doc 涵蓋的識別字 / 路徑 / route / API key（Step 5 掃出的 Feature-specific 結果；共用基礎設施不列）。

- 識別字：{ViewModel / Repository interface / Fake / UseCase / Contract 型別 / enum / sealed 成員}
- 路徑：{feature/{name}/** 或 layer-first 對應路徑}
- route / API key：{Route 名 / endpoint}

---

## 實作計畫 + 驗證紀錄

> 把 Requirement 拆成可獨立交付的 slice，每 slice 對應哪些 Scenario 要驗證。
> 欄位：**性質** / **狀態** / **驗證日** / **驗證方式**。
> 狀態圖示：✅ 全 PASS / 🟡 部分 / ⏸️ blocked / ❌ FAIL。

### Scenario 兩分法（落地時對每條 Scenario 分類）

| 性質 | 怎麼驗 | 範例 |
|------|--------|------|
| **邏輯** | unit test（`commonTest/`）— ViewModel state 推導、Repository 分支、validation、**async flow + side effect**（寫 token / DataStore、送 Event、導航決策邏輯；非同步路徑照 `/unit-test`「非同步與時間」一節控制排程與時間來測） | 「新密碼不符強度 → 送出按鈕不可按」；「登入成功 → 進入首頁」 |
| **UI** | emulator 手測 / Compose UI test — **純視覺**：畫面 render、視覺樣式、佈局、平台元件互動 | 「紅框 + 錯誤訊息顯示」「dialog 跳出」「全 read-only」 |

- **邏輯 scenario**：落地時 `驗證方式` 標「待補 unit test」，實作時補 test，改成 `unit test: {TestClass}#{method}` → 之後 verify 直接跑、永遠新鮮、自我維護
- **UI scenario**：`驗證方式` 寫 `emulator 手測 {date}` → 是 point-in-time，code 改了會過期，verify 會盯 staleness
- 判斷準則：**有行為 / 副作用（state、flow、寫入、event、導航決策）→ 邏輯**（非同步路徑控制排程與時間就測得到，見 `/unit-test`「非同步與時間」）；**真的只剩視覺 / 佈局才標 UI**，別把可測的流程邏輯推去手測
- **邏輯情境的結果會顯示在畫面上或會換頁時**（按鈕變色、紅字出現、進入首頁）：unit test 只證明狀態推導，畫面有沒有跟著變要實機證明 → `驗證方式` 同時列 `unit test: {TestClass}#{method}` 與實機編號（例 `device-check.md #6`）
- **高風險 Slice 一定要有實機證據**：`高風險: 是` 的 Slice，Slice 的「要上手機的情境」列的每條 Scenario（規劃時就逐條找出碰到高風險項的：換頁或返回、切背景再回前景、登入狀態或存起來的資料、付款、跟後端之間的資料格式），`驗證方式` 都要列實機編號（例 `device-check.md #6`），不論性質是邏輯還是 UI。只有 unit test、沒有實機編號時，該 Scenario 狀態最多 🟡，Slice 整體不能標 ✅。理由：讀 code 和 unit test 都看不出各環節接起來之後的行為（例：首頁按返回 App 整個重開，審查沒抓到，只有實機抓到）

### Slice {N} — {slice 名稱}
- **對應 Requirement**: {要在哪一條 Requirement 之下實作}
- **commit**: `{hash}` 或「未開始」
- **高風險**: 是（{改到哪幾項，定義見 `~/.claude/skills/my-flow/conventions.md`「高風險組」}）／否
- **要上手機的情境**（高風險是才寫，規劃時跟使用者逐條確認過）: {Scenario 標題}（{碰到的高風險項}）、…；不用上手機的不列
- **整體狀態**: ✅ / 🟡 / ⏸️ / ❌

| Scenario | 性質 | 狀態 | 驗證日 | 驗證方式 |
|----------|------|------|--------|---------|
| {Scenario 標題} | 邏輯 / UI | ✅ / 未測 / ⏸️ blocked | YYYY-MM-DD 或 — | `unit test: ClassNameTest#method` / `emulator 手測` / ⏸️ 原因 |

> **實作當下就驗證**：每實作完一個 slice，當下就跑它的 unit test + emulator 手測它的 UI scenario + 填表。**不要拖到 merge** —— verify-feature 不負責「驗證你正在做的 feature」，它是 branch 併入 + 解衝突後的核對步驟。
> 第一次落地時 commit 通常還沒做，狀態多半是「未測」或「⏸️ blocked」。

---

## 待辦 / 跟外部對齊

| 項目 | 屬於誰 | 阻擋上線？ | 移除條件 |
|------|-------|----------|---------|
| {待辦項} | {後端 / PM / App / QA} | 是/否 | {可直接驗證的條件，例：登入 API 文件寫明成功回應的欄位} |

---

## 變更紀錄

> 用 `ADDED` / `MODIFIED` / `REMOVED` 前綴標 spec 變更；其餘決策變動寫散文。

- **YYYY-MM-DD** ADDED: Requirement「{第一條}」
- **YYYY-MM-DD** ADDED: Requirement「{第二條}」
- **YYYY-MM-DD** MODIFIED: Requirement「{某條}」（PREVIOUSLY: X / CHANGE: Y）
- **YYYY-MM-DD** {散文式決策變動}
```

（**無 footer** — verify-feature 在 merge + 解衝突後核對過，才會在最底加 `**Verified**: YYYY-MM-DD @ <sha>`）

## 流程

### Step 1 — 確認 feature 名稱（一份 doc 對一個大功能）

- 從 user 訊息抽 feature 名稱
- 若使用者沒指定 → 從對話內容推（範例：「生物辨識登入」→ `BiometricLogin`）
- 命名規則：PascalCase，跟既有 `{DOC_DIR}` 內檔案命名風格一致（範例：`BiometricLogin.md`、`Checkout-API.md`）
- 命名盡量跟 `feature/{name}/` folder 對齊（如 `feature/login/` → `Login.md`、`feature/member/` 內的「重設密碼」子畫面 → `ResetPassword.md`）

#### 一份 doc 對一個「大功能」（拆分判斷）

**規則**：當 user 給的 user story 涵蓋多個獨立大功能 → **SHALL 拆成多份 doc**，每份對一個大功能。**不要**把多個大功能塞進同一份 doc。

判斷標準：
- 每個「大功能」≈ 一個 `feature/{name}/` folder，**或**一個 feature folder 內獨立可運作的子畫面 / 子流程（per-screen 切法）
- 行為規格能不能各自獨立成篇？能 → 拆。不能 → 合
- 實作 slice 是否在不同 feature folder 內？是 → 拆
- 拆到「per-screen」是 OK 的（一個 `feature/member/` 拆成 `ResetPassword.md` + `PersonalInformation.md`）—— 比 umbrella doc 好讀，每份聚焦一個畫面。但要處理「共用基礎設施」的歸屬，見下方

範例：

| User 給的 user story | ❌ 反例（合在一起） | ✅ 正解（拆開） |
|---|---|---|
| 「帳號管理與登入驗證」（涵蓋登入、忘記密碼、個人資料）| `AccountAndLogin.md` 一份大檔 | `Login.md` / `ResetPassword.md` / `PersonalInformation.md` 三份 |
| 「訂單管理」（涵蓋下單 / 付款 / 退貨）| `OrderManagement.md` 一份大檔 | `PlaceOrder.md` / `Payment.md` / `Refund.md` 三份 |
| 「個人偏好」（涵蓋通知、語言兩個設定）| 拆兩份太瑣碎 | `Preferences.md` 一份（同一畫面、同一 ViewModel）|

#### 拆好後的流程

1. **跟 user 確認拆法**：列出建議的多份檔名 + 各份涵蓋範圍，請 user 確認再進 Step 2
2. **每份 doc 各別跑後面流程**：Step 2-6 對每份 doc 獨立執行（各自抽 context、各自落地）
3. **共用內容用 cross-link**：若多份 doc 共享同一個 API spec / 加密參數，在其中一份完整寫，另外幾份用 `[詳見 OtherFeature.md](OtherFeature.md)` 連過去

#### 拆 doc 後的共用基礎設施怎麼放（per-screen 切法的配套）

同一個 `feature/{name}/` 拆成多份 per-screen doc 時，它們會共用 intra-feature 基礎設施（Repository interface / Fake / DTO / Mapper / DI module）。**不另開 umbrella doc**（會變難讀的大雜燴），改用：

- **共用基礎設施的待辦** → 放在「最受它阻擋」的那份 sub-doc（例如 `FakeMemberRepository` 的待辦放最先卡關的 `ResetPassword.md`）
- 其餘 sibling sub-doc → 在自己的待辦表用 cross-link 指過去（標「主要 tracking 在 `XXX.md`」）
- 共用項目要標明「**{feature} feature 共用，非本 doc 專屬**」，避免被誤認為 sub-doc 私有
- 共用基礎設施的「程式碼」本來就在 `feature/{name}/data/` 有家，doc 只是 tracking 待辦 + 跨 doc 可見性 —— 不需要為它另立一份 doc

### Step 2 — 抽 context 內容

從這場對話 / 既有狀態抽：

| 段落 | 抽什麼 |
|---|---|
| `目的` | 抽討論中關於「為什麼做這個」的核心動機，壓縮成 1-2 句 |
| `行為規格 > Requirement` | 抽討論中提到的「系統必須做到 X」「不能 Y」「應該 Z」 |
| `行為規格 > Scenario` | 抽討論中具體的 case：「點 X 之後 Y」「如果 A 就 B」 |
| `技術設計` | 抽 API spec、JSON shape、加密參數、interface 簽名、平台 specifics、DI 註冊（Koin / Hilt / Dagger 視專案）、安全紀律 |
| `實作計畫 + 驗證紀錄` | 抽討論中「分幾片做」「先做什麼後做什麼」「哪個 slice blocker」。每片對應 Requirement / 涵蓋的 Scenario。**對每條 Scenario 分類「邏輯 / UI」**（邏輯 → 待補 unit test；UI → emulator 手測）。第一次落地時驗證欄位多半是「未測」或「⏸️ blocked」。 |
| `待辦` | 抽「待後端確認」「等對齊」「未來補測試」這類跨 session 項。每列寫「移除條件」：什麼事成立就能拿掉暫定做法，要能直接驗（PM 的題預設「問卷該題有 PM 回覆」）。code 的等待標記照抄這一欄 |
| `變更紀錄` | 第一次寫 → 列出當天 ADDED 的所有 Requirement |

### Step 3 — Inline 標記

每條 Requirement 加 HTML 註解：

```markdown
### Requirement: 使用者必須能用生物辨識登入 <!-- ADDED 2026-05-11 -->
```

YYYY-MM-DD 用今天的日期（用 `date +%Y-%m-%d` 或對話 context 的當前日期）。

### Step 4 — **不**寫 footer

**重要**：feature-doc 產出的 doc **不**寫 `Verified` footer。

理由：footer 的語意是「**這份 doc 在 SHA X 跟 code 核對過、對齊**」，不是「**doc 寫好的時間戳**」。剛建立的 doc 還沒實作、更沒核對過，寫 footer 等於誤導。

footer 由 `/verify-feature` 在 **branch 併入 + 解衝突後**核對過、漂移已處理才負責寫入。流程：
```
/feature-doc 產 doc（無 footer）
  ↓
實作（每片 slice：寫 code + 補 unit test + emulator 手測 UI scenario + 填驗證紀錄 table）
  ↓
branch 併入 integration branch + 解衝突
  ↓
/verify-feature 核對（keyword-scoped，抓 conflict resolution 造成的漂移）
  ↓
🤖 修文件漂移 / 🧑 處理 code 被改壞
  ↓
verify-feature 寫 footer（Verified @ sha）
```

### Step 5 — 識別字分類掃描（cross-feature 檢查，落地前必跑）

從 Step 2 抽出的「涵蓋範圍識別字候選」拿來掃描，**避免把共用基礎設施誤寫進本 doc 涵蓋範圍**。同時可順便長 `CLAUDE.md` 的共用基礎設施清單。

#### 5.1 對每個候選識別字統計跨 feature 引用次數

- 對每個識別字 grep `{CODE_ROOT}/feature/*/`，統計出現在幾個不同的 `feature/{x}/` 資料夾
- 也用 Step 0 讀到的「共用基礎設施型別」清單做第一層過濾

#### 5.2 三類分類

| 跨 feature 引用數 | 已在 CLAUDE.md 清單？ | 分類 | 處理 |
|---|---|---|---|
| — | ✅ 已在 | 共用基礎設施（已知） | **自動排除**，不出現在 doc 涵蓋範圍 |
| 0-1 個 feature | ❌ | Feature-specific | 留在本 doc 涵蓋範圍 |
| 2 個 feature | ❌ | 邊界 | 提示 user 決定 |
| ≥3 個 feature | ❌ | **Suspicious 共用基礎設施候選** | 提示 user：移除 + 補進 CLAUDE.md |

#### 5.3 印分類報告給 user

報告格式：

```
識別字分類報告（落地前最後檢查）

✅ Feature-specific（留在涵蓋範圍，X 個）：
  - DeviceKeyAuthenticator, BiometricLoginRepository, ...

⚠️ Suspicious 共用基礎設施（≥3 feature 引用，Y 個）：
  - ApiResult       (17 feature folders) → 建議移除 + 加進 CLAUDE.md
  - TokenManager    (5 feature folders)  → 建議移除 + 加進 CLAUDE.md
  - BaseViewModel   (18 feature folders) → 建議移除 + 加進 CLAUDE.md

🟡 邊界（2 feature 引用，Z 個）：
  - SecretString    (login + member)     → 你決定（feature-specific 還是 shared?）

要：
  (a) 接受 ⚠️ 建議（自動移除 + 寫進 CLAUDE.md 清單）
  (b) 全部留在 doc 涵蓋範圍（不分類）
  (c) 手動挑（一個一個問）
```

#### 5.4 user 決策後動作

- **(a) 接受**：
  - 從涵蓋範圍移除 ⚠️ 項目
  - 把 ⚠️ 項目加進專案 `CLAUDE.md` 的 `## Skill 配置 > 共用基礎設施型別` section（Step 6 一起做）
- **(b) 全部留**：跳過分類、照原樣寫
- **(c) 手動挑**：對每個 ⚠️ / 🟡 項目問「留 / 移除 / 移除並加進 CLAUDE.md」

### Step 6 — 落地（含可能更新 CLAUDE.md）

- 預設路徑：`{DOC_DIR}/{Feature}.md`（從 Step 0 取得 `{DOC_DIR}`，fallback `.claude/docs/`）
- **若 `{DOC_DIR}/` 目錄不存在 → 自動 `mkdir -p`**（不阻擋，直接建立後寫檔）
- 若檔案已存在 → **不覆蓋**，提示 user「檔案已存在，要 Edit 還是覆蓋？」
- 若 Step 5 user 接受「加進 CLAUDE.md」→ 用 Edit 工具更新專案 `CLAUDE.md` 的 `## Skill 配置 > 共用基礎設施型別` 段（若整段不存在則先建立 `## Skill 配置` section）
- **寫 `## 涵蓋範圍` section**：把 Step 5 分類後留下的 **Feature-specific 識別字 + 路徑 + route/API key** 落地進去（共用基礎設施**不**列）→ /verify-feature 的「priority-1 精確反查」才有東西可比對
- 若這是專案**第一份 doc**（落地後 `{DOC_DIR}` 只有這一個 `.md`）→ 提示 user「這是專案第一份 feature doc，之後可跑 /verify-feature 對賬」
- 寫完印路徑給 user，提示「review 完可選擇跑 /verify-feature 對賬」

## Keyword 慣例

| 元素 | 語言 | 範例 |
|---|---|---|
| `## ADDED / MODIFIED / REMOVED Requirements`（用於 delta） | 英文（強制） | `## ADDED Requirements` |
| `### Requirement:` / `#### Scenario:` | 英文（強制） | `### Requirement: 使用者必須能...` |
| Requirement 標題（冒號後） | 中文 | 「使用者必須能用生物辨識登入」 |
| Requirement 描述段 | 中文 | 「當生物辨識登入已啟用，登入畫面...」 |
| `SHALL / MUST / MAY` | 英文 | RFC 2119，語意明確 |
| `GIVEN / WHEN / THEN / AND / BUT` | 英文 | Gherkin 慣例 |
| Scenario 步驟內容 | 中文 | 「使用者點擊生物辨識按鈕」 |
| `<!-- ADDED YYYY-MM-DD -->` 標記 | 英文 keyword + 日期 | `<!-- ADDED 2026-05-11 -->` |

## 輸出原則

- ❌ 不問「為什麼要做這個 feature」（user 是 emergent，不需要 propose-first）
- ❌ 不問 stakeholder / 業務價值（單人開發無 stakeholder）
- ❌ 不寫實作 step-by-step（那是對話內容，不該再寫一次）
- ✅ 直接從對話 context 抽內容、生 7 section、寫檔
- ✅ 若 context 不夠，**留 placeholder**（`TODO: 補 Scenario`）讓 user 後續手動補
- ✅ Requirement / Scenario 不夠精確時，**保守標 TODO 而非亂猜**
- ⛔ **`TODO` Scenario = 未定義的 oracle**：不得標「邏輯」、不得進 `/unit-test`、不得開始該 slice 的骨架；驗證紀錄狀態固定 `⏸️ blocked: Scenario 未定義`，直到 user 補完 GIVEN/WHEN/THEN

## 與其他 skill 的關係

- `/feature-doc` → 產出 doc（這個 skill）
- 實作期間：`/arch-test`（架構規則寫成會紅的測試）
- 落實「邏輯」Scenario：`/unit-test`（commonTest 寫 ViewModel / Repository / UseCase 測試）
- 實作完成：`/verify-feature` 對賬 doc vs code

完整閉環：
```
討論設計 → /feature-doc 落 doc → 實作 → /verify-feature 對賬 → 修漂移 → 更新 footer SHA → commit
```
