require "json"
require "fileutils"
require "securerandom"
require "date"

# Simple append-only JSON-file storage: one file per calendar date,
# holding an array of records. Good enough for a single-user tracker
# and keeps the app free of native DB dependencies.
class DateFileStore
  def initialize(dir)
    @dir = dir
    FileUtils.mkdir_p(@dir)
  end

  def all_for_date(date)
    path = file_for(date)
    return [] unless File.exist?(path)

    JSON.parse(File.read(path), symbolize_names: true)
  end

  def add(date, record)
    records = all_for_date(date)
    record = record.merge(id: SecureRandom.uuid, date: date.to_s)
    records << record
    File.write(file_for(date), JSON.pretty_generate(records))
    record
  end

  def for_range(start_date, end_date)
    (start_date..end_date).each_with_object({}) do |date, memo|
      records = all_for_date(date)
      memo[date.to_s] = records unless records.empty?
    end
  end

  private

  def file_for(date)
    File.join(@dir, "#{date}.json")
  end
end
