# AI香港醫療配對系統

這是一個使用AI技術的智能醫療配對系統，能夠根據病人的症狀、年齡、語言偏好和地理位置，推薦最合適的專科醫生。

## 功能特點

- 🤖 **AI智能分析**：支援Ollama本地LLM或OpenRouter雲端AI分析病人症狀
- 👨‍⚕️ **精準配對**：根據專科、語言、地區等條件匹配醫生
- 🌐 **多語言支持**：支援廣東話、英語、普通話、法語
- 📱 **響應式設計**：適配桌面和移動設備
- 🔒 **本地部署**：數據安全，隱私保護

## 系統要求

- Python 3.8+
- AI服務 (二選一):
  - Ollama (本地LLM服務)
  - OpenRouter API密鑰 (雲端AI服務)
- 現代網頁瀏覽器

## 安裝步驟

1. **安裝Python依賴**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置AI服務**
   
   **選項A: 使用Ollama (本地)**
   ```bash
   # 安裝Ollama (macOS)
   brew install ollama
   
   # 下載模型
   ollama pull llama3.1:8b
   
   # 啟動Ollama服務
   ollama serve
   ```
   
   **選項B: 使用OpenRouter (雲端)**
   ```bash
   # 設置環境變數
   export AI_PROVIDER=openrouter
   export OPENROUTER_API_KEY=your_api_key_here
   export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```
   
   或創建 `.env` 文件：
   ```
   AI_PROVIDER=openrouter
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```

3. **啟動網站**
   ```bash
   python app.py
   ```

4. **訪問網站**
   打開瀏覽器訪問：http://localhost:8081
   
   檢查系統狀態：http://localhost:8081/health
   查看AI配置：http://localhost:8081/ai-config

## 使用方法

1. 填寫病人資料：
   - 年齡
   - 症狀描述
   - 偏好語言
   - 所在地區

2. 點擊「尋找合適醫生」按鈕

3. 系統將使用AI分析症狀並推薦最合適的醫生

## 醫生資料

系統包含香港地區的專科醫生資料，包括：
- 醫生姓名和專科
- 支援語言
- 聯絡方式
- 診所地址
- 專業資格

## 技術架構

- **前端**：HTML5, CSS3, JavaScript
- **後端**：Flask (Python)
- **AI引擎**：Ollama + Llama3.2
- **數據處理**：Pandas
- **UI框架**：響應式設計 + Font Awesome圖標

## 注意事項

- 請確保Ollama服務正在運行
- 首次使用可能需要下載AI模型
- 本系統僅供參考，不能替代專業醫療建議

## 故障排除

如果遇到問題：

1. **Ollama連接失敗**
   - 確認Ollama服務正在運行：`ollama serve`
   - 檢查端口11434是否可用

2. **醫生資料載入失敗**
   - 確認assets目錄下有醫生資料CSV文件

3. **網站無法訪問**
   - 檢查Flask服務是否正常啟動
   - 確認端口5000未被佔用
