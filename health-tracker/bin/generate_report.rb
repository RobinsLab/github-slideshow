#!/usr/bin/env ruby
# Generates (and saves) the daily summary report. Intended to be run once a
# day, e.g. via cron, at the end of the day:
#   0 23 * * * cd /path/to/health-tracker && bundle exec ruby bin/generate_report.rb
require "date"
require_relative "../lib/meal_repository"
require_relative "../lib/weight_repository"
require_relative "../lib/report_generator"

date = ARGV[0] ? Date.parse(ARGV[0]) : Date.today

generator = ReportGenerator.new(meal_repo: MealRepository.new, weight_repo: WeightRepository.new)
result = generator.generate(date)

puts "Report saved to data/reports/#{result[:date]}.md"
puts
puts File.read(File.join(__dir__, "..", "data", "reports", "#{result[:date]}.md"))
