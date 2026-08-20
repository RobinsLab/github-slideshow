require "anthropic"
require "json"
require "base64"

# Thin wrapper around the Anthropic Ruby SDK for the two AI-backed
# features this app needs: analyzing a meal (photo or text) and
# writing the end-of-day / weekly report narrative.
class ClaudeClient
  MODEL = ENV.fetch("ANTHROPIC_MODEL", "claude-opus-5")

  def initialize
    @client = Anthropic::Client.new
  end

  # image_bytes/media_type present for a photo-based record, otherwise text is used.
  def analyze_meal(meal_type:, text: nil, image_bytes: nil, media_type: nil)
    system_prompt = <<~SYS
      あなたは管理栄養士です。ユーザーから提供された食事の写真またはテキストの説明を分析し、
      必ず次のキーだけを持つ有効なJSONオブジェクト1つだけを出力してください。
      説明文やマークダウンのコードフェンスは一切付けないでください。

      {
        "items": [{"name": "品目名", "calories": 概算カロリー(数値)}],
        "total_calories": 合計カロリー(数値),
        "nutrition": {
          "protein_g": タンパク質グラム数(数値),
          "fat_g": 脂質グラム数(数値),
          "carbs_g": 炭水化物グラム数(数値),
          "balance_comment": "この食事の栄養バランスについての短いコメント"
        },
        "suggestion": "この食事についての具体的な改善提案(1〜2文)"
      }

      数値は推定でよいが、必ず数値型で返すこと。今回の食事区分は「#{meal_type}」です。
    SYS

    content = []
    if image_bytes
      content << {
        type: "image",
        source: { type: "base64", media_type: media_type, data: Base64.strict_encode64(image_bytes) }
      }
      content << { type: "text", text: text.to_s.empty? ? "この食事の写真を分析してください。" : text }
    else
      content << { type: "text", text: text.to_s }
    end

    response = @client.messages.create(
      model: MODEL,
      max_tokens: 2000,
      system: system_prompt,
      output_config: { effort: "medium" },
      messages: [{ role: "user", content: content }]
    )

    parse_json_response(response)
  end

  # today: { meals: [...], weights: [...] }
  # week: array of { date:, total_calories:, weights: [...] } for the past 7 days (oldest first)
  def generate_report(date:, today:, week:)
    system_prompt = <<~SYS
      あなたは辛口だが的確な健康・ダイエットコーチです。以下の1日分の食事・体重データと
      過去1週間分の推移データを分析し、必ず次のキーだけを持つ有効なJSONオブジェクト1つだけを
      出力してください。説明文やマークダウンのコードフェンスは一切付けないでください。

      {
        "daily_meal_summary": "その日の食事内容と栄養バランスの要約(2〜3文)",
        "daily_weight_summary": "その日の体重(朝/夜)の要約(1〜2文)。記録が無ければその旨を書く",
        "daily_harsh_review": "その日の食事・体重に対する辛口だが具体的で建設的な総合評価(3〜5文)",
        "weekly_trend": "過去1週間のカロリー・体重・栄養バランスの推移の説明(3〜5文)",
        "weekly_harsh_review": "過去1週間全体に対する辛口だが具体的で建設的な総合評価(3〜5文)",
        "improvement_suggestions": ["改善提案1", "改善提案2", "改善提案3"]
      }
    SYS

    payload = { date: date, today: today, past_7_days: week }

    response = @client.messages.create(
      model: MODEL,
      max_tokens: 4000,
      system: system_prompt,
      output_config: { effort: "high" },
      messages: [{ role: "user", content: JSON.generate(payload) }]
    )

    parse_json_response(response)
  end

  private

  def parse_json_response(response)
    text_block = response.content.find { |block| block.type == :text }
    raise "Claude returned no text content" unless text_block

    JSON.parse(strip_code_fence(text_block.text))
  end

  def strip_code_fence(text)
    text.strip.sub(/\A```(?:json)?\s*/i, "").sub(/```\s*\z/, "")
  end
end
