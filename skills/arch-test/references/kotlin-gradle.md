# Kotlin／Gradle（含 KMP）的架構測試做法

2026-11-02 在 TravelRecordList（KMP、單一 `composeApp` 模組、Gradle、AGP 9）實際驗證過。其他 Kotlin 專案照這份起步，跟專案實際情況不同的地方以專案為準，驗證過再補進來。

## 認原始碼集合（第 1 步）

- Android 專案：`src/main`、`src/test`（電腦上跑）、`src/androidTest`（手機上跑）。
- KMP：`src/commonMain`、`androidMain`、`iosMain`…，測試是 `commonTest`、`androidHostTest`（AGP 9 的 KMP library 外掛要在 `androidLibrary { withHostTest { } }` 開啟才有）等。
- 層看 `package` 宣告，不看資料夾。

## 編譯擋不擋得住（第 1 步第 3 點）

- KMP 的 commonMain 寫 `android.*`、`java.*`：只有 metadata 編譯會擋，Android 目標的編譯與 `testAndroidHostTest` 照樣通過，所以要寫成測試。
- Compose、Room、Ktor 是 commonMain 的依賴，domain 也 import 得到；單一模組時，任何套件都 import 得到彼此。

## 測試放哪、怎麼讀原始碼（第 2 步）

- 放 `androidHostTest`（KMP）或 `src/test`（Android）：跑在電腦的 JVM 上，工作目錄是模組資料夾，`File("src")` 讀得到原始碼。`androidTest` 跑在手機上，讀不到。
- 用 JUnit 加 `kotlin.test` 斷言就夠，不加依賴：讀 `.kt` 檔，去掉註解與字串後抓 `package`、`import`、完整名稱的引用。
- 要看型別、繼承、註解這類結構時才考慮 Konsist；先查它的文件與跟專案 Kotlin、KSP 版本的相容性（TravelRecordList 沒有用，相容性沒驗證）。

## 建置設定（第 2 步，改之前給使用者看）

在 `build.gradle.kts` 的測試任務：

```kotlin
tasks.withType<Test>().configureEach {
    // 沒用到的 import 不改變編譯結果，不列為輸入會被判成 UP-TO-DATE 而不重跑
    inputs.dir("src").withPathSensitivity(PathSensitivity.RELATIVE)
    // 測試失敗時在終端機印出完整訊息（哪條規則、哪個檔案），不用另外開測試報告
    testLogging {
        events("failed")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        showStackTraces = false
    }
}
```

- 預設的 `testLogging` 只印「N tests completed, M failed」，失敗訊息只在 `build/reports/tests/`。
- `testLogging` 的設定在 `-q` 下不印，宣告的指令不要加 `-q`。
- 不印呼叫堆疊：架構測試的堆疊沒用，會把 hook 轉給 Claude 的最後 60 行擠掉。

## 證明會紅（第 3 步）

- 每次跑加 `--rerun --no-build-cache`，否則可能 `UP-TO-DATE` 或 `FROM-CACHE`，測試沒有真的跑。
- 結果檔：`<模組>/build/test-results/<測試任務>/TEST-*.xml`，看檔案時間是不是這次、`tests="N"` 的總和。
- 只跑一個類別：`--tests "*ArchitectureRulesTest"`。

## 宣告指令（第 4 步）

- 宣告完整測試，例：`./gradlew :composeApp:testAndroidHostTest`。
- 用 `--tests` 只跑架構測試時，Gradle 會清掉結果資料夾裡其他測試的結果檔；跟完整測試輪流跑時，每次換都要重跑。TravelRecordList 實測：只跑架構測試每次 22～28 秒；改宣告完整測試後，沒改程式時 2 秒、有改時約 7～12 秒。
- hook 在 Windows 用 Git 附的 bash 跑，`./gradlew` 可以直接用。
