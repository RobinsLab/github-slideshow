require_relative "store"
require_relative "claude_client"

class MealRepository
  MEAL_TYPES = %w[breakfast lunch dinner].freeze

  def initialize(store: DateFileStore.new(File.join(__dir__, "..", "data", "meals")), claude: ClaudeClient.new)
    @store = store
    @claude = claude
  end

  def for_date(date)
    @store.all_for_date(date)
  end

  def history(start_date, end_date)
    @store.for_range(start_date, end_date)
  end

  # Analyzes the meal via Claude, then stamps the record with a snapshot of
  # the day's cumulative calories/nutrition *including this meal*, and persists it.
  def record(date:, meal_type:, text: nil, image_bytes: nil, media_type: nil, input_type:)
    analysis = @claude.analyze_meal(meal_type: meal_type, text: text, image_bytes: image_bytes, media_type: media_type)

    existing = for_date(date)
    day_calories_before = existing.sum { |m| m[:calories].to_f }
    day_nutrition_before = sum_nutrition(existing)

    record = {
      meal_type: meal_type,
      recorded_at: Time.now.iso8601,
      input_type: input_type,
      input_summary: text.to_s.empty? ? "(photo)" : text,
      items: analysis["items"],
      calories: analysis["total_calories"],
      nutrition: analysis["nutrition"],
      suggestion: analysis["suggestion"],
      day_totals_at_record: {
        calories: day_calories_before + analysis["total_calories"].to_f,
        protein_g: day_nutrition_before[:protein_g] + analysis["nutrition"]["protein_g"].to_f,
        fat_g: day_nutrition_before[:fat_g] + analysis["nutrition"]["fat_g"].to_f,
        carbs_g: day_nutrition_before[:carbs_g] + analysis["nutrition"]["carbs_g"].to_f
      }
    }

    @store.add(date, record)
  end

  def daily_totals(date)
    records = for_date(date)
    {
      calories: records.sum { |m| m[:calories].to_f },
      nutrition: sum_nutrition(records)
    }
  end

  private

  def sum_nutrition(records)
    {
      protein_g: records.sum { |m| m.dig(:nutrition, :protein_g).to_f },
      fat_g: records.sum { |m| m.dig(:nutrition, :fat_g).to_f },
      carbs_g: records.sum { |m| m.dig(:nutrition, :carbs_g).to_f }
    }
  end
end
