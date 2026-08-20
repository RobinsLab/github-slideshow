require_relative "store"

class WeightRepository
  TIMES_OF_DAY = %w[morning night].freeze

  def initialize(store: DateFileStore.new(File.join(__dir__, "..", "data", "weights")))
    @store = store
  end

  def for_date(date)
    @store.all_for_date(date)
  end

  def history(start_date, end_date)
    @store.for_range(start_date, end_date)
  end

  def record(date:, time_of_day:, weight_kg:, note: nil)
    @store.add(date, {
                 time_of_day: time_of_day,
                 recorded_at: Time.now.iso8601,
                 weight_kg: weight_kg.to_f,
                 note: note
               })
  end
end
