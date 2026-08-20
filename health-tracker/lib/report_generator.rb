require "date"
require "fileutils"
require_relative "claude_client"

class ReportGenerator
  REPORTS_DIR = File.join(__dir__, "..", "data", "reports")

  def initialize(meal_repo:, weight_repo:, claude: ClaudeClient.new)
    @meal_repo = meal_repo
    @weight_repo = weight_repo
    @claude = claude
    FileUtils.mkdir_p(REPORTS_DIR)
  end

  def generate(date)
    date = Date.parse(date.to_s)
    week_start = date - 6

    today_payload = {
      meals: @meal_repo.for_date(date),
      weights: @weight_repo.for_date(date),
      totals: @meal_repo.daily_totals(date)
    }

    week_payload = (week_start..date).map do |d|
      {
        date: d.to_s,
        totals: @meal_repo.daily_totals(d),
        weights: @weight_repo.for_date(d)
      }
    end

    review = @claude.generate_report(date: date.to_s, today: today_payload, week: week_payload)

    result = {
      date: date.to_s,
      today: today_payload,
      week: week_payload,
      review: review
    }

    save_markdown(result)
    result
  end

  def load(date)
    path = markdown_path(date)
    File.exist?(path) ? File.read(path) : nil
  end

  private

  def save_markdown(result)
    File.write(markdown_path(result[:date]), to_markdown(result))
  end

  def markdown_path(date)
    File.join(REPORTS_DIR, "#{date}.md")
  end

  def to_markdown(result)
    review = result[:review]
    suggestions = (review["improvement_suggestions"] || []).map { |s| "- #{s}" }.join("\n")

    <<~MD
      # #{result[:date]} サマリレポート

      ## 食事サマリ
      #{review["daily_meal_summary"]}

      ## 体重サマリ
      #{review["daily_weight_summary"]}

      ## 本日の辛口総合評価
      #{review["daily_harsh_review"]}

      ## 過去1週間の推移
      #{review["weekly_trend"]}

      ## 過去1週間の辛口総合評価
      #{review["weekly_harsh_review"]}

      ## 改善提案
      #{suggestions}
    MD
  end
end
